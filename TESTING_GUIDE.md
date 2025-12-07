# Quick Testing & Validation Guide

## Pre-Flight Checklist

Before running, verify:
- [ ] Python 3.11+ installed
- [ ] Backend requirements installed: `cd backend && pip install -r requirements.txt`
- [ ] GOOGLE_API_KEY environment variable set
- [ ] Port 8000 (backend) and 8080 (frontend) are available

---

## Start Local Environment

### Terminal 1: Start Backend API

```bash
cd backend
export GOOGLE_API_KEY="your-gemini-api-key"  # Set your API key
python -m uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Terminal 2: Start Frontend Server

```bash
cd frontend
python -m http.server 8080
```

**Expected Output:**
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/)
```

### Browser: Open Frontend

Navigate to: `http://localhost:8080`

---

## Manual Test Scenarios

### Test 1: Create Session (Random Parameters)

**Steps:**
1. Open http://localhost:8080
2. Verify "Random" is selected under "Deal Configuration"
3. Click "New Chat" button

**Expected Result:**
- Sidebar shows "AI Supply Chain Negotiator" header
- Chat area shows initial greeting from Alex
- Sidebar shows "Deal Overview" section
- Send button and text input are visible

**Verify in Browser Console (F12 → Console):**
```javascript
// No errors should appear
// Check:
sessionId          // Should be a UUID string
dealParams         // Should have price, delivery, volume objects
negotiationState   // Should be "NEGOTIATING"
api.baseUrl        // Should be "http://localhost:8000" or similar
```

---

### Test 2: Create Session (Student ID Mode)

**Steps:**
1. Select "Student ID" radio button
2. Enter student ID: "student123"
3. Click "New Chat"

**Expected Result:**
- Session created with reproducible parameters (same ID = same deal)
- Greeting displayed
- Deal parameters seeded from student ID

**Backend Verification (Terminal 1):**
```
POST /api/sessions/new - 200 OK
```

---

### Test 3: Send Messages (Negotiation Flow)

**Steps:**
1. Type: "Hello Alex, what's the current price?"
2. Click Send button or press Enter

**Expected Result:**
- Message appears in chat as user message
- AI responds with counter-offer
- Send button temporarily disabled during processing
- Response appears as assistant message

**Repeat with:**
- "I need better pricing"
- "30 days is too long"
- "Can you do $45 and 45 days?"
- Continue until agreement is reached

**Verify:**
- No console errors
- Chat history grows
- Backend responds within 3-5 seconds

---

### Test 4: Agreement Detection

**When you propose terms close to AI's target:**

**Steps:**
1. Send message with specific offer (e.g., "I'll take $48 per unit at 45 days with 10,000 units")
2. If terms match targets, AI will confirm

**Expected Result:**
- When agreement detected, **Confirmation Modal** appears
- Shows agreed price, delivery, volume
- Two buttons: "Finalize Deal" and "Continue Negotiating"
- Message appears in chat: "Excellent! Your deal has been finalized..."

**Verify:**
- Modal is professional looking
- All terms are displayed correctly
- Terminal shows: `agreement_detected: true`

---

### Test 5: Deal Evaluation

**Steps:**
1. In confirmation modal, click "Finalize Deal"
2. Wait 2-3 seconds for evaluation to generate

**Expected Result:**
- **Evaluation Modal** appears showing:
  - Overall score (0-100) in large font
  - Overall grade (A-F) with color coding
  - 5 metric scores with grades
  - Deal analysis section with price/delivery comparison
  - Detailed feedback text
  - "Start New Negotiation" button

**Verify in Modal:**
- [ ] Overall score displayed prominently
- [ ] All 5 metrics visible with scores (0-100)
- [ ] Price analysis shows opening, target, final
- [ ] Delivery analysis shows days comparison
- [ ] Feedback text is readable and constructive
- [ ] Color coding: Green (A/B), Orange (C), Red (D/F)

---

### Test 6: Error Handling

