# 🚀 Quick Start Guide - FabrIQ Frontend & Backend

## Prerequisites

- **Python 3.9+** installed
- **Node.js 18+** and npm installed
- **Trained YOLO model** (you've already set the path in `backend/app.py`)

## Step 1: Setup Backend

### Option A: Using Virtual Environment (Recommended)

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

### Option B: Direct Installation

```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Expected Output:**
```
✅ Model loaded: C:\Users\hp\Desktop\FabrIQ_dataset\runs\detect\fabriq_defect_detection\weights\best.pt
 * Running on http://127.0.0.1:5000
```

**Keep this terminal open!** The backend must be running.

## Step 2: Setup Frontend

Open a **NEW terminal window** (keep backend running):

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 3: Access the Application

1. Open your browser
2. Go to: **http://localhost:3000**
3. Login with:
   - **Email:** `admin@fabriq.com`
   - **Password:** `admin123`

## 🎯 What You'll See

- **Dashboard:** Overview with statistics and charts
- **Real-Time Detection:** Upload images or use camera for defect detection
- **Analytics:** View defect trends and quality distribution
- **Reports:** Export inspection reports as PDF/CSV
- **Settings:** Configure detection thresholds

## 🔧 Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError` or import errors
```bash
# Make sure you're in the backend folder and dependencies are installed
cd backend
pip install -r requirements.txt
```

**Problem:** Model not loading
- Check the path in `backend/app.py` is correct
- Ensure the model file exists at that path
- Use forward slashes or raw string: `r"C:\Users\..."`

**Problem:** Port 5000 already in use
```python
# Edit backend/app.py, change the port:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
```

### Frontend Issues

**Problem:** `npm: command not found`
- Install Node.js from https://nodejs.org/
- Restart your terminal after installation

**Problem:** Port 3000 already in use
```bash
# Edit frontend/vite.config.js, change port:
server: {
  port: 3001,  // Use different port
}
```

**Problem:** CORS errors
- Make sure backend is running on port 5000
- Check `frontend/src/utils/api.js` has correct API URL

### Connection Issues

**Problem:** Frontend can't connect to backend
1. Verify backend is running (check terminal)
2. Test backend directly: Open http://localhost:5000/api/health in browser
3. Should see: `{"status":"healthy","model_loaded":true}`

## 📝 Quick Commands Reference

### Start Backend
```bash
cd backend
python app.py
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Build Frontend for Production
```bash
cd frontend
npm run build
# Output in frontend/dist/
```

## 🐳 Using Docker (Alternative)

If you have Docker installed:

```bash
# Build and run both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## ✅ Verification Checklist

- [ ] Backend server running on http://localhost:5000
- [ ] Frontend server running on http://localhost:3000
- [ ] Can access http://localhost:3000 in browser
- [ ] Can login with admin credentials
- [ ] Model loaded successfully (check backend terminal)

## 🎉 You're Ready!

Once both servers are running, you can:
- Upload fabric images for defect detection
- View real-time detection results
- Access analytics and reports
- Configure settings

**Need help?** Check `README_FRONTEND.md` and `DEPLOYMENT_GUIDE.md` for more details.

