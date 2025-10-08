@echo off
:: Ir al directorio del proyecto
cd C:\Users\Martin\Desktop\carestino\planning

:: Ejecutar scripts Python
C:\Users\Martin\AppData\Local\Programs\Python\Python312\python.exe acciones.py
C:\Users\Martin\AppData\Local\Programs\Python\Python312\python.exe otta.py
C:\Users\Martin\AppData\Local\Programs\Python\Python312\python.exe reporting_tableau.py

:: Obtener la fecha actual en formato YYYY-MM-DD
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set today=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%

:: Hacer commit y push automático
git add .
git commit -m "%today%"
git push origin main