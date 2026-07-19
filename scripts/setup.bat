
@echo off
echo ============================================
echo  Vayu-Drishti - Local Dev Setup
echo ============================================
echo.

echo [1/4] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo   Virtual environment created.
) else (
    echo   Virtual environment already exists.
)

echo [2/4] Activating virtual environment and installing backend...
call venv\Scripts\activate.bat
pip install -e backend/ > nul
pip install -r backend/requirements.txt > nul
echo   Backend dependencies installed.

echo [3/4] Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
    npm install --silent
) else (
    echo   Frontend dependencies already installed.
)
cd ..

echo [4/4] Creating data directories...
if not exist "backend\data\graph" mkdir backend\data\graph
if not exist "backend\data\embeddings" mkdir backend\data\embeddings
if not exist "backend\data\satellite" mkdir backend\data\satellite
if not exist "backend\data\sensor" mkdir backend\data\sensor
if not exist "backend\data\weather" mkdir backend\data\weather
if not exist "backend\data\traffic" mkdir backend\data\traffic
if not exist "backend\data\static" mkdir backend\data\static

echo.
echo ============================================
echo  Setup complete!
echo.
echo  To start the application:
echo.
echo    Terminal 1:  python -m backend.main
echo    Terminal 2:  cd frontend ^&^& npm run dev
echo.
echo  Then open http://localhost:3000
echo ============================================
pause
