# Quick Start Guide - AI Negotiation Platform

## 🚀 Start Development Environment

### Option 1: Quick Start (Both Servers)

**Terminal 1 - Backend:**
```bash
cd "c:\Users\jeged\Downloads\Fall 2025\Agentic AI\negotiation\backend"
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd "c:\Users\jeged\Downloads\Fall 2025\Agentic AI\negotiation\frontend"
python -m http.server 8080
```

**Access:** http://localhost:8080

---

## ✅ Verification Checklist

### 1. Check Environment Variable
```bash
echo $env:GOOGLE_API_KEY
```
If empty, set it:
```bash
$env:GOOGLE_API_KEY = "your-api-key-here"
```

### 2. Test Backend
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok"}`

### 3. Test Frontend
Open browser: http://localhost:8080
- Should see "AI Supply Chain Negotiator"
- Click "New Chat" button
- Should receive greeting from Alex

---

## 📁 Project Structure

```
negotiation/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   └── services/
│   │       ├── ai_service.py    # Gemini AI integration
│   │       ├── deal_generator.py # Parameter generation
│   │       ├── evaluator.py     # Performance scoring
│   │       ├── agreement.py     # Deal detection
│   │       └── extraction.py    # Term parsing
│   └── requirements.txt
├── frontend/
│   ├── index.html               # UI structure
│   ├── style.css               # Styling
│   ├── script.js               # App logic
│   └── api.js                  # API client
└── Documentation/
    ├── CHANGES_APPLIED.md      # This implementation
    ├── INTEGRATION_FIXES.md    # All bug fixes
    ├── TESTING_GUIDE.md        # Test procedures
    └── README_AWS.md           # AWS deployment
```

---

## 🎯 Core Functionality

### Create New Session
```javascript
// Frontend (automatic via button)
api.createSession(studentId);

// Backend endpoint
POST /api/sessions/new
Body: { "student_id": "optional-id" }
```

### Send Message
```javascript
// Frontend
api.sendMessage("I'd like to order at $40 per unit");

// Backend endpoint
POST /api/chat
Body: {
  "session_id": "uuid",
  "user_input": "message"
}
```

### Get Evaluation
```javascript
// Frontend
api.evaluateDeal();

// Backend endpoint
GET /api/deals/{session_id}/evaluate
```

---

## 🔧 Common Issues & Solutions

### Issue: "API class not found"
**Solution:** Check `index.html` loads `api.js` before `script.js`
```html
<script src="api.js"></script>
<script src="script.js"></script>
```

### Issue: CORS errors
**Solution:** Ensure backend is running on port 8000
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Issue: "GOOGLE_API_KEY not found"
**Solution:** Set environment variable
```bash
# Windows PowerShell
$env:GOOGLE_API_KEY = "your-key"

# Linux/Mac
export GOOGLE_API_KEY="your-key"
```

### Issue: "Session not found"
**Solution:** Click "New Chat" to create session first

---

## 📊 API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions/new` | Create session |
| POST | `/api/chat` | Send message |
| GET | `/api/deals/{id}/evaluate` | Get evaluation |
| GET | `/api/sessions/{id}` | Get session |
| DELETE | `/api/sessions/{id}` | Close session |
| GET | `/api/sessions` | List all (admin) |
| GET | `/health` | Health check |

---

## 🧪 Testing Workflow

1. **Start both servers** (see Quick Start above)
2. **Open http://localhost:8080**
3. **Click "New Chat"** → Should show greeting
4. **Type message:** "What's your best price?"
5. **Click Send** → Should receive AI response
6. **Continue negotiating** → 3-5 rounds
7. **Make agreement:** "I accept $44, 42 days, 20000 units"
8. **Click "Finalize Deal"** → Should show evaluation with scores

---

## 📈 Evaluation Metrics

The system scores across 5 dimensions:

1. **Deal Quality (33%)** - Price/delivery vs seller targets
2. **Trade-off Strategy (28%)** - Multi-issue bargaining
3. **Professionalism (17%)** - Tone and communication
4. **Process Management (11%)** - Clarity and organization
5. **Creativity (11%)** - Adaptation and flexibility

**Grade Scale:**
- A: 90-100 (Excellent)
- B: 80-89 (Good)
- C: 70-79 (Satisfactory)
- D: 60-69 (Needs Improvement)
- F: 0-59 (Failing)

---

## 🎓 Student Usage

### Random Parameters
1. Select "Random" radio button
2. Click "New Chat"
3. Each session gets different parameters

### Student ID Parameters
1. Select "Student ID" radio button
2. Enter student ID (e.g., "S12345")
3. Click "New Chat"
4. Same student ID always gets same parameters

---

## 🌐 AWS Deployment

### Backend (Lambda)
```bash
cd backend
pip install -r requirements.txt -t .
zip -r lambda.zip .
# Upload to Lambda with handler: app.main.lambda_handler
```

### Frontend (Amplify)
1. Push frontend folder to Git
2. Connect Amplify to repo
3. Set build settings (static site)
4. Deploy

**Update API URL after deployment:**
```javascript
// In browser console or localStorage
localStorage.setItem('API_BASE_URL', 'https://your-api-url.com');
```

---

## 📞 Support & Documentation

- **Full Implementation:** `CHANGES_APPLIED.md`
- **Integration Fixes:** `INTEGRATION_FIXES.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **AWS Deployment:** `README_AWS.md`
- **Quick Reference:** This file

---

## ✨ Status: Production Ready

All components verified and tested:
✅ Backend FastAPI server  
✅ Frontend UI and API client  
✅ AI integration (Gemini)  
✅ Deal generation  
✅ Agreement detection  
✅ Performance evaluation  
✅ AWS Lambda handler  
✅ CORS configuration  

**Ready for deployment!** 🚀
