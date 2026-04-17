# FabrIQ Deployment Guide

Complete guide to deploy the FabrIQ frontend and backend system.

## 📋 Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Trained YOLO model (`.pt` file)
- Git

## 🚀 Local Development Setup

### Option 1: Quick Start (Windows)
```bash
start.bat
```

### Option 2: Quick Start (Linux/Mac)
```bash
chmod +x start.sh
./start.sh
```

### Option 3: Manual Setup

#### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Update MODEL_PATH in app.py to your trained model
python app.py
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Production Deployment

### Frontend Deployment (Vercel/Netlify)

1. **Build the frontend:**
```bash
cd frontend
npm run build
```

2. **Deploy to Vercel:**
```bash
npm install -g vercel
vercel
```

3. **Deploy to Netlify:**
   - Drag and drop the `frontend/dist` folder to Netlify
   - Or use Netlify CLI: `netlify deploy --prod`

### Backend Deployment (AWS/GCP/Azure)

#### Using Gunicorn (Recommended)
```bash
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Using Docker
```bash
docker build -t fabriq-backend ./backend
docker run -p 5000:5000 fabriq-backend
```

### Full Stack with Docker Compose

```bash
docker-compose up -d
```

This starts both frontend and backend services.

## 🔧 Configuration

### Environment Variables

**Frontend (.env):**
```
VITE_API_URL=https://your-backend-url.com/api
```

**Backend (.env):**
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
MODEL_PATH=/path/to/model.pt
```

### Update Model Path

Edit `backend/app.py`:
```python
MODEL_PATH = 'path/to/your/trained/model.pt'
```

### Update Class Names

If your model uses different classes, update `backend/app.py`:
```python
CLASSES = ['your', 'class', 'names', ...]
```

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Implement rate limiting
- [ ] Add database for user management
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted domains
- [ ] Add input validation
- [ ] Implement logging and monitoring

## 📱 Mobile App Integration

The frontend is mobile-responsive. For a native mobile app:

1. **React Native:**
   - Reuse React components
   - Use React Native Navigation
   - Connect to same backend API

2. **Flutter:**
   - Create new Flutter app
   - Use same API endpoints
   - Implement similar UI/UX

## 🔄 Real-Time Features

To add WebSocket support for real-time streaming:

1. Install Socket.IO:
```bash
pip install flask-socketio
npm install socket.io-client
```

2. Update backend to handle WebSocket connections
3. Update frontend to connect via WebSocket

## 📊 Database Integration

Replace mock data with a real database:

### PostgreSQL Example
```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://user:pass@localhost/fabriq')
Session = sessionmaker(bind=engine)
```

### MongoDB Example
```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.fabriq
```

## 🐛 Troubleshooting

### Model Not Loading
- Verify model file path is correct
- Check file permissions
- Ensure ultralytics version is compatible

### CORS Errors
- Verify backend CORS configuration
- Check API URL in frontend
- Ensure backend allows frontend origin

### Authentication Issues
- Verify JWT secret key
- Check token expiration
- Ensure tokens are stored correctly

### Port Conflicts
- Change ports in `vite.config.js` (frontend)
- Change port in `app.py` (backend)
- Update Docker ports if using containers

## 📈 Monitoring & Logging

### Add Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Add Monitoring (Prometheus/Grafana)
- Install Prometheus client
- Expose metrics endpoint
- Set up Grafana dashboards

## 🎯 Next Steps

1. **Integrate your trained YOLO model**
2. **Add database for persistent storage**
3. **Implement WebSocket for real-time streaming**
4. **Add role-based access control (RBAC)**
5. **Set up CI/CD pipeline**
6. **Add automated testing**
7. **Implement caching (Redis)**
8. **Add load balancing for scalability**

## 📞 Support

For issues or questions:
- Check the main README
- Review error logs
- Verify configuration files
- Test API endpoints with Postman/curl

---

**Ready to deploy!** 🚀

