# validate_encoding.py - Validar y corregir codificación de archivos
import os
import chardet
from typing import Dict, List, Tuple

class EncodingValidator:
    def __init__(self):
        self.supported_extensions = {
            '.html', '.htm', '.css', '.js', '.txt', '.py', '.xml', '.json'
        }
    
    def detect_file_encoding(self, file_path: str) -> Tuple[str, float]:
        """Detecta la codificación de un archivo"""
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Leer primeros 10KB
                result = chardet.detect(raw_data)
                return result['encoding'], result['confidence']
        except Exception as e:
            print(f"Error detectando codificación de {file_path}: {e}")
            return 'unknown', 0.0
    
    def validate_utf8(self, file_path: str) -> bool:
        """Valida si un archivo es UTF-8 válido"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file.read()
                return True
        except UnicodeDecodeError:
            return False
        except Exception:
            return False
    
    def convert_to_utf8(self, file_path: str, source_encoding: str) -> bool:
        """Convierte un archivo a UTF-8"""
        try:
            # Leer con codificación original
            with open(file_path, 'r', encoding=source_encoding) as file:
                content = file.read()
            
            # Escribir en UTF-8
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"? Convertido a UTF-8: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"? Error convertiendo {file_path}: {e}")
            return False
    
    def scan_directory(self, root_path: str) -> Dict[str, List[str]]:
        """Escanea un directorio y clasifica archivos por codificación"""
        results = {
            'utf8_valid': [],
            'utf8_invalid': [],
            'other_encoding': [],
            'binary_files': [],
            'errors': []
        }
        
        print(f"?? Escaneando archivos en: {root_path}")
        
        for root, dirs, files in os.walk(root_path):
            # Saltar directorios comunes que no necesitamos
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                # Solo procesar archivos de texto
                if file_ext not in self.supported_extensions:
                    results['binary_files'].append(file_path)
                    continue
                
                try:
                    encoding, confidence = self.detect_file_encoding(file_path)
                    
                    if encoding is None or encoding == 'unknown':
                        results['errors'].append(file_path)
                        continue
                    
                    if encoding.lower().startswith('utf-8') or encoding.lower() == 'ascii':
                        if self.validate_utf8(file_path):
                            results['utf8_valid'].append(file_path)
                        else:
                            results['utf8_invalid'].append(file_path)
                    else:
                        results['other_encoding'].append((file_path, encoding, confidence))
                        
                except Exception as e:
                    results['errors'].append(file_path)
                    print(f"?? Error procesando {file_path}: {e}")
        
        return results
    
    def fix_encoding_issues(self, root_path: str, auto_convert: bool = False) -> Dict[str, int]:
        """Corrige problemas de codificación en un directorio"""
        results = self.scan_directory(root_path)
        stats = {
            'converted': 0,
            'errors': 0,
            'skipped': 0
        }
        
        print(f"\n?? Resumen de codificaciones:")
        print(f"   ? UTF-8 válidos: {len(results['utf8_valid'])}")
        print(f"   ? UTF-8 inválidos: {len(results['utf8_invalid'])}")
        print(f"   ?? Otras codificaciones: {len(results['other_encoding'])}")
        print(f"   ?? Archivos binarios: {len(results['binary_files'])}")
        print(f"   ?? Errores: {len(results['errors'])}")
        
        # Mostrar archivos con otras codificaciones
        if results['other_encoding']:
            print(f"\n?? Archivos que necesitan conversión:")
            for file_path, encoding, confidence in results['other_encoding']:
                print(f"   {os.path.basename(file_path)} -> {encoding} ({confidence:.2f})")
        
        # Convertir archivos si auto_convert está habilitado
        if auto_convert and results['other_encoding']:
            print(f"\n?? Convirtiendo archivos a UTF-8...")
            for file_path, encoding, confidence in results['other_encoding']:
                if confidence > 0.7:  # Solo convertir si tenemos confianza alta
                    if self.convert_to_utf8(file_path, encoding):
                        stats['converted'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    print(f"?? Saltando {file_path} (confianza baja: {confidence:.2f})")
                    stats['skipped'] += 1
        
        return stats

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validador de codificación UTF-8")
    parser.add_argument("path", help="Ruta del directorio a validar")
    parser.add_argument("--fix", action="store_true", help="Corregir automáticamente los archivos")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"? Error: La ruta {args.path} no existe")
        return 1
    
    validator = EncodingValidator()
    
    if args.fix:
        print("?? Modo de corrección activado")
        stats = validator.fix_encoding_issues(args.path, auto_convert=True)
        
        print(f"\n?? Resultados:")
        print(f"   Convertidos: {stats['converted']}")
        print(f"   Errores: {stats['errors']}")
        print(f"   Saltados: {stats['skipped']}")
    else:
        print("??? Modo solo lectura (usar --fix para corregir)")
        validator.scan_directory(args.path)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())