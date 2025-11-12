#!/usr/bin/env python3
# debug_chatbot.py - Herramientas para analizar inconsistencias (VERSIÓN CORREGIDA)
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from services.chatbot_service import ChatbotService
from services.weaviate_service import WeaviateService
from utils.embeddings import EmbeddingUtils
from services.openai_service import OpenAIService

class ChatbotDebugger:
    """Herramientas para debuggear y analizar problemas de consistencia"""
    
    def __init__(self):
        self.weaviate_service = WeaviateService()
        self.chatbot_service = ChatbotService(self.weaviate_service)
        self.openai_service = OpenAIService()
        self.embedding_utils = EmbeddingUtils(self.openai_service)
        
        # Configurar logging para debug
        self._setup_debug_logging()
    
    def _setup_debug_logging(self):
        """Configura logging específico para debug"""
        debug_log = f"debug_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        debug_handler = logging.FileHandler(debug_log, encoding='utf-8')
        debug_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        debug_handler.setFormatter(formatter)
        
        logger = logging.getLogger()
        logger.addHandler(debug_handler)
        logger.setLevel(logging.DEBUG)
        
        print(f"Debug log: {debug_log}")
    
    def analyze_question_consistency(self, question: str, num_tests: int = 5) -> Dict[str, Any]:
        """Analiza la consistencia de una pregunta en múltiples ejecuciones"""
        print(f"\nANALIZANDO CONSISTENCIA DE: '{question}'")
        print("=" * 80)
        
        results = []
        session_prefix = f"debug_consistency_{datetime.now().strftime('%H%M%S')}"
        
        for i in range(num_tests):
            session_id = f"{session_prefix}_{i}"
            
            print(f"\nTest {i+1}/{num_tests}")
            print("-" * 40)
            
            try:
                # Procesar la pregunta
                result = self.chatbot_service.process_question(question, session_id)
                
                # Analizar resultado
                analysis = {
                    "test_number": i + 1,
                    "session_id": session_id,
                    "success": "error" not in result,
                    "has_response": bool(result.get("response")),
                    "response_length": len(result.get("response", "")),
                    "response_preview": result.get("response", "")[:150] + "..." if result.get("response") else None,
                    "error": result.get("error"),
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(analysis)
                
                # Mostrar resultado del test
                if analysis["success"] and analysis["has_response"]:
                    print(f"ÉXITO - Respuesta generada ({analysis['response_length']} chars)")
                    print(f"   Preview: {analysis['response_preview']}")
                else:
                    print(f"FALLÓ - {analysis.get('error', 'Sin respuesta')}")
                
            except Exception as e:
                print(f"ERROR CRÍTICO: {e}")
                results.append({
                    "test_number": i + 1,
                    "session_id": session_id,
                    "success": False,
                    "critical_error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Análisis de consistencia
        consistency_analysis = self._analyze_consistency_results(results)
        
        # Guardar reporte detallado
        report_file = self._save_consistency_report(question, results, consistency_analysis)
        
        print(f"\nRESUMEN DE CONSISTENCIA:")
        print("=" * 50)
        print(f"Éxitos: {consistency_analysis['success_count']}/{num_tests} ({consistency_analysis['success_rate']:.1f}%)")
        print(f"Consistencia: {consistency_analysis['consistency_score']:.1f}%")
        print(f"Problema principal: {consistency_analysis['main_issue']}")
        print(f"Reporte completo: {report_file}")
        
        return {
            "question": question,
            "total_tests": num_tests,
            "results": results,
            "consistency_analysis": consistency_analysis,
            "report_file": report_file
        }
    
    def _analyze_consistency_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza los resultados para identificar patrones de inconsistencia"""
        total_tests = len(results)
        successful_tests = [r for r in results if r.get("success", False) and r.get("has_response", False)]
        
        success_count = len(successful_tests)
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        # Identificar el problema principal
        main_issue = "Desconocido"
        if success_rate == 0:
            main_issue = "No se encontró información relevante en ningún test"
        elif success_rate < 30:
            main_issue = "Búsqueda muy inconsistente - revisar vectorización de documentos"
        elif success_rate < 60:
            main_issue = "Inconsistencia moderada - optimizar estrategias de búsqueda"
        elif success_rate < 90:
            main_issue = "Inconsistencia menor - ajustar umbrales de similitud"
        else:
            main_issue = "Funcionamiento consistente"
        
        # Calcular score de consistencia
        if successful_tests:
            response_lengths = [r["response_length"] for r in successful_tests]
            length_variance = max(response_lengths) - min(response_lengths)
            length_consistency = max(0, 100 - (length_variance / 10))
        else:
            length_consistency = 0
        
        consistency_score = (success_rate + length_consistency) / 2
        
        return {
            "success_count": success_count,
            "total_tests": total_tests,
            "success_rate": success_rate,
            "consistency_score": consistency_score,
            "main_issue": main_issue,
            "response_length_variance": max([r["response_length"] for r in successful_tests]) - min([r["response_length"] for r in successful_tests]) if successful_tests else 0
        }
    
    def _save_consistency_report(self, question: str, results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Guarda un reporte detallado de consistencia"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"consistency_report_{timestamp}.json"
        
        report_data = {
            "metadata": {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(results),
                "analysis_version": "1.0"
            },
            "summary": analysis,
            "detailed_results": results,
            "recommendations": self._generate_recommendations(analysis)
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return report_file
        except Exception as e:
            print(f"Error guardando reporte: {e}")
            return "Error guardando reporte"
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        success_rate = analysis.get("success_rate", 0)
        
        if success_rate < 30:
            recommendations.extend([
                "CRÍTICO: Muy baja tasa de éxito",
                " Revisar si los documentos están correctamente vectorizados",
                " Verificar que la pregunta tenga información en la base de datos",
                " Considerar re-entrenar o actualizar los embeddings",
                " Revisar la configuración de Weaviate"
            ])
        elif success_rate < 60:
            recommendations.extend([
                "MODERADO: Inconsistencia significativa",
                " Ajustar umbrales de similitud (reducir SIMILARITY_THRESHOLD)",
                " Optimizar estrategias de búsqueda híbrida",
                " Mejorar expansión de sinónimos para esta temática"
            ])
        elif success_rate < 90:
            recommendations.extend([
                "BUENO: Inconsistencia menor",
                " Afinar umbrales de distancia en Weaviate",
                " Optimizar procesamiento de contexto"
            ])
        else:
            recommendations.append("EXCELENTE: Funcionamiento consistente")
        
        variance = analysis.get("response_length_variance", 0)
        if variance > 500:
            recommendations.append(" Alta varianza en longitud de respuestas - revisar prompts")
        
        return recommendations

    def simple_search_analysis(self, question: str) -> Dict[str, Any]:
        """Análisis simplificado del sistema de búsqueda para una pregunta"""
        print(f"\nANÁLISIS SIMPLIFICADO DE BÚSQUEDA: '{question}'")
        print("=" * 80)
        
        try:
            # 1. Análisis de embeddings
            question_vector = self.embedding_utils.get_embeddings(question)
            if not question_vector:
                return {"error": "No se pudieron obtener embeddings"}
            
            print(f"Embeddings generados: {len(question_vector)} dimensiones")
            
            # 2. Búsqueda directa
            context_results = self.weaviate_service.search_similar_documents(
                question_vector,
                query_text=question,
                max_results=10
            )
            
            print(f"\nRESULTADOS DE BÚSQUEDA:")
            print(f"   Éxito: {context_results.get('success', False)}")
            print(f"   Resultados: {context_results.get('results_count', 0)}")
            print(f"   Contexto: {len(context_results.get('context', ''))} caracteres")
            
            # 3. Búsqueda permisiva si la normal falla
            if context_results.get('results_count', 0) < 2:
                print("\nIntentando búsqueda permisiva...")
                permissive_results = self.weaviate_service.search_similar_documents_permissive(
                    question_vector,
                    query_text=question,
                    max_results=15
                )
                
                print(f"   Búsqueda permisiva - Éxito: {permissive_results.get('success', False)}")
                print(f"   Resultados permisivos: {permissive_results.get('results_count', 0)}")
            
            # 4. Test completo de la pregunta
            print(f"\nTEST COMPLETO DE PREGUNTA:")
            session_id = f"analysis_{datetime.now().strftime('%H%M%S')}"
            
            result = self.chatbot_service.process_question(question, session_id)
            
            success = "error" not in result and bool(result.get("response"))
            response_length = len(result.get("response", ""))
            
            print(f"   Respuesta exitosa: {success}")
            print(f"   Longitud respuesta: {response_length} caracteres")
            
            if success:
                preview = result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", "")
                print(f"   Preview: {preview}")
            else:
                print(f"   Error: {result.get('error', 'Sin respuesta útil')}")
            
            return {
                "question": question,
                "embeddings_generated": question_vector is not None,
                "search_results": context_results,
                "chatbot_success": success,
                "response_length": response_length
            }
        
        except Exception as e:
            print(f"Error en análisis: {e}")
            return {"error": str(e)}

    def test_problematic_questions(self) -> Dict[str, Any]:
        """Prueba preguntas conocidas como problemáticas"""
        
        # Leer preguntas no respondidas del archivo
        problematic_questions = []
        try:
            with open("preguntas_no_respondidas.txt", "r", encoding="utf-8") as f:
                problematic_questions = [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            print("No se encontró archivo de preguntas no respondidas")
        
        # Preguntas de test adicionales
        test_questions = [
            "como defino una cuenta?",
            "como creo una empresa?",
            "que es un año fiscal?",
            "como cerrar un ejercicio?",
            "que es un asiento y para que sirve?",
            "como emitir un reporte?",
            "donde encuentro el plan de cuentas?",
            "como modificar datos de empresa?"
        ]
        
        all_questions = list(set(problematic_questions + test_questions))[:10]
        
        print(f"\nPROBANDO {len(all_questions)} PREGUNTAS PROBLEMÁTICAS")
        print("=" * 80)
        
        results = {}
        
        for i, question in enumerate(all_questions, 1):
            print(f"\n[{i}/{len(all_questions)}] Pregunta: '{question}'")
            
            # Test rápido (3 intentos)
            consistency_result = self.analyze_question_consistency(question, num_tests=3)
            
            results[question] = {
                "success_rate": consistency_result["consistency_analysis"]["success_rate"],
                "main_issue": consistency_result["consistency_analysis"]["main_issue"]
            }
            
            print(f"   Resultado: {consistency_result['consistency_analysis']['success_rate']:.1f}% éxito")
        
        # Resumen general
        print(f"\nRESUMEN GENERAL DE PREGUNTAS PROBLEMÁTICAS")
        print("=" * 60)
        
        successful_questions = [q for q, r in results.items() if r["success_rate"] > 60]
        problematic_questions = [q for q, r in results.items() if r["success_rate"] <= 60]
        
        print(f"Preguntas ahora funcionando: {len(successful_questions)}")
        print(f"Preguntas aún problemáticas: {len(problematic_questions)}")
        
        if problematic_questions:
            print(f"\nPREGUNTAS QUE NECESITAN ATENCIÓN:")
            for q in problematic_questions:
                print(f"    {q} ({results[q]['success_rate']:.1f}%)")
        
        return {
            "total_questions": len(all_questions),
            "successful_questions": successful_questions,
            "problematic_questions": problematic_questions,
            "detailed_results": results
        }

    def benchmark_performance(self, num_questions: int = 20) -> Dict[str, Any]:
        """Ejecuta un benchmark completo del rendimiento"""
        print(f"\nBENCHMARK DE RENDIMIENTO ({num_questions} preguntas)")
        print("=" * 80)
        
        # Preguntas de benchmark variadas
        benchmark_questions = [
            "como crear una cuenta contable?",
            "que es easysoft?",
            "como defino una empresa?",
            "donde esta el plan de cuentas?",
            "como emitir un reporte?",
            "que es un asiento contable?",
            "como cerrar ejercicio?",
            "donde modificar datos empresa?",
            "como consultar el mayor?",
            "que es año fiscal?",
            "como hacer backup?",
            "donde estan los parametros?",
            "como importar datos?",
            "que es debe y haber?",
            "como crear usuario?",
            "donde ver reportes?",
            "como exportar datos?",
            "que es balance?",
            "como configurar impuestos?",
            "donde cambiar contraseña?"
        ]
        
        # Seleccionar preguntas para el test
        test_questions = benchmark_questions[:num_questions]
        
        results = {
            "total_questions": len(test_questions),
            "successful_responses": 0,
            "failed_responses": 0,
            "total_time": 0,
            "avg_response_time": 0,
            "question_results": []
        }
        
        for i, question in enumerate(test_questions, 1):
            print(f"[{i}/{len(test_questions)}] Procesando: '{question}'")
            
            start_time = time.time()
            
            try:
                session_id = f"benchmark_{i}"
                response = self.chatbot_service.process_question(question, session_id)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                success = "error" not in response and bool(response.get("response"))
                
                question_result = {
                    "question": question,
                    "success": success,
                    "response_time": response_time,
                    "response_length": len(response.get("response", "")),
                    "has_error": "error" in response
                }
                
                results["question_results"].append(question_result)
                results["total_time"] += response_time
                
                if success:
                    results["successful_responses"] += 1
                    print(f"   ? {response_time:.2f}s - {len(response.get('response', ''))} chars")
                else:
                    results["failed_responses"] += 1
                    print(f"   ? {response_time:.2f}s - FALLÓ")
            
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f"   ?? {response_time:.2f}s - ERROR: {e}")
                
                results["question_results"].append({
                    "question": question,
                    "success": False,
                    "response_time": response_time,
                    "error": str(e)
                })
                results["failed_responses"] += 1
                results["total_time"] += response_time
        
        # Calcular estadísticas
        results["success_rate"] = (results["successful_responses"] / results["total_questions"]) * 100
        results["avg_response_time"] = results["total_time"] / results["total_questions"]
        
        successful_times = [r["response_time"] for r in results["question_results"] if r["success"]]
        if successful_times:
            results["avg_successful_response_time"] = sum(successful_times) / len(successful_times)
        else:
            results["avg_successful_response_time"] = 0
        
        print(f"\nRESULTADOS DEL BENCHMARK:")
        print("=" * 50)
        print(f"Tasa de éxito: {results['success_rate']:.1f}%")
        print(f"Tiempo promedio: {results['avg_response_time']:.2f}s")
        print(f"Tiempo promedio exitoso: {results['avg_successful_response_time']:.2f}s")
        print(f"Respuestas exitosas: {results['successful_responses']}")
        print(f"Respuestas fallidas: {results['failed_responses']}")
        
        return results

    def cleanup(self):
        """Limpia recursos"""
        try:
            self.weaviate_service.close()
            print("Conexiones cerradas correctamente.")
        except Exception as e:
            print(f"Error cerrando conexiones: {e}")

def main():
    """Función principal para ejecutar análisis de debug"""
    import sys
    
    debugger = ChatbotDebugger()
    
    try:
        if len(sys.argv) < 2:
            print("HERRAMIENTAS DE DEBUG DISPONIBLES:")
            print("=" * 50)
            print("python3 debug_chatbot.py consistency 'tu pregunta'")
            print("python3 debug_chatbot.py problematic")
            print("python3 debug_chatbot.py simple 'tu pregunta'")
            print("python3 debug_chatbot.py benchmark [num_preguntas]")
            return
        
        command = sys.argv[1].lower()
        
        if command == "consistency":
            if len(sys.argv) < 3:
                print("? Uso: python3 debug_chatbot.py consistency 'tu pregunta'")
                return
            
            question = sys.argv[2]
            num_tests = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            debugger.analyze_question_consistency(question, num_tests)
        
        elif command == "problematic":
            debugger.test_problematic_questions()
        
        elif command == "simple":
            if len(sys.argv) < 3:
                print("? Uso: python3 debug_chatbot.py simple 'tu pregunta'")
                return
            
            question = sys.argv[2]
            debugger.simple_search_analysis(question)
        
        elif command == "benchmark":
            num_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            debugger.benchmark_performance(num_questions)
        
        else:
            print(f"? Comando desconocido: {command}")
    
    finally:
        debugger.cleanup()

if __name__ == "__main__":
    main()