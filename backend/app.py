from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import random
import uuid
from datetime import datetime, timezone
from mangum import Mangum

app = FastAPI(title="AI Supply Chain Negotiator")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with DynamoDB for production)
sessions_db = {}


class SessionCreate(BaseModel):
    student_id: str


class ChatMessage(BaseModel):
    session_id: str
    message: str


class DealParameters:
    """Seedable deal parameters based on student ID"""
    
    def __init__(self, student_id: str):
        # Use student_id as seed for reproducibility
        seed = sum(ord(c) for c in student_id)
        random.seed(seed)
        
        self.base_price = random.randint(50, 100)  # $ per unit
        self.min_price = int(self.base_price * 0.7)  # Seller's bottom line
        self.target_quantity = random.randint(500, 2000)  # units
        self.min_quantity = int(self.target_quantity * 0.5)
        self.delivery_days = random.randint(30, 90)
        self.min_delivery = int(self.delivery_days * 0.6)
        self.quality_grade = random.choice(['A', 'B', 'C'])
        self.warranty_months = random.randint(6, 24)
        
        # Reset random to avoid affecting other randomness
        random.seed()


class NegotiationSession:
    """Represents a negotiation session with AI seller Alex"""
    
    def __init__(self, session_id: str, student_id: str):
        self.session_id = session_id
        self.student_id = student_id
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.deal_params = DealParameters(student_id)
        self.messages = []
        self.turn_count = 0
        self.status = "active"  # active, completed, failed
        self.current_offer = None
        self.deal_closed = False
        
        # AI seller's current position
        self.alex_price = self.deal_params.base_price
        self.alex_quantity = self.deal_params.target_quantity
        self.alex_delivery = self.deal_params.delivery_days
        
        # Negotiation state
        self.concession_count = 0
        self.max_concessions = 5
        
        # Add initial greeting from Alex
        self._add_alex_message(
            f"Hello! I'm Alex, your AI seller for high-quality microprocessors. "
            f"I have premium grade {self.deal_params.quality_grade} chips available. "
            f"My opening offer is ${self.alex_price} per unit for {self.alex_quantity} units, "
            f"with delivery in {self.alex_delivery} days and {self.deal_params.warranty_months} months warranty. "
            f"What are you looking for?"
        )
    
    def _add_alex_message(self, content: str):
        """Add a message from Alex to the conversation"""
        self.messages.append({
            "role": "alex",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def _add_user_message(self, content: str):
        """Add a user message to the conversation"""
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def process_message(self, user_message: str) -> str:
        """Process user message and generate Alex's response"""
        self._add_user_message(user_message)
        self.turn_count += 1
        
        # Parse user message for offers or questions
        message_lower = user_message.lower()
        
        # Check for deal acceptance
        if any(word in message_lower for word in ["accept", "deal", "agreed", "yes, let's do it"]):
            if self.current_offer:
                return self._close_deal()
            else:
                response = "Great! But I need to know what specific terms you're accepting. Could you clarify the price, quantity, and delivery terms?"
                self._add_alex_message(response)
                return response
        
        # Check for rejection or walkaway
        if any(word in message_lower for word in ["no deal", "walk away", "never mind", "forget it"]):
            self.status = "failed"
            response = "I understand. Perhaps we can do business another time. Good luck with your procurement!"
            self._add_alex_message(response)
            return response
        
        # Extract numbers from message (simple parsing)
        numbers = [int(s) for s in user_message.split() if s.isdigit()]
        
        # Determine negotiation response
        response = self._generate_negotiation_response(message_lower, numbers)
        self._add_alex_message(response)
        
        return response
    
    def _generate_negotiation_response(self, message_lower: str, numbers: List[int]) -> str:
        """Generate Alex's negotiation response with realistic tactics"""
        
        # Tactic 1: Anchoring - resist large changes
        if "price" in message_lower or "$" in message_lower:
            if numbers:
                proposed_price = numbers[0]
                if proposed_price < self.deal_params.min_price:
                    return (f"I appreciate your interest, but ${proposed_price} is below my cost. "
                           f"The best I can do is ${self.alex_price}. These are high-quality grade "
                           f"{self.deal_params.quality_grade} chips with {self.deal_params.warranty_months} months warranty.")
                elif proposed_price < self.alex_price and self.concession_count < self.max_concessions:
                    # Make a counter-offer (small concession)
                    concession = min(5, (self.alex_price - proposed_price) // 3)
                    self.alex_price -= concession
                    self.concession_count += 1
                    return (f"I can see you're serious about this deal. I can come down to ${self.alex_price} per unit, "
                           f"but that's really pushing my margins. Can you meet me there?")
                else:
                    self.current_offer = {
                        "price": self.alex_price,
                        "quantity": self.alex_quantity,
                        "delivery": self.alex_delivery
                    }
                    return (f"${proposed_price} works for me! So we're agreed on ${proposed_price} per unit "
                           f"for {self.alex_quantity} units, delivery in {self.alex_delivery} days?")
        
        # Tactic 2: Bundle and trade-off
        if "quantity" in message_lower or "units" in message_lower:
            if numbers:
                proposed_qty = max(numbers)
                if proposed_qty >= self.deal_params.min_quantity:
                    if proposed_qty > self.alex_quantity:
                        # Offer volume discount
                        discount = 2 if proposed_qty > self.alex_quantity * 1.5 else 1
                        self.alex_price = max(self.deal_params.min_price, self.alex_price - discount)
                        self.alex_quantity = proposed_qty
                        return (f"For {proposed_qty} units, I can offer a volume discount. "
                               f"How about ${self.alex_price} per unit?")
                    else:
                        self.alex_quantity = proposed_qty
                        return f"I can do {proposed_qty} units at ${self.alex_price} per unit."
                else:
                    return f"I need to move at least {self.deal_params.min_quantity} units to make this worthwhile."
        
        # Tactic 3: Time pressure
        if "delivery" in message_lower or "days" in message_lower or "time" in message_lower:
            if numbers:
                proposed_delivery = numbers[0]
                if proposed_delivery < self.deal_params.min_delivery:
                    return (f"Rush delivery in {proposed_delivery} days would require express shipping. "
                           f"I'd need to charge ${self.alex_price + 5} per unit to cover those costs.")
                else:
                    self.alex_delivery = proposed_delivery
                    return f"I can accommodate {proposed_delivery} days delivery at our current price of ${self.alex_price}."
        
        # Tactic 4: Information gathering
        if "?" in message_lower:
            if "warranty" in message_lower:
                return f"All chips come with a {self.deal_params.warranty_months} month warranty covering manufacturing defects."
            elif "quality" in message_lower or "grade" in message_lower:
                return f"These are grade {self.deal_params.quality_grade} microprocessors, tested to industry standards."
            elif "stock" in message_lower or "available" in message_lower:
                return f"I have up to {self.deal_params.target_quantity * 2} units in stock currently."
            else:
                return "What specific information do you need? I can tell you about pricing, quantity, delivery, warranty, or quality."
        
        # Default: Encouraging response
        responses = [
            f"I'm at ${self.alex_price} per unit for {self.alex_quantity} units. What price works for your budget?",
            "Tell me more about your needs. What's your target price and quantity?",
            "I want to make this work. What aspects of the deal are most important to you?",
            f"My current offer stands at ${self.alex_price} per unit. Can you work with that?",
        ]
        return random.choice(responses)
    
    def _close_deal(self) -> str:
        """Close the deal and evaluate the negotiation"""
        self.deal_closed = True
        self.status = "completed"
        
        final_price = self.alex_price
        final_quantity = self.alex_quantity
        final_delivery = self.alex_delivery
        
        response = (f"Excellent! We have a deal: {final_quantity} units at ${final_price} per unit, "
                   f"delivery in {final_delivery} days. I'll send over the contract. "
                   f"Pleasure doing business with you!")
        
        return response
    
    def evaluate(self) -> Dict:
        """Evaluate negotiation performance on 5 metrics"""
        if not self.deal_closed:
            return {
                "deal_completed": False,
                "message": "Negotiation not completed yet"
            }
        
        # Metric 1: Price Achievement (0-100)
        price_saved = self.deal_params.base_price - self.alex_price
        max_possible_savings = self.deal_params.base_price - self.deal_params.min_price
        price_score = int((price_saved / max_possible_savings) * 100) if max_possible_savings > 0 else 0
        price_score = max(0, min(100, price_score))
        
        # Metric 2: Efficiency (turns taken)
        efficiency_score = max(0, 100 - (self.turn_count * 10))
        
        # Metric 3: Relationship Building (based on message tone - simplified)
        relationship_score = 70  # Base score
        polite_words = ["please", "thank", "appreciate"]
        for msg in self.messages:
            if msg["role"] == "user":
                msg_lower = msg["content"].lower()
                if any(word in msg_lower for word in polite_words):
                    relationship_score = min(100, relationship_score + 5)
        
        # Metric 4: Value Creation (quantity secured vs target)
        quantity_ratio = self.alex_quantity / self.deal_params.target_quantity
        value_score = int(quantity_ratio * 100)
        value_score = max(0, min(100, value_score))
        
        # Metric 5: Strategic Concessions (how well they negotiated)
        # Lower concession by Alex = better negotiation
        strategic_score = max(0, 100 - (self.concession_count * 15))
        
        overall_score = (price_score + efficiency_score + relationship_score + value_score + strategic_score) / 5
        
        return {
            "deal_completed": True,
            "overall_score": round(overall_score, 1),
            "metrics": {
                "price_achievement": price_score,
                "efficiency": efficiency_score,
                "relationship_building": relationship_score,
                "value_creation": value_score,
                "strategic_negotiation": strategic_score
            },
            "deal_details": {
                "final_price": self.alex_price,
                "base_price": self.deal_params.base_price,
                "quantity": self.alex_quantity,
                "delivery_days": self.alex_delivery,
                "turns_taken": self.turn_count
            }
        }
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for API response"""
        return {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "created_at": self.created_at,
            "status": self.status,
            "messages": self.messages,
            "turn_count": self.turn_count,
            "deal_closed": self.deal_closed,
            "current_state": {
                "price": self.alex_price,
                "quantity": self.alex_quantity,
                "delivery": self.alex_delivery
            },
            "evaluation": self.evaluate() if self.deal_closed else None
        }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Supply Chain Negotiator API", "status": "running"}


@app.post("/api/sessions/new")
async def create_session(session_data: SessionCreate):
    """Create a new negotiation session"""
    session_id = str(uuid.uuid4())
    session = NegotiationSession(session_id, session_data.student_id)
    sessions_db[session_id] = session
    
    return {
        "session_id": session_id,
        "student_id": session_data.student_id,
        "initial_message": session.messages[0],
        "deal_parameters": {
            "base_price": session.deal_params.base_price,
            "target_quantity": session.deal_params.target_quantity,
            "delivery_days": session.deal_params.delivery_days,
            "quality_grade": session.deal_params.quality_grade,
            "warranty_months": session.deal_params.warranty_months
        }
    }


@app.post("/api/chat")
async def send_message(chat_message: ChatMessage):
    """Send a message in a negotiation session"""
    session = sessions_db.get(chat_message.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "active" and not session.deal_closed:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    response = session.process_message(chat_message.message)
    
    return {
        "session_id": session.session_id,
        "alex_response": response,
        "status": session.status,
        "turn_count": session.turn_count,
        "deal_closed": session.deal_closed,
        "evaluation": session.evaluate() if session.deal_closed else None
    }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    session = sessions_db.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.to_dict()


# AWS Lambda handler
handler = Mangum(app)
