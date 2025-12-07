# AWS Migration README

## Project Structure

This project has been restructured for AWS deployment with FastAPI backend and static frontend.

### Backend (/backend)
- **app/main.py**: FastAPI application with API endpoints
- **services/**: Business logic services
  - **deal_generator.py**: Deal parameter generation
  - **negotiation_service.py**: Negotiation logic and AI integration
- **requirements.txt**: Python dependencies

### Frontend (/frontend)
- **index.html**: Main UI
- **script.js**: Frontend logic
- **api.js**: API client for backend communication
- **style.css**: Styling

### Original Files
- **app.py**: Original Streamlit application (kept for reference)
- **main.py**: Example negotiation script (kept for reference)

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file with:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

5. Run locally:
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Update API_BASE_URL in `frontend/api.js` to point to your backend
2. For local development: `http://localhost:8000`
3. For AWS: Your API Gateway URL

4. Serve frontend files:
   - Use any static file server
   - Or upload to AWS Amplify

## AWS Deployment

### Lambda + API Gateway (Backend)

1. Install deployment dependencies:
```bash
pip install mangum
```

2. Package application:
```bash
cd backend
pip install -r requirements.txt -t package/
cp -r app package/
cp -r services package/
cd package
zip -r ../deployment.zip .
```

3. Create Lambda function:
   - Runtime: Python 3.11
   - Handler: app.main.lambda_handler
   - Upload deployment.zip
   - Add environment variable: GOOGLE_API_KEY

4. Create API Gateway:
   - Type: HTTP API
   - Integration: Lambda function
   - Enable CORS

### Amplify (Frontend)

1. Push frontend folder to Git repository

2. Connect to AWS Amplify:
   - Choose repository
   - Build settings: None (static files)
   - Publish directory: frontend

3. Update `frontend/api.js`:
   - Set API_BASE_URL to your API Gateway URL

## API Endpoints

- `GET /`: Health check
- `POST /api/session/new`: Create new negotiation session
- `POST /api/chat`: Send message and get AI response
- `POST /api/evaluate`: Get negotiation evaluation
- `GET /api/session/{session_id}`: Get session details

## Environment Variables

- **GOOGLE_API_KEY**: Gemini API key for AI responses

## Testing Locally

1. Start backend:
```bash
cd backend/app
uvicorn main:app --reload
```

2. Open frontend/index.html in browser
   - Or use Live Server extension in VS Code
   - Update api.js to use http://localhost:8000

## Migration Notes

The application has been migrated from:
- **Streamlit monolith** → **FastAPI backend + Static frontend**
- **Session state** → **API session management**
- **Streamlit UI** → **Custom HTML/CSS/JS UI**

All business logic from app.py has been preserved in the backend services.
