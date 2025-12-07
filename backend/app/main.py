from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
from datetime import datetime

try:
    from app.services.deal_generator import generate_deal_parameters, format_deal_parameters
    from app.services.ai_service import get_ai_response, MASTER_PROMPT_TEMPLATE
    from app.services.agreement import validate_agreement, get_time_based_greeting
    from app.services.extraction import extract_price, extract_delivery, extract_volume
    from app.services.evaluator import NegotiationEvaluator
except ImportError:
    # Fallback for different module paths
    from services.deal_generator import generate_deal_parameters, format_deal_parameters
    from services.ai_service import get_ai_response, MASTER_PROMPT_TEMPLATE
    from services.agreement import validate_agreement, get_time_based_greeting
    from services.extraction import extract_price, extract_delivery, extract_volume
    from services.evaluator import NegotiationEvaluator

app = FastAPI(title="AI Supply Chain Negotiator API", version="1.0.0")

# Enable CORS for Amplify frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Amplify domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (replace with DynamoDB for production)
sessions_db = {}

# Pydantic models
class MessageInput(BaseModel):
    user_input: str
    session_id: str

class NewSessionInput(BaseModel):
    student_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    deal_params: dict
    greeting: str
    history: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    ai_response: str
    agreement_detected: bool
    agreed_terms: Optional[Dict] = None
    missing_terms: Optional[List[str]] = None
    state: str

class MetricScore(BaseModel):
    score: float
    grade: str
    weight: str

class PriceAnalysis(BaseModel):
    opening: float
    target: float
    reservation: float
    final: float

class DeliveryAnalysis(BaseModel):
    opening: int
    target: int
    reservation: int
    final: int

class NegotiationAnalysis(BaseModel):
    price_analysis: PriceAnalysis
    delivery_analysis: DeliveryAnalysis
    volume: Optional[int] = None

class EvaluationResponse(BaseModel):
    overall_score: float
    overall_grade: str
    metrics: Dict[str, MetricScore]
    negotiation_analysis: NegotiationAnalysis
    negotiation_rounds: int
    feedback: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Supply Chain Negotiator API", "status": "running", "version": "1.0.0"}

@app.post("/api/sessions/new", response_model=SessionResponse)
async def create_new_session(input_data: NewSessionInput) -> SessionResponse:
    """Create new negotiation session"""
    session_id = str(uuid.uuid4())
    
    # Generate deal params with optional seed
    seed = hash(input_data.student_id) % (2**32) if input_data.student_id else None
    deal_params = generate_deal_parameters(seed=seed)
    deal_parameters_str = format_deal_parameters(deal_params)
    
    # Get time-based greeting
    greeting = get_time_based_greeting()
    initial_message = f"{greeting}. Thank you for your interest in the CS-1000 microprocessor. I'm Alex from ChipSource Inc. I have our standard terms here, but I'm confident we can find an arrangement that works well for both our companies. Our standard offering is 10,000 units at our current market price with our normal delivery schedule. What specific requirements does your company have for this order?"
    
    # Store session
    sessions_db[session_id] = {
        'session_id': session_id,
        'created_at': datetime.utcnow().isoformat(),
        'deal_params': deal_params,
        'deal_parameters_str': deal_parameters_str,
        'history': [
            {
                "role": "assistant",
                "content": initial_message
            }
        ],
        'state': 'NEGOTIATING'
    }
    
    return SessionResponse(
        session_id=session_id,
        deal_params=deal_params,
        greeting=initial_message
    )

