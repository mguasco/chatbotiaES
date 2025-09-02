
import logging
import traceback
from typing import Optional, List, Dict, Any
from openai import OpenAI
from config import Config


def _as_str(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    out_chunks: List[str] = []
    try:
        if isinstance(content, list):
            for p in content:
                if isinstance(p, dict):
                    if "text" in p and isinstance(p["text"], str):
                        out_chunks.append(p["text"])
                    elif "text" in p and isinstance(p["text"], dict):
                        val = p["text"].get("value") or p["text"].get("data") or ""
                        if val:
                            out_chunks.append(str(val))
                else:
                    if hasattr(p, "text"):
                        t = getattr(p.text, "value", None) or getattr(p, "text", None)
                        if t:
                            out_chunks.append(str(t))
            return " ".join([c for c in out_chunks if c]).strip()
        if isinstance(content, dict):
            if "text" in content and isinstance(content["text"], str):
                return content["text"].strip()
            if "text" in content and isinstance(content["text"], dict):
                val = content["text"].get("value") or content["text"].get("data") or ""
                return str(val).strip()
    except Exception:
        return ""
    return ""


def _normalize_messages(msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    norm: List[Dict[str, Any]] = []
    for m in msgs:
        role = m.get("role", "user")
        content = m.get("content", "")
        norm.append({"role": role, "content": _as_str(content)})
    return norm


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.system_prompt = (
            "Eres un asistente útil que responde preguntas solo con base en la "
            "información de los documentos de EasySoft. Si la información no está en el "
            "contexto, respondé: 'No tengo la información para responder a esa pregunta "
            "basándome en los documentos de EasySoft disponibles.'"
        )
        self.safe_fallback = (
            "No tengo la información para responder a esa pregunta basándome en los "
            "documentos de EasySoft disponibles."
        )
        # Permite ajustar tokens máximos de salida desde config (opcional)
        self.max_out_tokens = getattr(Config, "OPENAI_MAX_OUTPUT_TOKENS", 1500)

    def generate_response(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        try:
            msgs = [{"role": "system", "content": self.system_prompt}] + list(messages)
            msgs = _normalize_messages(msgs)

            # Chat Completions
            try:
                resp = self.client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=msgs,
                    max_completion_tokens=self.max_out_tokens,
                )
                finish = getattr(resp.choices[0], "finish_reason", None) if getattr(resp, "choices", None) else None
                usage = getattr(resp, "usage", None)
                text = ""
                if getattr(resp, "choices", None):
                    choice = resp.choices[0]
                    text = _as_str(getattr(getattr(choice, "message", None), "content", None))
                logging.info("[OpenAIService] chat.completions finish_reason=%s usage=%s", finish, usage)
                if text:
                    return text
            except Exception as e1:
                logging.warning("[OpenAIService] chat.completions fallback: %s", e1)

            # Responses
            resp2 = self.client.responses.create(
                model="gpt-5-mini",
                input=msgs,
                max_output_tokens=self.max_out_tokens,
            )
            # Algunos SDKs exponen finish_reason/usage en un lugar distinto
            try:
                fr = getattr(resp2, "output", None)
                usage2 = getattr(resp2, "usage", None)
                logging.info("[OpenAIService] responses usage=%s", usage2)
            except Exception:
                pass

            text2 = (getattr(resp2, "output_text", "") or "").strip()
            if not text2:
                out = getattr(resp2, "output", None)
                if isinstance(out, list) and out:
                    content2 = getattr(out[0], "content", None)
                    text2 = _as_str(content2)
                if not text2 and hasattr(resp2, "choices"):
                    choices = getattr(resp2, "choices", [])
                    if choices:
                        content3 = getattr(getattr(choices[0], "message", None), "content", None)
                        text2 = _as_str(content3)
            if text2:
                return text2

            logging.error("[OpenAIService] Respuesta vacía tras ambos intentos")
            return self.safe_fallback

        except Exception as e:
            logging.error(f"Error al llamar a OpenAI: {e}")
            logging.error(traceback.format_exc())
            return None

    def get_health_status(self) -> str:
        try:
            self.client.models.list()
            return "connected"
        except Exception as e:
            logging.error(f"Error en health check de OpenAI: {e}")
            return "error"
