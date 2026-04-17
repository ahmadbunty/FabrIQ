FabrIQ – AI Powered Fabric Defect Detection System

FabrIQ is an AI-driven fabric inspection system designed to automatically detect defects in textile materials using computer vision and edge computing. The system uses a camera connected to an edge device to analyze fabric in real time and identify defects such as holes, stains, and weaving faults.

The goal of FabrIQ is to assist textile manufacturers by improving quality control, reducing manual inspection errors, and increasing production efficiency.

Project Overview

Manual inspection of fabric in textile industries is often slow, inconsistent, and prone to human error. FabrIQ addresses this problem by using an automated vision-based inspection system.

The system captures images of fabric through a camera, processes them using an AI object detection model, and identifies potential defects. Detected defects are logged and stored in a database for monitoring and analysis.

This solution is designed to be lightweight and deployable on edge hardware for real-time industrial applications.

Key Features

• Automated fabric defect detection
• Real-time image processing
• Edge AI deployment
• Defect classification and logging
• Database integration for defect tracking
• Hardware-based inspection prototype
• Scalable architecture for textile industry deployment

System Architecture

The FabrIQ system follows the pipeline below:

Camera → Image Capture → AI Model Inference → Defect Detection → Database Storage → Dashboard Visualization

Fabric images are captured using a camera.
The edge device processes images using an object detection model.
Detected defects are classified and marked.
Detection results are stored in a database.
The dashboard displays detected defects and related information.
Technologies Used
Artificial Intelligence
YOLOv8 for object detection
Hardware
NVIDIA Jetson Nano
Camera module for fabric capture
Backend & Database
Firebase Firestore for storing defect records
Firebase Storage for image storage
Programming
Python
JavaScript
Development Tools
Git
GitHub
Hardware Setup

The hardware system consists of the following components:

• Jetson Nano edge computing device
• Camera module for image capture
• Fabric roller setup for controlled movement
• Power supply and mounting frame

The camera captures fabric images while the Jetson Nano processes them in real time using the trained detection model.

Installation Guide
1 Clone the Repository
git clone https://github.com/ahmadbunty/fabriq.git
cd fabriq
2 Install Dependencies
pip install -r requirements.txt
3 Run Detection
cd frontend 
run npm dev
cd backend 
python app.py



The system will start capturing images from the camera and detecting fabric defects.


Project Structure
FabrIQ
│
├── dataset
│   ├── images
│   ├── labels
│
├── models
│   ├── trained_model
│
├── hardware
│   ├── camera_setup
│
├── backend
│   ├── firebase_integration
│
├── scripts
│   ├── detect.py
│   ├── train.py
│
└── README.md
Future Improvements

• Improve model accuracy using larger datasets
• Integrate conveyor belt fabric inspection
• Real-time monitoring dashboard
• Industrial scale deployment
• Automated reporting and analytics
