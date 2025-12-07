import os
import re
import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_time_based_greeting():
    """Returns appropriate greeting based on current UTC time."""
    current_hour = datetime.datetime.utcnow().hour
    
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def extract_price(text):
    """Extract price value from text using regex."""
    if not text:
        return None
    match = re.search(r'\$\s*([0-9][0-9,]*(?:\.\d+)?)', text)
    if match:
        num_str = match.group(1).replace(',', '').strip()
        try:
            return float(num_str)
        except ValueError:
            return None
    return None

def extract_delivery(text):
    """Extract delivery days from text using regex."""
    if not text:
        return None
    match = re.search(r'(\d+)\s*days?', text.lower())
    if match:
        return int(match.group(1))
    return None

def extract_volume(text):
    """Extract volume/quantity from text using regex."""
    if not text:
        return None
    txt = text.lower()
    
    # Handle "15 thousand" or "15k"
    m_thousand = re.search(r'(\d{1,3}(?:,\d{3})*|\d+\.?\d*)\s*(thousand|k)\b', txt)
    if m_thousand:
        num_str = m_thousand.group(1).replace(',', '')
        try:
            return int(float(num_str) * 1000)
        except ValueError:
            return None
    
    # Handle explicit "15,000 units" or "15000 units"
    m_units = re.search(r'(\d{1,3}(?:,\d{3})*|\d+\.?\d*)\s*(?:units?)\b', txt)
    if m_units:
        num_str = m_units.group(1).replace(',', '')
        try:
            return int(float(num_str))
        except ValueError:
            return None
    
    # Fallback: standalone number with context
    if any(keyword in txt for keyword in ['units', 'order', 'volume', 'quantity']):
        m_num = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)', txt)
        if m_num:
            num_str = m_num.group(1).replace(',', '')
            try:
                return int(float(num_str))
            except ValueError:
                return None
    return None

def validate_agreement(conversation_history):
    """Validate and extract agreement terms from conversation."""
    agreed_terms = {"price": None, "delivery": None, "volume": None}
    agreement_keywords = [
        "agree", "agreed", "deal", "accept", "acceptable", "works for me", 
        "sounds good", "confirmed", "yes", "okay that works", "perfect",
        "deal", "let's do it", "that works", "i accept"
    ]

    # Iterate backwards to find the most recent user agreement
    for i in range(len(conversation_history) - 1, 0, -1):
        current_msg = conversation_history[i]
        prev_msg = conversation_history[i-1]

        if current_msg.get("role") == "user":
            user_content = current_msg["content"].lower()
            if any(keyword in user_content for keyword in agreement_keywords):
                # Check for explicit numeric terms in user's confirmation
                user_price = extract_price(current_msg.get("content", ""))
                user_delivery = extract_delivery(current_msg.get("content", ""))
                user_volume = extract_volume(current_msg.get("content", ""))
                
                if sum(1 for x in (user_price, user_delivery, user_volume) if x is not None) >= 2:
                    agreed_terms.update({"price": user_price, "delivery": user_delivery, "volume": user_volume})
                else:
                    # Use previous assistant message if it contains a proposal
                    if prev_msg.get("role") == "assistant":
                        price = extract_price(prev_msg.get("content", ""))
                        delivery = extract_delivery(prev_msg.get("content", ""))
                        volume = extract_volume(prev_msg.get("content", ""))
                        if sum(1 for x in (price, delivery, volume) if x is not None) >= 2:
                            agreed_terms.update({"price": price, "delivery": delivery, "volume": volume})

                missing_terms = [k for k, v in agreed_terms.items() if v is None]
                is_valid = len(missing_terms) == 0
                return is_valid, missing_terms, agreed_terms

    return False, ["price", "delivery", "volume"], agreed_terms