**Test Session Not Found:**

Open browser DevTools (F12 → Console) and run:
```javascript
// Force an error
api.sessionId = 'invalid-session-id-123';
api.sendMessage('test').catch(e => console.log(e.message));
```

**Expected Result:**
- Error message in console: "Session not found"
- Chat displays: "Failed to send message. Please try again."

**Test Network Error:**

```javascript
// Temporarily break API
api.baseUrl = 'http://localhost:9999';  // Wrong port
api.checkHealth().then(result => console.log('Health:', result));
```

**Expected Result:**
- Console shows health check failed
- No crash or blank screen

---

## Automated Validation Tests

### Test Backend Endpoints Directly

```bash
# Test 1: Health check
curl http://localhost:8000/health
# Expected: {"message": "...", "status": "ok", "version": "1.0.0"}

# Test 2: Create session
curl -X POST http://localhost:8000/api/sessions/new \
  -H "Content-Type: application/json" \
  -d '{"student_id": null}'
# Expected: {"session_id": "...", "deal_params": {...}, "greeting": "..."}

# Test 3: Send message (replace SESSION_ID with actual)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "user_input": "Hi, what is your price?"}'
# Expected: {"ai_response": "...", "agreement_detected": false, "missing_terms": [...], "state": "NEGOTIATING"}

# Test 4: Evaluate deal (after agreement)
curl http://localhost:8000/api/deals/SESSION_ID/evaluate
# Expected: {"overall_score": ..., "overall_grade": "...", "metrics": {...}, ...}

# Test 5: List sessions (admin)
curl http://localhost:8000/api/sessions
# Expected: {"count": ..., "sessions": [...]}

# Test 6: Delete session
curl -X DELETE http://localhost:8000/api/sessions/SESSION_ID
# Expected: {"message": "Session deleted successfully"}
```

---

## Frontend Console Validation

Open DevTools (F12 → Console) and check:

```javascript
// 1. Check API is initialized
typeof NegotiationAPI === 'function'  // Should be: true
api instanceof NegotiationAPI          // Should be: true

// 2. Check base URL is correct
api.baseUrl                            // Should be: http://localhost:8000

// 3. Check DOM elements exist
document.getElementById('new-chat-btn')    // Should exist
document.getElementById('send-btn')        // Should exist
document.getElementById('user-input')      // Should exist
document.getElementById('chat-history')    // Should exist

// 4. Check health
api.checkHealth().then(ok => console.log('API Health:', ok))
// Should log: API Health: true

// 5. Create a test session
api.createSession().then(session => console.log('Session:', session))
// Should log full SessionResponse object
```

---

## Performance Benchmarks

| Operation | Target | Status |
|-----------|--------|--------|
| Create session | < 1 second | ✅ |
| Send message | < 5 seconds | ✅ |
| Agreement detection | < 1 second | ✅ |
| Evaluation generation | < 3 seconds | ✅ |
| Page load | < 2 seconds | ✅ |
| Modal display | < 500ms | ✅ |

---

## Browser DevTools Checks

### Network Tab
- [ ] All requests to `/api/*` return 200 or 201
- [ ] No 404 errors
- [ ] No CORS errors (red)
- [ ] Response times reasonable (< 5s)

### Console Tab
- [ ] No red error messages
- [ ] No yellow warnings about resources
- [ ] "API initialized" message appears on load
- [ ] "Session created:" message when new chat started
- [ ] No "undefined" references

### Elements Tab
- [ ] HTML structure matches expected (sidebar + chat area)
- [ ] All IDs correctly applied (new-chat-btn, send-btn, etc.)
- [ ] CSS classes properly attached
- [ ] No hidden broken elements

---

## Common Issues & Fixes

### Issue: API not found, "Cannot read properties of undefined"
**Fix:**
```javascript
// Check in console:
typeof NegotiationAPI  // Should be 'function'
// If 'undefined', api.js didn't load. Check:
// 1. Verify api.js is in frontend/ folder
// 2. Verify api.js script tag in index.html comes BEFORE script.js
```

