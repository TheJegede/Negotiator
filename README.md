# AI Supply Chain Negotiator

An interactive web application where students negotiate with an AI seller named "Alex" to purchase microprocessors. Built with FastAPI backend (AWS Lambda) and vanilla JavaScript frontend (AWS Amplify).

## Features

- **Dynamic Deal Parameters**: Each student gets unique, reproducible deal parameters based on their student ID
- **AI Negotiation**: Realistic negotiation tactics including anchoring, bundling, time pressure, and information gathering
- **Auto-Evaluation**: Performance measured on 5 key metrics:
  1. Price Achievement
  2. Efficiency
  3. Relationship Building
  4. Value Creation
  5. Strategic Negotiation
- **Serverless Architecture**: AWS Lambda backend with API Gateway and Amplify frontend

## Project Structure

```
Negotiator/
├── backend/
│   ├── app.py              # FastAPI application with all endpoints
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML interface
│   ├── app.js              # Vanilla JavaScript application logic
│   └── style.css           # Styling
└── README.md
```

## API Endpoints

### POST /api/sessions/new
Create a new negotiation session.

**Request:**
```json
{
  "student_id": "S12345"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "student_id": "S12345",
  "initial_message": {...},
  "deal_parameters": {
    "base_price": 75,
    "target_quantity": 1200,
    "delivery_days": 45,
    "quality_grade": "A",
    "warranty_months": 12
  }
}
```

### POST /api/chat
Send a message in a negotiation session.

**Request:**
```json
{
  "session_id": "uuid",
  "message": "Can you do $70 per unit?"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "alex_response": "I can see you're serious...",
  "status": "active",
  "turn_count": 2,
  "deal_closed": false,
  "evaluation": null
}
```

### GET /api/sessions/{session_id}
Get session details including full conversation history.

**Response:**
```json
{
  "session_id": "uuid",
  "student_id": "S12345",
  "status": "active",
  "messages": [...],
  "turn_count": 3,
  "deal_closed": false,
  "current_state": {...},
  "evaluation": null
}
```

## Local Development

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn app:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Serve the files using a local server:
```bash
python -m http.server 8080
```
Or use any static file server.

3. Open `http://localhost:8080` in your browser

4. Update `app.js` to point to your local backend:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## AWS Deployment

### Backend (AWS Lambda + API Gateway)

1. Install dependencies in a deployment package:
```bash
cd backend
pip install -r requirements.txt -t package/
cp app.py package/
cd package
zip -r ../deployment.zip .
```

2. Create a Lambda function:
   - Runtime: Python 3.9+
   - Handler: `app.handler`
   - Upload `deployment.zip`

3. Configure API Gateway:
   - Create a REST API or HTTP API
   - Add routes for each endpoint
   - Deploy the API
   - Update frontend `API_BASE_URL` with your API Gateway URL

### Frontend (AWS Amplify)

1. Initialize Amplify in the frontend directory:
```bash
cd frontend
amplify init
```

2. Add hosting:
```bash
amplify add hosting
```

3. Deploy:
```bash
amplify publish
```

4. Update `app.js` with your production API Gateway URL

## Negotiation Tips

- **Be polite**: The AI tracks relationship building based on courteous language
- **Negotiate efficiently**: Fewer turns result in better efficiency scores
- **Know your limits**: The AI has bottom-line prices and quantities
- **Create value**: Negotiate for larger quantities for better value scores
- **Be strategic**: Avoid unnecessary concessions for better strategic scores

## AI Negotiation Tactics

Alex uses several realistic negotiation tactics:

1. **Anchoring**: Starts with a high initial offer and resists large changes
2. **Bundling**: Offers volume discounts for larger quantities
3. **Time Pressure**: Charges more for rush deliveries
4. **Information Gathering**: Asks questions to understand your needs
5. **Strategic Concessions**: Makes small, calculated price reductions

## Evaluation Metrics

Each completed negotiation is scored on:

1. **Price Achievement (0-100)**: How much you saved vs. maximum possible savings
2. **Efficiency (0-100)**: Based on number of turns (fewer is better)
3. **Relationship Building (0-100)**: Based on polite and professional communication
4. **Value Creation (0-100)**: Quantity secured vs. target quantity
5. **Strategic Negotiation (0-100)**: How well you negotiated (fewer concessions from Alex is better)

## Technologies Used

- **Backend**: FastAPI, Python 3.9+, Pydantic, Mangum (for AWS Lambda)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Deployment**: AWS Lambda, API Gateway, Amplify

## License

MIT License
