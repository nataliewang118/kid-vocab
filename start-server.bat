@echo off
cd /d "%~dp0"

netstat -ano | findstr ":8010" | findstr "LISTENING" >nul && (
  echo.
  echo  Port 8010 is ALREADY IN USE by another program.
  echo  Close it first, or the iPad may load the OTHER app.
  echo  ^(Windows python binds a busy port without complaining.^)
  echo.
  pause & exit /b
)

echo.
echo  kid-vocab - local server on port 8010
echo.
echo  On the iPad (same Wi-Fi), open one of these in Safari:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=* delims= " %%b in ("%%a") do echo      http://%%b:8010
)
echo.
echo  Then: Share - Add to Home Screen.
echo  Keep this window open while using the app. Ctrl+C stops it.
echo.
python -m http.server 8010
pause