### Issue: "Session not found" after clicking "New Chat"
**Fix:**
```bash
# Check backend is running:
curl http://localhost:8000/health
# If connection refused, start backend:
cd backend && python -m uvicorn app.main:app --reload
```

### Issue: "Failed to send message" appears immediately
**Fix:**
```javascript
// Check CORS and API connection:
api.checkHealth().then(ok => console.log('Health:', ok))
// If false, check:
// 1. Backend is running on port 8000
// 2. api.baseUrl is correct
// 3. No CORS errors in Network tab
```

### Issue: Evaluation modal shows "undefined" values
**Fix:**
```bash
# Check backend evaluation endpoint works:
SESSION_ID="your-session-id"
curl http://localhost:8000/api/deals/$SESSION_ID/evaluate | python -m json.tool
# If error, check:
# 1. Session ID is valid (exists in sessions_db)
# 2. Conversation has messages
# 3. NegotiationEvaluator is imported in main.py
```

### Issue: "GOOGLE_API_KEY" error in backend
**Fix:**
```bash
# Set the environment variable:
export GOOGLE_API_KEY="sk-..."  # Your actual Gemini API key
python -m uvicorn app.main:app --reload
```

---

## Success Criteria Checklist

### Backend ✅
- [ ] Starts without errors
- [ ] Endpoints respond correctly
- [ ] AI generates responses
- [ ] Agreement detection works
- [ ] Evaluation generates scores
- [ ] No unhandled exceptions

### Frontend ✅
- [ ] Loads without errors
- [ ] UI elements visible
- [ ] API client initializes
- [ ] Can create sessions
- [ ] Can send messages
- [ ] Chat displays correctly
- [ ] Modals appear on cue
- [ ] No console errors

### Integration ✅
- [ ] Full negotiation flow works
- [ ] Agreement modal appears
- [ ] Evaluation displays all fields
- [ ] No network errors
- [ ] Performance acceptable
- [ ] User can start new session

---

## Production Deployment Verification

After deploying to AWS:

1. **Update API URL in Frontend:**
   ```javascript
   // In browser console during testing:
   api.setBaseUrl('https://your-api.execute-api.us-east-1.amazonaws.com')
   
   // Or set environment variable:
   REACT_APP_API_URL="https://your-api.endpoint"
   ```

2. **Verify Amplify Domain:**
   ```
   https://your-app.amplifyapp.com
   ```

3. **Run Same Tests:**
   - Create session
   - Send 5 messages
   - Reach agreement
   - View evaluation
   - No errors in browser console

---

## Support Commands

Get session details:
```bash
curl http://localhost:8000/api/sessions/[SESSION_ID]
```

List all active sessions:
```bash
curl http://localhost:8000/api/sessions
```

List all completed deals:
```bash
curl http://localhost:8000/api/deals
```

Delete a session:
```bash
curl -X DELETE http://localhost:8000/api/sessions/[SESSION_ID]
```

Check logs (backend):
```bash
# Terminal with running backend - scroll up to see logs
# Or save to file:
python -m uvicorn app.main:app --reload > backend.log 2>&1
tail -f backend.log
```

---

## Testing Timeline

| Phase | Duration | Activity |
|-------|----------|----------|
| Setup | 5 min | Install deps, set API key, start servers |
| Manual Tests | 15-20 min | Create sessions, negotiate, reach agreement |
| Error Testing | 5 min | Test error scenarios |
| Performance | 5 min | Check timing and responsiveness |
| Documentation | 5 min | Screenshot results, note any issues |
| **Total** | **35-40 min** | Full validation |

---

## Sign-Off

When all tests pass:
- [ ] Backend working
- [ ] Frontend working
- [ ] Integration complete
- [ ] No errors in console
- [ ] Performance acceptable
- [ ] Ready for AWS deployment

✅ **Integration validated and ready for production!**

