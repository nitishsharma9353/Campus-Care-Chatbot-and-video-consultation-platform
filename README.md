# CampusCare – AI-Powered Campus Telemedicine Platform

## 📌 Overview
CampusCare is a full-stack AI-powered telemedicine platform developed to improve healthcare accessibility for college hostel students. The system integrates an AI health assistant, appointment booking, doctor notifications, and real-time video consultation into a single web application.

The platform enables students to:
- Chat with an AI-powered health assistant
- Book appointments with affiliated hospitals
- Attend online consultations with doctors
- Track appointment status in real time

Doctors can:
- Receive appointment notifications
- Confirm appointments
- Conduct video consultations
- Update consultation status

---

# 🚀 Features

## 🤖 AI Health Assistant (MedBot)
- Powered by Groq LLaMA 3.1
- Conversational AI chatbot for health guidance
- Maintains rolling conversation history
- Suggests medical consultation when necessary
- Provides empathetic and interactive responses

---

## 🏥 College-Hospital Mapping
- Students can only access hospitals affiliated with their college
- Dynamic hospital filtering based on institution
- Secure institutional healthcare access

---

## 📅 Appointment Booking System
### Student Features
- Book appointments
- Select hospitals
- Choose doctors (optional)
- Add symptoms and consultation reason
- Set priority level
- Select preferred consultation time

### Doctor Features
- Receive appointment notifications
- Confirm appointments
- Add doctor notes
- Update appointment status

### Appointment Workflow
```text
Waiting → Confirmed → In Progress → Completed
```

---

## 🎥 Real-Time Video Consultation
- Integrated using Twilio Video API
- Secure room-based video consultation
- Audio and video support
- Microphone and camera controls
- Real-time participant handling

---

## 🔐 Authentication & Security
- Session-based authentication
- Role-based access control
- SHA-256 password hashing
- Secure API endpoints

### User Roles
- Student
- Doctor

---

# 🛠️ Tech Stack

## Frontend
- HTML
- CSS
- JavaScript

## Backend
- Python
- Flask
- Flask-CORS

## AI Integration
- Groq API
- LLaMA 3.1

## Video Consultation
- Twilio Video API
- WebRTC

## Storage
- JSON Flat File Database

---

# ⚙️ Modules

## 1. Authentication Module
- User Signup
- User Login
- Token Validation
- Password Hashing

## 2. MedBot AI Module
- AI Chat System
- Prompt Engineering
- Chat Context Management
- Health Guidance

## 3. Appointment Module
- Appointment Booking
- Hospital Validation
- Doctor Assignment
- Status Tracking

## 4. Notification Module
- Doctor Notifications
- Pending Appointment Tracking
- Real-Time Updates

## 5. Video Consultation Module
- Twilio Token Generation
- Video Room Creation
- Media Controls
- Video Connection Management

---

# 📂 Project Workflow

```text
Student Login
      ↓
Chat with MedBot
      ↓
Book Appointment
      ↓
Doctor Receives Notification
      ↓
Doctor Confirms Appointment
      ↓
Video Room Generated
      ↓
Student & Doctor Join Consultation
      ↓
Appointment Completed
```

---

# 🧪 Testing

## Unit Testing
- Password hashing validation
- Token generation testing
- Chat history testing
- Hospital mapping validation

## Integration Testing
- Frontend-backend communication
- MedBot API flow
- Notification system integration
- Twilio token validation

## System Testing
- Complete appointment lifecycle
- Role-based access testing
- Concurrent request handling
- Data persistence testing

## Acceptance Testing
- Student user experience
- Doctor workflow testing
- Video consultation quality testing

---

# 📈 Advantages
- Improves healthcare accessibility for hostel students
- Enables remote consultation
- AI-assisted healthcare guidance
- Easy-to-use appointment workflow
- Scalable and cost-effective architecture
- Supports telemedicine within educational institutions

---

# 🔮 Future Scope

## Functional Enhancements
- MongoDB/PostgreSQL integration
- Push notification system
- Digital prescription management
- Medical history tracking
- Pharmacy integration

## AI Improvements
- Symptom severity classification
- Multilingual MedBot support
- Responsible AI auditing

## Platform Expansion
- React Native mobile application
- Analytics dashboard
- Large-scale institutional deployment

---

# 📚 APIs & Technologies Used
- Flask
- Groq API
- LLaMA 3.1
- Twilio Video API
- WebRTC
- Flask-CORS
- SHA-256 Hashing
- JSON Data Storage

---

# 🎯 Objective
The main objective of CampusCare is to bridge the healthcare accessibility gap for college hostel students by providing an AI-assisted telemedicine platform that combines healthcare guidance, appointment scheduling, and online consultation into one unified digital system.

---

# 👨‍💻 Developed By
Nitish Sharma  
BCA (Data Science)  
CMR University