@app.post("/api/chat", response_model=ChatResponse)
async def send_message(msg: MessageInput):
    """Process user message and return AI response"""
    session_id = msg.session_id
    user_input = msg.user_input
    
    # Retrieve session
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_db[session_id]
    history = session['history']
    deal_params = session['deal_params']
    deal_parameters_str = session['deal_parameters_str']
    
    # Add user message
    history.append({"role": "user", "content": user_input})
    
    # Determine state
    agreement_keywords = ["agree", "deal", "accept", "agreed", "confirmed"]
    user_lower = user_input.lower()
    next_state = "CLOSING" if any(kw in user_lower for kw in agreement_keywords) else "NEGOTIATING"
    
    # Build conversation history for prompt
    conversation_history_str = "\n".join([
        f'{msg["role"].title()}: {msg["content"]}' for msg in history
    ])
    
    # Generate prompt
    ai_task = "Respond concisely in 2-3 sentences. Be direct and business-like. Propose trade-offs if needed."
    final_prompt = MASTER_PROMPT_TEMPLATE.format(
        deal_parameters=deal_parameters_str,
        conversation_history=conversation_history_str,
        current_state=next_state,
        user_input=user_input,
        ai_task=ai_task
    )
    
    # Generate AI response
    ai_response = get_ai_response(final_prompt)
    
    history.append({"role": "assistant", "content": ai_response})
    
    # Check for agreement
    is_valid, missing_terms, agreed_terms = validate_agreement(history)
    
    # Update session
    session['history'] = history
    session['state'] = 'CLOSING' if is_valid else next_state
    
    return ChatResponse(
        ai_response=ai_response,
        agreement_detected=is_valid,
        agreed_terms=agreed_terms if is_valid else None,
        missing_terms=missing_terms if not is_valid else None,
        state=session['state']
    )

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve session data"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions_db[session_id]

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete/close a session"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    del sessions_db[session_id]
    return {"message": "Session deleted successfully"}

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions (admin/testing)"""
    return {
        "count": len(sessions_db),
        "sessions": list(sessions_db.keys())
    }

@app.get("/api/deals/{session_id}/evaluate", response_model=EvaluationResponse)
async def evaluate_deal(session_id: str):
    """Evaluate negotiation performance"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_db[session_id]
    history = session['history']
    deal_params = session['deal_params']
    
    # Extract final agreed terms from conversation
    agreed_terms = {}
    for msg in reversed(history):
        if msg['role'] == 'assistant':
            agreed_terms['price'] = extract_price(msg['content']) or deal_params['price']['target']
            agreed_terms['delivery'] = extract_delivery(msg['content']) or deal_params['delivery']['target']
            if agreed_terms.get('price') and agreed_terms.get('delivery'):
                break
    
    # Set defaults if not extracted
    if 'price' not in agreed_terms:
        agreed_terms['price'] = deal_params['price']['target']
    if 'delivery' not in agreed_terms:
        agreed_terms['delivery'] = deal_params['delivery']['target']
    agreed_terms['volume'] = deal_params.get('volume', 10000)
    
    # Create evaluator and get evaluation
    evaluator = NegotiationEvaluator(history, deal_params, agreed_terms)
    evaluation = evaluator.evaluate()
    
    # Build response with all required fields
    metrics_response = {}
    for key, metric in evaluation['metrics'].items():
        metrics_response[key] = MetricScore(
            score=metric['score'],
            grade=metric['grade'],
            weight=metric['weight']
        )
    
    # Extract price and delivery analysis from negotiation_analysis
    analysis = evaluation['negotiation_analysis']
    price_analysis = PriceAnalysis(
        opening=analysis['price_analysis']['opening'],
        target=analysis['price_analysis']['target'],
        reservation=deal_params['price']['reservation'],
        final=analysis['price_analysis']['final']
    )
    
    delivery_analysis = DeliveryAnalysis(
        opening=analysis['delivery_analysis']['opening'],
        target=analysis['delivery_analysis']['target'],
        reservation=deal_params['delivery']['reservation'],
        final=analysis['delivery_analysis']['final']
    )
    
    return EvaluationResponse(
        overall_score=evaluation['overall_score'],
        overall_grade=evaluation['overall_grade'],
        metrics=metrics_response,
        negotiation_analysis=NegotiationAnalysis(
            price_analysis=price_analysis,
            delivery_analysis=delivery_analysis,
            volume=analysis.get('volume', agreed_terms.get('volume'))
        ),
        negotiation_rounds=analysis['rounds'],
        feedback=evaluation['feedback']
    )

@app.get("/api/deals")
async def list_completed_deals():
    """List all completed deals (admin/testing)"""
    completed = [sid for sid, s in sessions_db.items() if s['state'] == 'CLOSING']
    return {
        "count": len(completed),
        "completed_deals": completed
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "AI Supply Chain Negotiator API", "status": "ok", "version": "1.0.0"}

@app.get("/")
async def root():
    """Root endpoint redirects to health check"""
    return {"message": "AI Supply Chain Negotiator API", "status": "ok", "version": "1.0.0"}

# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler for deployment"""
    try:
        from mangum import Mangum
        handler = Mangum(app)
        return handler(event, context)
    except ImportError:
        return {"statusCode": 500, "body": "Mangum not installed"}
