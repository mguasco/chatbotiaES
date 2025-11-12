# services/chatbot_service.py - VERSIÓN FINAL CORREGIDA (indentación uniforme, 4 espacios)
# Incluye: normalización genérica + búsqueda híbrida + anclaje de follow-ups + sinónimos EasySoft
import logging
import string
import time
import re
import unicodedata
from typing import Dict, Any, Optional, Tuple

from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from utils.embeddings import EmbeddingUtils
from config import Config


# ---------------------------------------------------------------------
# Utilidad: Guardar preguntas no respondidas
# ---------------------------------------------------------------------
def guardar_pregunta_no_respondida(pregunta: str, archivo: str = "preguntas_no_respondidas.log") -> None:
    try:
        with open(archivo, "a", encoding="utf-8") as f:
            f.write(pregunta.strip() + "\n")
    except Exception as e:
        logging.error(f"No se pudo guardar la pregunta no respondida: {e}")


# ---------------------------------------------------------------------
# Normalización genérica y neutral (sin listas)
# --------------------------------1-------------------------------------
def normalize_generic(text: str) -> str:
    """
    Limpieza neutral para embeddings/keyword:
    - recorta espacios
    - elimina signos ¿?¡! al borde
    - pasa a minúsculas
    - quita tildes (NFKD)
    - reemplaza puntuación por espacios
    - colapsa espacios
    No elimina palabras (no usa stopwords) ni cambia el sentido.
    """
    if not text:
        return text
    t = text.strip()
    t = t.strip("¿?¡!")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    t = re.sub(r"[^\w\sáéíóúñü]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ---------------------------------------------------------------------
# Clase principal del chatbot
# ---------------------------------------------------------------------
class ChatbotService:
    def _strip_unnecessary_disclaimer(self, text: str) -> str:
        """
        Si la respuesta comienza con un aviso tipo 'No encontré información específica...'
        pero luego incluye contenido útil (listas, pasos, 'Para ...', etc.), elimina ese aviso inicial.
        No toca el resto de la respuesta.
        """
        if not text:
            return text
        t = text.lstrip()
        # patrones de disclaimer comunes
        disclaimers = [
            "no encontré información específica en la documentación disponible",
            "no encontré información adicional específica en la documentación disponible",
            "la información que encontré no parece estar relacionada",
        ]
        lower = t.lower()
        starts_with_disclaimer = any(lower.startswith(d) for d in disclaimers)
        if not starts_with_disclaimer:
            return text

        # ¿hay contenido útil enseguida? bullets, numeración, o 'para ...'
        useful = bool(re.search(r"(?m)^\s*[-•]\s+", t)) or \
                 bool(re.search(r"(?m)^\s*\d+\.\s+", t)) or \
                 "para " in lower or "pasos" in lower or "según la documentación" in lower

        if useful:
            # quitar solo el primer párrafo hasta doble salto de línea o final de línea
            t = re.sub(r"^.*?\n\s*\n", "", t, count=1, flags=re.IGNORECASE|re.DOTALL)
            # si no había doble salto, intentar hasta el primer punto
            t = re.sub(r"^.*?\.\s*", "", t, count=1, flags=re.IGNORECASE)
            return t.lstrip()
        return text

    def __init__(self, weaviate_service: WeaviateService) -> None:
        self.weaviate_service = weaviate_service
        self.openai_service = OpenAIService()
        self.embedding_utils = EmbeddingUtils(self.openai_service)
        self.chat_histories: Dict[str, list] = {}

        self.escalation_keywords = {
            "humano", "persona", "agente", "supervisor", "hablar con alguien",
            "no entiendo", "no me sirve", "quiero hablar", "contacto",
            "reclamo", "queja", "problema urgente", "error crítico",
            "atención al cliente", "soporte técnico", "ayuda personal", "ayuda",
            "no resuelve", "mal servicio", "insatisfecho", "frustrado", "consultor"
        }

        self.failed_attempts: Dict[str, int] = {}

        self.predefined_responses = {
            "hola": "¡Hola! Soy la IA especializada en EasySoft. ¿En qué puedo ayudarte hoy?",
            "adios": "¡Hasta pronto! Si necesitas más ayuda, no dudes en preguntar.",
            "gracias": "De nada. Estoy aquí para ayudarte.",
            "buenos dias": "¡Buenos días! ¿Cómo puedo asistirte hoy?",
            "buenas tardes": "¡Buenas tardes! ¿En qué puedo ayudarte?",
            "buenas noches": "¡Buenas noches! ¿Hay algo en lo que pueda ayudarte?",
            "chau": "¡Hasta luego!",
            "después seguimos": "¡Seguro! Estoy aquí para ayudarte?",
            "hasta mañana": "Hasta mañana. Estaré aquí para ayudarte."
        }

    # ------------------------
    # Helpers básicos

    def _should_respond_based_on_context(self, question: str, context: str, results_count: int) -> bool:
        """
        Decide si responder según similitud entre (pregunta normalizada) y contexto.
        Tolerante: si no hay normalizador/umbral dinámico, usa los valores base.
        """
        try:
            q = question
            try:
                if hasattr(self, "_normalize_for_semantics"):
                    # Se usa la pregunta completa (q) para obtener un vector más rico, 
                    # especialmente si incluye el anclaje de contexto.
                    pass 
            except Exception as e:
                logging.warning(f"⚠️ _should_respond_based_on_context normalize error: {e}")
                q = question

            # 🛑 INICIO DE CORRECCIÓN (Similitud con anclaje)
            # El vector para el cálculo de similitud debe generarse con la consulta anclada (q)
            # para validar la cercanía al contexto de los follow-ups.
            # Se omite el stripping del contexto para el vector de la pregunta.
            vector_q_input = q # La consulta completa (con anclaje si aplica)
            
            # Genera el vector con la pregunta ANCLADA (vector_q_input).
            question_vector = self.embedding_utils.get_embeddings(vector_q_input)
            # 🛑 FIN DE CORRECCIÓN
            context_vector = self.embedding_utils.get_embeddings((context or "")[:1000])
            if not question_vector or not context_vector:
                return False

            similarity = self.embedding_utils.cosine_similarity(question_vector, context_vector)

            try:
                if hasattr(self, "_effective_similarity_threshold"):
                    thr = self._effective_similarity_threshold(question, base=getattr(Config, "SIMILARITY_THRESHOLD", 0.80))
                else:
                    thr = float(getattr(Config, "SIMILARITY_THRESHOLD", 0.80))
            except Exception as e:
                logging.warning(f"⚠️ _should_respond_based_on_context threshold error: {e}")
                thr = float(getattr(Config, "SIMILARITY_THRESHOLD", 0.80))

            logging.info(f"📈 Similitud: {similarity:.3f} (umbral: {thr})")
            return similarity >= thr

        except Exception as e:
            logging.warning(f"⚠️ Error calculando similitud: {e}")
            return False

    def _normalize_for_semantics(self, text: str) -> str:
        """
        Normaliza para embeddings:
        1. Expande sinónimos (si es llamado antes de la búsqueda vectorial).
        2. Desambigua verbos en 1ª persona (cargo, creo, defino) a su infinitivo 
           en cualquier parte de la frase para mejorar la similitud semántica.
        """
        t = (text or "").strip()
        try:
            # 1. Expansión de sinónimos (se realiza primero para ampliar la cadena)
            if hasattr(self, "_expand_question_with_synonyms"):
                t2 = self._expand_question_with_synonyms(t)
            else:
                t2 = None
            if t2:
                t = t2
        except Exception as e:
            logging.warning(f"⚠️ Error en expansión de sinónimos: {e}")
            
        # 2. Desambiguación de verbos en 1ª persona e Imperativos/Impersonales
        
        # 👇 AGREGAR ESTA LÍNEA DE CORRECCIÓN PARA EXPRESIONES DE MÚLTIPLES PALABRAS 👇
        # Esto corrige "como se da de alta" -> "como se dar de alta"
        t = re.sub(r'\bda\s+de\s+alta\b', 'dar de alta', t, flags=re.IGNORECASE)
        
        # Mapeo de conjugaciones (1ª Persona : Infinitivo)
        conjugation_fixes = {
            # Se ha reordenado para que 'cierro' no aparezca duplicado, pero la funcionalidad es la misma
            "creo": "crear", "cargo": "cargar", "cierro": "cerrar",
            "emito": "emitir", "consulto": "consultar", "defino": "definir",
            "doy": "dar", "agrego": "agregar", "genero": "generar",
            "muestro": "mostrar", "elimino": "eliminar", "borro": "borrar",
            "listo": "listar", "saco": "sacar", "veo": "ver", "busco": "buscar",
            "finalizo": "finalizar", "termino": "terminar", "registro": "registrar", "asigno": "asignar",
            "incorporo": "incorporar", "selecciono": "seleccionar",
        }
        
        # Aplicar los reemplazos a nivel de palabra completa (\b{conj}\b)
        # Esto reemplaza 'cargo' por 'cargar', 'defino' por 'definir', etc., donde sea que aparezcan.
        for conj, infinitive in conjugation_fixes.items():
            pattern = rf'\b{conj}\b' 
            t = re.sub(pattern, infinitive, t, flags=re.IGNORECASE)

        # 3. Mantenemos la corrección original para el caso crítico "cómo creo" 
        # (se aplica sobre el resultado del paso 2 por seguridad)
        t = re.sub(r'^\s*c[oó]mo\s+crear\b', 'cómo crear', t, flags=re.IGNORECASE)
            
        return t

    def _effective_similarity_threshold(self, user_question: str, base: float = None) -> float:
        """Si la normalización cambió el texto, alivio mínimo del umbral (-0.02).
           Si se usó anclaje de contexto (follow-up), se alivio aún más (-0.01 extra, total -0.03 max).
        """
        if base is None:
            base = float(getattr(Config, "SIMILARITY_THRESHOLD", 0.80))
        q = (user_question or "").strip()
        
        # 1. Alivio por normalización/sinónimos (-0.02)
        norm = normalize_generic(q)
        sem_q = self._normalize_for_semantics(q)
        if norm.lower() != normalize_generic(sem_q).lower():
             # Si la expansión de sinónimos o corrección de conjugaciones tuvo efecto, alivia el umbral
            base = max(0.0, base - 0.02)

        # 2. Alivio adicional si se usó anclaje de contexto (-0.01 extra, total -0.03 max)
        # Esto es para manejar la ambigüedad de vectores cortos.
        if "|| contexto_previo:" in q.lower():
             # Si es un follow-up anclado, la ambigüedad es mayor, aliviamos más
            return max(0.0, base - 0.01) # Total max reduction is 0.03 (0.80 -> 0.77)
            
        return base
    # ------------------------
    def _normalize(self, text: str) -> str:
        return text.lower().strip().translate(str.maketrans('', '', string.punctuation))


    def _is_short_followup(self, text: str) -> bool:
        t = re.sub(r"\s*\(en el mismo tema previo\).*?$", "", text.strip().lower())
        greetings = {'hola', 'gracias', 'chau', 'adios', 'buenos dias', 'buenas tardes', 'buenas noches'}
        if t in greetings:
            return False
        # Considerar follow-up si es breve (<=6 tokens) o usa anáforas frecuentes
        if len(t.split()) <= 6:
            return True
        if re.search(r"\b(el|la|los|las|del|de|sobre|ese|esa|eso|estos|estas|aquello|aquella|anterior|siguiente|puedo|eliminar|modificar|crear)\b", t):
            return True
        return False

    def _build_followup_query(self, user_question: str, session_id: str) -> str:
        last_user = next((m['content'] for m in reversed(self.chat_histories.get(session_id, [])) if m['role'] == 'user'), '')
        last_assistant = next((m['content'] for m in reversed(self.chat_histories.get(session_id, [])) if m['role'] == 'assistant'), '')
        base = (last_user + ' ' + last_assistant).strip()[:600]
        uq = user_question.strip()
        if base:
            return uq  # no agregar sufijos ruidosos
        return uq

    # ------------------------
    # Helpers de anclaje para follow-ups
    # ------------------------
    def _extract_keywords_generic(self, text: str, k: int = 8) -> list:
        """
        Extrae hasta k palabras clave del texto sin conocimiento de dominio.
        Heurística simple:
          - normaliza (minúsculas, sin tildes/punt.)
          - elimina stopwords comunes en español
          - descarta tokens muy cortos y verbos infinitivos (-ar/-er/-ir) como heurística
          - ordena por frecuencia y primer aparición (estable) y devuelve top-k
        """
        if not text:
            return []
        t = normalize_generic(text)
        tokens = t.split()
        stop = {"a","ante","bajo","cabe","con","contra","de","desde","durante","en","entre","hacia","hasta","mediante",
                "para","por","segun","según","sin","so","sobre","tras","y","o","u","e","pero","que","como","cual","cuales",
                "el","la","los","las","un","una","unos","unas","al","del","lo","le","les","se","su","sus","tu","tus","mi","mis",
                "es","son","ser","fue","fueron","era","eran","soy","eres","somos","estan","están","esta","está","estaba","estaban",
                "hay","haber","tengo","tiene","tienen","tenia","tenía","tenian","tenían","puede","puedo","pueden","poder",
                "si","sí","no","mas","más","tambien","también","ya","aun","aún","solo","sólo","muy","menos",
                "uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez"}
        freq = {}
        first_pos = {}
        cleaned = []
        for i, w in enumerate(tokens):
            if len(w) < 3:
                continue
            if w in stop:
                continue
            if len(w) > 4 and (w.endswith("ar") or w.endswith("er") or w.endswith("ir")):
                continue
            if w not in freq:
                freq[w] = 0
                first_pos[w] = i  # guardamos la primera aparición
                cleaned.append(w)
            freq[w] += 1
        # ordenar por (-frecuencia, primera_aparición)
        cleaned.sort(key=lambda x: (-freq[x], first_pos[x]))
        return cleaned[:k]

    def _resolve_ordinal_reference(self, user_question: str, session_id: str) -> str:
        q = (user_question or "").lower()
        ordinal_map = {
            "primero": 0, "1ero": 0, "1º": 0, "1ro": 0, "1°": 0, "primer": 0, "primera": 0,
            "segundo": 1, "2do": 1, "2º": 1, "2°": 1, "segunda": 1,
            "tercero": 2, "3ero": 2, "3º": 2, "3°": 2, "tercera": 2,
            "cuarto": 3, "4to": 3, "4º": 3, "4°": 3, "cuarta": 3,
            "quinto": 4, "5to": 4, "5º": 4, "5°": 4, "quinta": 4
        }
        idx = None
        for k, i in ordinal_map.items():
            if re.search(rf"\b{k}\b", q):
                idx = i
                break
        if idx is None:
            return ""
        # Último mensaje informativo (ignorando derivaciones)
        last_info = ""
        for m in reversed(self.chat_histories.get(session_id, [])):
            if m.get("role") == "assistant":
                t = (m.get("content") or "").lower()
                if ("te voy a conectar con un especialista" in t) or ("conectando con un consultor" in t) or ("derivando a un especialista" in t):
                    continue
                last_info = m.get("content") or ""
                break
        if not last_info:
            for m in reversed(self.chat_histories.get(session_id, [])):
                if m.get("role") == "user":
                    txt = (m.get("content") or "").lower().strip()
                    if self._is_acknowledgement(txt):
                        continue
                    last_info = m.get("content") or ""
                    break
        if not last_info:
            return ""
        # Ítems de lista
        lines = [ln.strip() for ln in last_info.splitlines() if ln.strip()]
        items = []
        for ln in lines:
            if re.match(r"^[-•]\s*", ln) or re.match(r"^\d+\.\s+", ln):
                items.append(re.sub(r"^([-•]|\d+\.)\s*", "", ln))
        if not items:
            paragraphs = [p.strip() for p in last_info.split("\n\n") if p.strip()]
            items = [p for p in paragraphs if len(p.split()) > 3]
        if not items or idx >= len(items):
            return ""
        chosen = items[idx]
        chosen = re.split(r"[.;]\s+", chosen)[0]
        kw = self._extract_keywords_generic(chosen, k=8)
        context = " ".join(kw) if kw else chosen
        return f"continuar con más detalle || contexto_previo: {context}"

    def _extract_focus_from_user_followup(self, text: str) -> list:
        if not text:
            return []
        t = normalize_generic(text)
        tokens = t.split()
        stop = {"a","ante","bajo","cabe","con","contra","de","del","desde","durante","en","entre","hacia","hasta","mediante",
                "para","por","segun","según","sin","so","sobre","tras","y","o","u","e","pero","que","como","cual","cuales",
                "el","la","los","las","un","una","unos","unas","al","lo","le","les","se","su","sus","tu","tus","mi","mis",
                "si","sí","no","mas","más","tambien","también","ya","solo","muy","ninguno","ninguna","ningunas","ningunos",
                "este","esta","estos","estas","ese","esa","esos","esas","esto","eso","aquello","aquel","aquella","aquellos","aquellas"}
        focus = [w for w in tokens if len(w) > 2 and w not in stop]
        focus = [w for w in focus if not (len(w) > 4 and (w.endswith('ar') or w.endswith('er') or w.endswith('ir')))]
        return focus[:4]

    def _extract_topic_from_text(self, text: str) -> str:
        """
        Extrae un tema del último turno del asistente, priorizando sustantivos del dominio EasySoft.
        """
        if not text:
            return ""
        t = text.lower()
        keys = {
            "atributo", "empresa", "cuenta", "asiento", "cierre", "comprobante",
            "cliente", "proveedor", "centro de costos", "item", "depósito", "deposito",
            "balance", "informe", "reporte"
        }
        for k in sorted(keys, key=len, reverse=True):
            if k in t:
                return k
        tokens = [w for w in re.findall(r"[a-záéíóúñü]+", t)]
        candidates = [w for w in tokens if len(w) > 4]
        return candidates[0] if candidates else ""

    def _detect_action_from_followup(self, uq: str) -> str:
        """
        Dado un follow-up corto (“como lo creo?”, “y si lo borro?”),
        estima la acción canónica: crear / eliminar / emitir / consultar…
        """
        q = uq.lower()
        if re.search(r"\b(crear|creo|definir|dar alta|alta|agregar|cargar)\b", q) or re.search(r"c[oó]mo\s+lo\s+cre", q):
            return "crear"
        if re.search(r"\b(eliminar|elimino|borrar|borro|quitar|remover|modificar|modifico)\b", q):
            return "eliminar" # Usar eliminar como acción genérica de alteración/cambio
        if re.search(r"\b(emitir|generar|listar|reporte|informe)\b", q):
            return "emitir"
        if re.search(r"\b(consultar|ver|mostrar|buscar)\b", q):
            return "consultar"
        return "crear"



    def _anchor_followup_query(self, user_question: str, session_id: str) -> str:
        """
        Ancla follow-ups cortos al contexto previo de forma GENÉRICA (sin listas de dominio):
        - Ignora mensajes de derivación
        - Toma keywords del último mensaje informativo del asistente; si no hay, del último usuario no-ack
        - Concatena esos keywords como 'contexto_previo' a la consulta
        """
        uq = user_question.strip()
        uq_clean = re.sub(r"\s*\(en el mismo tema previo\).*?$", "", uq.lower())
        if not self._is_short_followup(uq_clean):
            return uq

        # Resolver referencia ordinal si aplica
        ordq = self._resolve_ordinal_reference(user_question, session_id)
        if ordq:
            return self._expand_question_with_synonyms(ordq)

        # Último mensaje informativo del asistente (ignorando derivaciones)
        last_info = ""
        for m in reversed(self.chat_histories.get(session_id, [])):
            if m.get("role") == "assistant":
                text = (m.get("content") or "").lower()
                if ("te voy a conectar con un especialista" in text) or ("conectando con un consultor" in text) or ("derivando a un especialista" in text):
                    continue
                last_info = m.get("content") or ""
                break

        # Fallback al último usuario no-ack
        if not last_info:
            for m in reversed(self.chat_histories.get(session_id, [])):
                if m.get("role") == "user":
                    txt = (m.get("content") or "").lower().strip()
                    if self._is_acknowledgement(txt):
                        continue
                    last_info = m.get("content") or ""
                    break

        keywords = self._extract_keywords_generic(last_info, k=8)
        focus = self._extract_focus_from_user_followup(user_question)
        merged = []
        # Agregar "modificar" si es el foco (puedo modificarla?)
        if "modificarla" in normalize_generic(user_question):
            merged.append("modificar")
            merged.append("modificarla")
        # Agregar "eliminar" si es el foco (puedo eliminarlas?)
        if "eliminarlas" in normalize_generic(user_question):
            merged.append("eliminar")
            merged.append("eliminarlas")
            
        for w in (focus + keywords):
            if w not in merged:
                merged.append(w)
        if not merged:
            return uq
        context = " ".join(merged)
        anchored = f"{uq} || contexto_previo: {context}"
        anchored = self._expand_question_with_synonyms(anchored)
        return anchored

    def _should_escalate_to_human(self, user_question: str, context_results: Dict[str, Any], session_id: str) -> Tuple[bool, Optional[str]]:
        question_lower = user_question.lower()

        for keyword in self.escalation_keywords:
            if keyword in question_lower:
                logging.info(f"🔺 Escalación por palabra clave: '{keyword}' en '{user_question}'")
                return True, "user_explicit_request"

        has_no_context = not context_results or not context_results.get("context")
        has_low_similarity = context_results.get("low_similarity", False)

        if has_no_context or has_low_similarity:
            self.failed_attempts[session_id] = self.failed_attempts.get(session_id, 0) + 1
            if Config.ENABLE_HUMAN_ESCALATION and self.failed_attempts[session_id] >= Config.ESCALATION_THRESHOLD:
                reason = "no_context" if has_no_context else "low_similarity"
                logging.info(f"🔺 Escalación por '{reason}': {self.failed_attempts[session_id]} intento(s)")
                return True, reason
        else:
            if session_id in self.failed_attempts:
                self.failed_attempts[session_id] = 0

        sensitive_topics = ["urgente", "necesito ayuda urgente", "frustrado", "mesa de ayuda", "soporte", "alguien", "contacto", "ayuda", "persona", "agente", "queja", "reclamo", "mal servicio", "consultor"]
        if any(topic in question_lower for topic in sensitive_topics):
            logging.info(f"🔺 Escalación por tema sensible en: '{user_question}'")
            return True, "sensitive_topic"

        return False, None

    def _create_escalation_response(self, user_question: str, session_id: str, reason: str) -> Dict[str, Any]:
        reason_messages = {
            "user_explicit_request": "Por supuesto, te conectaré con un consultor que podrá ayudarte de manera más personalizada.",
            "multiple_failed_attempts": "Veo que no estoy pudiendo ayudarte como esperabas. Te voy a conectar con un especialista.",
            "sensitive_topic": "Para este tipo de consultas es mejor que hables directamente con uno de nuestros especialistas.",
            "no_context": "No encontré información específica sobre tu consulta en la documentación disponible. Te voy a conectar con un especialista que podrá ayudarte mejor.",
            "low_similarity": "La información que encontré no parece estar relacionada con tu consulta. Te voy a conectar con un especialista que podrá ayudarte mejor."
        }
        escalation_response = reason_messages.get(reason, "Te voy a conectar con un consultor que podrá ayudarte mejor.")

        response_data = {
            'response': escalation_response,
            'escalate_to_human': True,
            'escalation_reason': reason,
            'user_question': user_question,
            'session_context': self._get_session_summary(session_id),
            'full_conversation': (
                f"<div class='chat-message user-message'><span class='message-label'></span> {user_question}</div>\n"
                f"<div class='chat-message assistant-message escalation'><span class='message-label'></span> {escalation_response}</div>\n"
            )
        }

        self.chat_histories[session_id].append({"role": "user", "content": user_question})
        self.chat_histories[session_id].append({"role": "assistant", "content": escalation_response})
        logging.info(f"🚩 ESCALACIÓN: Razón='{reason}', Sesión='{session_id}', Pregunta='{user_question[:50]}...'")
        return response_data

    def _get_session_summary(self, session_id: str) -> str:
        if session_id not in self.chat_histories:
            return "Nueva conversación"
        history = self.chat_histories[session_id]
        if not history:
            return "Nueva conversación"

        recent_messages = history[-6:] if len(history) > 6 else history
        summary_parts = []
        for i in range(0, len(recent_messages), 2):
            if i + 1 < len(recent_messages):
                user_msg = recent_messages[i].get('content', '')[:100]
                ai_msg = recent_messages[i + 1].get('content', '')[:100]
                summary_parts.append(f"Usuario: {user_msg}... | IA: {ai_msg}...")
        return " | ".join(summary_parts[-2:])

    def _is_acknowledgement(self, text: str) -> bool:
        """Detecta confirmaciones cortas que suelen significar 'sí, avanzá'."""
        t = (text or "").strip().lower()
        acks = {"si", "sí", "ok", "dale", "de una", "claro", "por favor", "please", "hace", "hazlo", "siga", "segui", "sigue", "vale", "perfecto", "genial", "va"}
        return t in acks or t.startswith(("si,", "sí,", "ok,", "dale,", "claro,", "por favor"))

    def _extract_named_report(self, text: str) -> str:
        """Extrae el nombre del informe si aparece: 'diario general', 'mayores', 'centros de costos'..."""
        t = (text or "").lower()
        if "diario general" in t:
            return "diario general"
        if "mayores" in t:
            return "mayores"
        if "centros de costos" in t or "centro de costos" in t:
            return "centros de costos"
        return ""

    def _expand_acknowledgement_to_intent(self, session_id: str) -> str:
        """
        Convierte un 'sí/ok/dale' en una consulta explícita basada en el último contenido útil.
        Arma una intención genérica y le agrega keywords del contexto previo.
        """
        # Último mensaje informativo del asistente (ignorando derivaciones)
        last_info = ""
        for m in reversed(self.chat_histories.get(session_id, [])):
            if m.get("role") == "assistant":
                text = (m.get("content") or "").lower()
                if ("te voy a conectar con un especialista" in text) or ("conectando con un consultor" in text) or ("derivando a un especialista" in text):
                    continue
                last_info = m.get("content") or ""
                break
        # Fallback al último usuario no-ack
        if not last_info:
            for m in reversed(self.chat_histories.get(session_id, [])):
                if m.get("role") == "user":
                    txt = (m.get("content") or "").lower().strip()
                    if self._is_acknowledgement(txt):
                        continue
                    last_info = m.get("content") or ""
                    break
        keywords = self._extract_keywords_generic(last_info, k=8)
        context = " ".join(keywords)
        # Intención genérica (sin hardcode de dominio)
        query = "continuar con más detalle"
        if context:
            query = f"{query} || contexto_previo: {context}"
        # Refuerzo con sinónimos genéricos de usuario (tu mapa)
        query = self._expand_question_with_synonyms(query)
        return query

    # ------------------------
    # BÚSQUEDA (GENÉRICA + HÍBRIDA)
    # ------------------------
    def _hybrid_search_wrapper(self, query: str, bias: str = "", limit: int = 5, alpha: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Intenta usar un método híbrido nativo del WeaviateService si existe.
        Fallback: usa la búsqueda vectorial existente (search_similar_documents) con query_text enriquecido.
        Devuelve un dict con al menos: success(bool), context(str), results_count(int), search_method(str), optional score(float).
        """
        try:
            if hasattr(self.weaviate_service, "search_hybrid"):
                # Si el query ya tiene el anclaje (|| contexto_previo: ...), no se pasa el bias por separado
                if "|| contexto_previo:" in query.lower():
                    resp = self.weaviate_service.search_hybrid(
                        query=query,
                        max_results=limit,
                        alpha=alpha,
                        bias="", # Se omite bias para evitar duplicación
                    )
                else:
                     resp = self.weaviate_service.search_hybrid(
                        query=query,
                        max_results=limit,
                        alpha=alpha,
                        bias=bias
                    )
                
                if resp and resp.get("success") and resp.get("context"):
                    resp.setdefault("search_method", "hybrid")
                    return resp

            # Fallback a búsqueda vectorial tradicional
            question_vector = self.embedding_utils.get_embeddings(query)
            if not question_vector:
                return None

            # Si el query ya está enriquecido con contexto_previo, usarlo como está para el query_text de Weaviate.
            query_text = query if not bias or "|| contexto_previo:" in query.lower() else f"{query} || contexto_previo: {bias}"
            
            resp = self.weaviate_service.search_similar_documents(
                question_vector,
                query_text=query_text,
                max_results=limit
            )
            if resp and resp.get("success") and resp.get("context"):
                resp.setdefault("search_method", "vector_fallback")
                return resp

            return None
        except Exception as e:
            logging.warning(f"⚠️ Error en _hybrid_search_wrapper: {e}")
            return None

    def _pick_better_context(self, a: Optional[Dict[str, Any]], b: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Elige el mejor contexto disponible comparando heurísticamente score -> results_count -> len(context)."""
        def score_of(x: Optional[Dict[str, Any]]) -> Tuple[float, int, int]:
            if not x:
                return -1.0, -1, -1
            score = x.get("score", 0.0)
            count = x.get("results_count", 0)
            clen = len((x.get("context") or "").strip())
            return score, count, clen

        if not a and not b:
            return None
        if a and not b:
            return a
        if b and not a:
            return b

        sa = score_of(a)
        sb = score_of(b)
        return a if sa > sb else b

    # ------------------------
    # Núcleo de procesamiento
    # ------------------------
    def process_question(self, user_question: str, session_id: str) -> Dict[str, Any]:
        """Procesamiento con lógica de fallback restrictiva (no inventar)."""
        try:
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = []

            logging.info(f"❓ Pregunta recibida: {user_question}")
            original_user_question = user_question
            cleaned_question = self._normalize(user_question)

            # Si el usuario responde con un acuse corto (sí/ok/dale), expandir a intención explícita
            if self._is_acknowledgement(original_user_question):
                user_question = self._expand_acknowledgement_to_intent(session_id)
                logging.info(f"🔧 Ack detectado. Reformulado a intención: {user_question}")

            # 1) Respuestas predefinidas
            if cleaned_question in self.predefined_responses:
                return self._handle_predefined_response(user_question, cleaned_question, session_id)

            # 1.1) Reformulación para follow-ups cortos
            if self.chat_histories.get(session_id) and self._is_short_followup(user_question):
                rewritten = self._build_followup_query(user_question, session_id)
                if rewritten and rewritten != user_question:
                    user_question = rewritten
                    logging.info(f"🔁 Follow-up detectado. Reformulada: {user_question}")

            # 1.2) Escalación previa (por pedido explícito/tema sensible)
            should_escalate, escalation_reason = self._should_escalate_to_human(user_question, {}, session_id)
            if should_escalate and escalation_reason in ["user_explicit_request", "sensitive_topic"]:
                return self._create_escalation_response(user_question, session_id, escalation_reason)

            # 2) BÚSQUEDA: híbrida (original vs anclada+normalizada)
            bias = ""
            if session_id and self.chat_histories.get(session_id):
                last_assistant = next((m["content"] for m in reversed(self.chat_histories[session_id]) if m["role"] == "assistant"), "")
                bias = (last_assistant or "")[:600]

            # 2.1) Preparación de consultas
            anchored_q = self._anchor_followup_query(original_user_question, session_id)
            # sem_q: Es la query completamente enriquecida (sinónimos + contexto_previo: si aplica)
            sem_q = self._normalize_for_semantics(anchored_q) 
            
            # Limpia ruido (solo para fines de logging y para la generación final)
            sem_q_clean = re.sub(r"\s*\|\|\s*contexto_previo:.*$", "", sem_q, flags=re.IGNORECASE)
            sem_q_clean = re.sub(r"\s+", " ", sem_q_clean).strip()
            if len(sem_q_clean) > 220:
                sem_q_clean = sem_q_clean[:220]
            
            # Usamos la pregunta original (o follow-up reescrito si aplica)
            query_for_search = user_question 
            if sem_q_clean != user_question:
                 # Si la normalización generó una mejor query (por sinónimos), usar esa.
                query_for_search = sem_q_clean 

            norm_q = normalize_generic(query_for_search)
            logging.info(f"🔧 SEM normalize (Final Clean Query): '{anchored_q}' -> '{query_for_search}'")
            
            # Intentos de búsqueda híbrida/vectorial
            # Intento 1: Query original
            res_orig = self._hybrid_search_wrapper(user_question, bias=bias, limit=5, alpha=0.5)
            # Intento 2 (MODIFICADO): Usar la query completamente enriquecida (sinónimos + contexto anclado)
            # Esto corrige la búsqueda para follow-ups cortos.
            res_anchored = self._hybrid_search_wrapper(sem_q, bias=bias, limit=5, alpha=0.5) 
            context_results = self._pick_better_context(res_orig, res_anchored)
            
            
            # CORRECCIÓN CLAVE: Si la primera búsqueda híbrida no da un buen resultado, 
            # se intenta una búsqueda con reintentos usando la consulta semánticamente rica (sem_q).
            if not self._has_good_context(context_results or {}):
                logging.info("🔎 No hay buen contexto inicial. Intentando búsqueda con múltiples reintentos...")
                context_results = self._search_with_multiple_attempts(sem_q, session_id)


            if not self._has_good_context(context_results):
                context_results = context_results or {}
                context_results["low_similarity"] = True
                should_escalate, escalation_reason = self._should_escalate_to_human(user_question, context_results, session_id)
                if should_escalate:
                    return self._create_escalation_response(user_question, session_id, escalation_reason)
                return self._create_no_info_response(user_question, session_id)

            context = context_results.get("context", "")
            results_count = context_results.get("results_count", 0)
            search_method = context_results.get("search_method", "unknown")
            logging.info(f"🔎 Contexto encontrado con '{search_method}': {results_count} resultados")

            # 3) Decisión estricta por similitud (mantener umbral)
            # MODIFICADO: Usar la query semánticamente enriquecida (sem_q) para generar el vector de pregunta.
            # La limpieza de ruido estructural para el vector se hace dentro de _should_respond_based_on_context.
            should_respond = self._should_respond_based_on_context(sem_q, context, results_count) 
            if not should_respond:
                context_results["low_similarity"] = True
                should_escalate, escalation_reason = self._should_escalate_to_human(user_question, context_results, session_id)
                if should_escalate:
                    return self._create_escalation_response(user_question, session_id, escalation_reason)
                return self._create_no_info_response(user_question, session_id)

            # 4) Generar respuesta (prompt restrictivo)
            history = self.chat_histories[session_id][-Config.MAX_HISTORY_MESSAGES * 2:]
            system_prompt = self._create_adaptive_prompt(context, results_count, search_method)
            messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_question}, {"role": "assistant", "content": f"(consulta normalizada: {norm_q})"}]
            
            logging.warning("🧠 PROMPT FINAL >>>\nSYSTEM:\n%s\nUSER:\n%s\nCONTEXT:\n%s", system_prompt, user_question, context)


            chatbot_response = self.openai_service.generate_response(messages)
            chatbot_response = self._strip_unnecessary_disclaimer(chatbot_response)
            if not chatbot_response:
                return self._create_error_response("Error al generar respuesta", user_question, session_id)

            # 5) Validación de respuesta
            if self._is_generic_response(chatbot_response):
                logging.warning("🟨 Respuesta genérica detectada, reintentando con prompt más restrictivo…")
                aggressive_response = self._retry_with_aggressive_prompt(user_question, context, history, results_count, search_method)
                if aggressive_response and not self._is_generic_response(aggressive_response):
                    chatbot_response = aggressive_response
                elif self._is_generic_response(aggressive_response or ""):
                    return self._create_no_info_response(user_question, session_id)

            # 6) Actualizar historial
            self.chat_histories[session_id].append({"role": "user", "content": user_question})
            self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})
            if len(self.chat_histories[session_id]) > Config.MAX_HISTORY_MESSAGES * 2:
                self.chat_histories[session_id] = self.chat_histories[session_id][-Config.MAX_HISTORY_MESSAGES * 2:]

            if session_id in self.failed_attempts:
                self.failed_attempts[session_id] = 0

            return self._create_success_response(user_question, chatbot_response)

        except Exception as e:
            logging.error(f"❌ Error en process_question: {e}")
            return self._create_error_response(f"Error del servidor: {str(e)}", user_question, session_id)

    # ------------------------------------------------------------------
    # Compatibilidad: carryover y búsquedas previas
    # ------------------------------------------------------------------
    def _try_topic_carryover(self, user_question: str, session_id: str) -> Optional[Dict[str, Any]]:
        last_assistant = next((m["content"] for m in reversed(self.chat_histories.get(session_id, [])) if m["role"] == "assistant"), "")
        if not last_assistant:
            return None
        carry = f"{user_question} (tema relacionado a: {last_assistant[:300]})"
        return self._try_search(carry, "carryover", session_id)

    def _search_with_multiple_attempts(self, user_question: str, session_id: str) -> Optional[Dict[str, Any]]:
        # user_question aquí ya DEBERÍA estar normalizada semánticamente (expandida y verbos corregidos)
        result = self._try_search(user_question, "original", session_id)
        if self._has_good_context(result):
            return result

        if "easysoft" not in user_question.lower():
            enhanced_question = f"{user_question} en EasySoft sistema contable?"
            result = self._try_search(enhanced_question, "with_easysoft", session_id)
            if self._has_good_context(result):
                return result

        key_terms = self._extract_main_keywords(user_question)
        if key_terms != user_question:
            result = self._try_search(f"{key_terms} EasySoft", "keywords", session_id)
            if self._has_good_context(result):
                return result

        return None

    def _try_search(self, question: str, method_name: str, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            bias = ""
            # Normalizar antes de embeddings/búsqueda
            # Nota: Si se llama desde _search_with_multiple_attempts, la pregunta ya está normalizada semánticamente
            question_norm = self._normalize_for_semantics(question)
            if session_id and self.chat_histories.get(session_id):
                last_assistant = next((m["content"] for m in reversed(self.chat_histories[session_id]) if m["role"] == "assistant"), "")
                bias = (last_assistant or "")[:600]

            question_vector = self.embedding_utils.get_embeddings(question_norm)
            if not question_vector:
                return None

            context_results = self.weaviate_service.search_similar_documents(
                question_vector,
                # Si question_norm ya está enriquecido con contexto_previo, no pasamos bias por separado.
                query_text=(question_norm + " || contexto_previo: " + bias) if bias and "|| contexto_previo:" not in question_norm.lower() else question_norm,
                max_results=5
            )
            if context_results.get("success") and context_results.get("context"):
                context_results["search_method"] = method_name
                return context_results

            return None
        except Exception as e:
            logging.warning(f"⚠️ Error en búsqueda '{method_name}': {e}")
            return None

    # ------------------------------------------------------------------
    # Utilidades de extracción/expansión (lista de sinónimos se conserva)
    # ------------------------------------------------------------------
    def _extract_main_keywords(self, question: str) -> str:
        stop_words = {"como", "que", "es", "el", "la", "los", "las", "de", "en", "para", "con", "por", "una", "un", "se", "y", "o"}
        words = normalize_generic(question).split()
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        return " ".join(keywords[:4]) if keywords else question

    def _expand_question_with_synonyms(self, question: str) -> str:
        """Expande la pregunta con sinónimos específicos del dominio EasySoft (tu mapa original)."""
        synonyms_map = {
            "cargar": "cargo crear definir dar alta agregar nueva",
            "cargo": "crear definir dar alta agregar nueva",
            "crear": "creo cargar definir dar alta agregar nueva",
            "creo": "crear cargar definir dar alta agregar nueva",
            "cuenta": "cuenta contable plan cuentas",
            "empresa": "empresa compañía organización datos empresa",
            "asiento": "asiento contable registro movimiento",
            "cerrar": "cierro cerrar cierre finalizar ejercicio",
            "cierro": "cierro cerrar cierre finalizar ejercicio",
            "emitir": "emito emitir generar listar reporte informe",
            "emito": "emito emitir generar listar reporte informe",
            "consultar": "consulto consultar ver mostrar buscar",
            "consulto": "consulto consultar ver mostrar buscar",
            "definir":"definir cargar crear dar alta agregar nueva",
            "defino":"defino definir cargar crear dar alta agregar nueva",
            "dar de alta":"dar de alta cargar crear definir agregar nueva",
            "doy de alta":"doy de alta cargar crear definir agregar nueva",
            "agregar": "agrego cargar crear definir dar alta nueva",
            "agrego": "agrego agregar cargar crear definir dar alta nueva",
            "cierre":"cierro cerrar finalizar",
            "generar":"genero emitir listar informe reporte",
            "genero":"genero generar emitir listar informe reporte",
            "mostrar":"muestra mostrar consultar ver buscar",
            "muestro":"muestra mostrar consultar ver buscar",
            "consultar":"consulto ver mostrar buscar",
            "eliminar":"elimino eliminar borrar borro",
            "elimino":"elimino eliminar borrar borro",
            "borro":"elimino eliminar borrar borro",
            "borrar":"elimino eliminar borrar borro",
            "registrar":"registrar registro",
            "registro":"registro registrar",
            "asignar":"asignar asigno",
            "asigno":"asigno asignar",
            "incorporo": "incorporo incorporar",
            "incorporar": "incorporar incorporo",
            "seleccionar": "seleccionar selecciono",
            "selecciono": "selecciono seleccionar",
            "modificar": "modificar modifico cambiar actualiza",
            "modifico": "modifico modificar cambiar actualiza",
            "actualizar": "actualizar actualiza modificar",
            "actualiza": "actualiza actualizar modificar"
        }
        q = question.lower()
        expanded_parts = [q]
        for k, v in synonyms_map.items():
            # Usar regex para coincidencia de palabra completa si la palabra clave es un verbo o sustantivo de dominio.
            # No es necesario para el caso de 'contexto_previo' (que es la clave que más preocupa).
            # Para las demás, la búsqueda 'in q' es suficiente dada la agresividad de la normalización.
            if k in q:
                expanded_parts.append(v)
        return " ".join(expanded_parts)

    # ------------------------------------------------------------------
    # Similitud / prompts / respuestas
    # ------------------------------------------------------------------
    def _has_good_context(self, result: Optional[Dict[str, Any]]) -> bool:
        if not result or not result.get("success"):
            return False
        context = result.get("context", "")
        results_count = result.get("results_count", 0)
        return len((context or "").strip()) >= 50 and results_count >= 1


    def _create_adaptive_prompt(self, context: str, results_count: int, search_method: str) -> str:
        instruction = (
        "Responde ÚNICAMENTE con información presente en el CONTEXTO. "
        "Si el CONTEXTO no cubre la pregunta, responde exactamente: "
        "'No encontré información específica disponible para esa pregunta.' "
        "y ofrece reformular. No agregues información de otros temas, incluso si parecen relacionados"
        "Si no encontras información, decile que no encontraste información y ofrecele que escriba explicitamente la palabra 'ayuda' para ser derivado a un consultor."
        )

        return f"""Eres un asistente experto en EasySoft.

REGLAS ANTIALUCINACIONES:
- No inventes información.
- No completes con conocimiento general ni con temas relacionados.
- Responde solo si el dato aparece en el CONTEXTO.
- Si no está, di literalmente que no se encontró información específica.

{instruction}

CONTEXTO (de Weaviate):
{context}

METADATOS:
- Resultados: {results_count}
- Método: {search_method}
"""
    def _is_generic_response(self, response: str) -> bool:
        generic_phrases = [
            "no tengo la información",
            "no puedo responder",
            "no hay información",
            "basándome en la información disponible",
            "no encuentro información"
        ]
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in generic_phrases) and len(response) < 200

    def _retry_with_aggressive_prompt(self, question: str, context: str, history: list, results_count: int, search_method: str) -> Optional[str]:
        try:
            aggressive_prompt = f"""Eres un asistente experto en EasySoft.

REGLAS IMPORTANTES (ANTIALUCINACIONES):
- Responde SOLO con el CONTEXTO provisto.
- Si el CONTEXTO no incluye la respuesta, di exactamente: "No encontré información específica disponible para esa pregunta." y sugiere reformular.
- No inventes ni extrapoles.
- Sé breve y directo.
- No menciones la palabra "documentación" ni frases como "según la documentación", "en la documentación disponible", "de acuerdo a la documentación", etc.
- No introduzcas preámbulos; comienza directamente con el contenido útil.

CONTEXTO (de Weaviate):
{context}

METADATOS DE BÚSQUEDA:
- Resultados encontrados: {results_count}
- Método de búsqueda: {search_method}
"""
            messages = [{"role": "system", "content": aggressive_prompt}] + history + [{"role": "user", "content": question}]
            return self.openai_service.generate_response(messages)
        except Exception as e:
            logging.error(f"Error en reintento restrictivo: {e}")
            return None

    # ------------------------------------------------------------------
    # Respuestas y utilidades finales
    # ------------------------------------------------------------------
    def _handle_predefined_response(self, user_question: str, cleaned_question: str, session_id: str) -> Dict[str, Any]:
        chatbot_response = self.predefined_responses[cleaned_question]
        self.chat_histories[session_id].append({"role": "user", "content": user_question})
        self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})
        return self._create_success_response(user_question, chatbot_response)

    def _create_success_response(self, user_question: str, chatbot_response: str) -> Dict[str, Any]:
        full_display = f"<div class='chat-message user-message'><span class='message-label'></span> {user_question}</div>\n"
        full_display += f"<div class='chat-message assistant-message'><span class='message-label'></span> {chatbot_response}</div>\n"
        return {'response': chatbot_response, 'full_conversation': full_display}

    def _create_no_info_response(self, user_question: str, session_id: str) -> Dict[str, Any]:
        chatbot_response = (
            "No encontré información específica para responder esa pregunta. "
            "¿Podrías reformular la consulta o indicar el módulo/pantalla exacta para buscar mejor?"
        )
        self.chat_histories[session_id].append({"role": "user", "content": user_question})
        self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})
        guardar_pregunta_no_respondida(user_question)
        return self._create_success_response(user_question, chatbot_response)

    def _create_error_response(self, error_message: str, user_question: str, session_id: str) -> Dict[str, Any]:
        return {
            'error': error_message,
            'full_conversation': (
                f"<div class='chat-message user-message'><span class='message-label'></span> {user_question}</div>\n"
                f"<div class='chat-message assistant-message error'><span class='message-label'>Error:</span> {error_message}</div>\n"
            )
        }

    # ------------------------------------------------------------------
    # Mantenimiento / salud del servicio
    # ------------------------------------------------------------------
    def clear_chat_history(self, session_id: str) -> bool:
        try:
            if session_id in self.chat_histories:
                del self.chat_histories[session_id]
            return True
        except Exception as e:
            logging.error(f"Error al limpiar historial de {session_id}: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        health_status: Dict[str, Any] = {
            "status": "ok",
            "timestamp": time.time(),
            "services": {}
        }
        health_status["services"]["weaviate"] = self.weaviate_service.get_health_status()
        health_status["services"]["openai"] = self.openai_service.get_health_status()

        all_services_ok = all(service == "connected" for service in health_status["services"].values())
        if not all_services_ok:
            health_status["status"] = "degraded"
        return health_status

    def cleanup(self) -> None:
        try:
            self.weaviate_service.close()
            logging.info("Servicios de chatbot cerrados correctamente.")
        except Exception as e:
            logging.error(f"Error al cerrar servicios: {e}")
