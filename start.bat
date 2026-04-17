@echo off
echo 🚀 Starting FabrIQ System...

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo 📦 Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo ✅ Setup complete!
echo.
echo To start the system:
echo   Terminal 1: cd backend ^&^& venv\Scripts\activate ^&^& python app.py
echo   Terminal 2: cd frontend ^&^& npm run dev
echo.
echo Or use Docker: docker-compose up

pause

