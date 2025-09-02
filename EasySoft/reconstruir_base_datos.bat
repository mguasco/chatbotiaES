@echo off
echo ⚠️ RECONSTRUCCIÓN COMPLETA DE LA BASE DE DATOS
echo.
echo Esto eliminará todos los datos actuales y los recreará.
echo.
set /p confirm="¿Estás seguro? (S/N): "
if /i "%confirm%" NEQ "S" goto :cancel

echo.
echo 🔄 Reconstruyendo base de datos completa...
python weaviate_manager.py rebuild

echo.
echo ✅ Reconstrucción completada
goto :end

:cancel
echo ❌ Operación cancelada

:end
pause
