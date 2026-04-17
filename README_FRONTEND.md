# FabrIQ Frontend - Deployment Guide

Complete frontend and backend system for FabrIQ Fabric Defect Detection.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Trained YOLO model (`.pt` file)

### 1. Frontend Setup

```bash
cd frontend
npm install
npm run dev  # Development server on http://localhost:3000
npm run build  # Production build
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Update MODEL_PATH in app.py to point to your trained model
python app.py  # Server runs on http://localhost:5000
```

### 3. Environment Variables

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:5000/api
```

## 📁 Project Structure

```
fabriq-frontend/
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── context/        # React context (Auth)
│   │   ├── utils/         # API utilities
│   │   └── App.jsx        # Main app component
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app.py             # Flask API server
│   └── requirements.txt
└── README_FRONTEND.md
```

## 🎯 Features

### ✅ Implemented
- **Authentication System** - Login with JWT tokens
- **Dashboard** - Overview with statistics and charts
- **Real-Time Detection** - Image upload and camera support
- **Analytics** - Defect trends and quality distribution
- **Reports** - Exportable PDF/CSV reports
- **Settings** - Configurable detection thresholds
- **Responsive Design** - Mobile-friendly interface

### 🔄 To Integrate
- Connect to your trained YOLO model
- Add database (PostgreSQL/MongoDB) for persistent storage
- Implement WebSocket for real-time streaming
- Add role-based access control (RBAC)
- Deploy to cloud (AWS, Azure, or Vercel)

## 🔧 Configuration

### Update Model Path
Edit `backend/app.py`:
```python
MODEL_PATH = 'path/to/your/trained/model.pt'
```

### Update Class Names
Edit `backend/app.py` if your classes differ:
```python
CLASSES = ['your', 'class', 'names', ...]
```

## 📦 Deployment

### Frontend (Vercel/Netlify)
```bash
cd frontend
npm run build
# Deploy dist/ folder
```

### Backend (AWS/GCP/Azure)
```bash
# Use gunicorn for production
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Recommended)
```bash
# Build and run
docker-compose up -d
```

## 🔐 Security Notes

- Change `SECRET_KEY` in production
- Use environment variables for sensitive data
- Implement HTTPS in production
- Add rate limiting
- Use database for user management

## 📱 Mobile App (Future)

The mobile app can be built using:
- React Native
- Flutter
- Or use the responsive web app

## 🆘 Troubleshooting

### Model Not Loading
- Check model path is correct
- Ensure model file exists
- Verify ultralytics version compatibility

### CORS Errors
- Ensure backend CORS is configured
- Check API URL in frontend `.env`

### Authentication Issues
- Verify JWT secret key matches
- Check token expiration

## 📞 Support

For issues or questions, refer to the main project documentation.

