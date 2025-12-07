import os
import re
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import random
import html
import unicodedata
import textwrap
import datetime  # Added for time-based greeting

def get_time_based_greeting():
    """
    Returns appropriate greeting based on current UTC time.
    Morning: 5:00 AM - 11:59 AM
    Afternoon: 12:00 PM - 5:59 PM  
    Evening: 6:00 PM - 4:59 AM
    """
    current_hour = datetime.datetime.utcnow().hour
    
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def generate_deal_parameters(seed=None):
    """
    Generates unique deal parameters for each student with meaningful negotiation ranges.
    Implements 15-25% reduction steps to enable dynamic and engaging negotiations.
    """
    if seed is not None:
        random.seed(seed)
    
    # Configuration constants for negotiation ranges
    MIN_PRICE_DIFF = 5       # Minimum dollar difference between price levels
    MIN_DELIVERY_DIFF = 3    # Minimum day difference between delivery levels
    RESERVATION_FLOOR = 0.50 # Reservation cannot go below 50% of opening price
    
    # Base price generation with wider ranges for meaningful negotiation
    opening_price = round(random.uniform(5, 30) * 10, 2)
    
    # Price reductions: 15-25% per step for meaningful negotiation space
    price_reduction_1 = random.uniform(0.15, 0.25)  # 15-25% reduction for target
    price_reduction_2 = random.uniform(0.10, 0.15)  # Additional 10-15% reduction for reservation
    
    target_price = round(opening_price * (1 - price_reduction_1), 2)
    reservation_price = round(target_price * (1 - price_reduction_2), 2)

    # Ensure minimum price difference between levels for meaningful concessions
    if target_price >= opening_price - MIN_PRICE_DIFF:
        target_price = round(opening_price - max(MIN_PRICE_DIFF, opening_price * 0.15), 2)
    if reservation_price >= target_price - MIN_PRICE_DIFF:
        reservation_price = round(target_price - max(MIN_PRICE_DIFF, target_price * 0.10), 2)
    
    # Ensure reservation doesn't go below floor percentage of opening (prevents unrealistic deals)
    min_reservation = round(opening_price * RESERVATION_FLOOR, 2)
    reservation_price = max(reservation_price, min_reservation)

    # Delivery generation with meaningful reductions
    opening_delivery = int(round(random.uniform(4, 10) * 10))
    
    # Delivery reductions: 15-25% per step for meaningful negotiation
    delivery_reduction_1 = random.uniform(0.15, 0.25)  # 15-25% reduction for target
    delivery_reduction_2 = random.uniform(0.10, 0.15)  # Additional 10-15% reduction for reservation
    
    target_delivery = int(round(opening_delivery * (1 - delivery_reduction_1)))
    reservation_delivery = int(round(target_delivery * (1 - delivery_reduction_2)))

    # Ensure minimum delivery day difference between levels for meaningful concessions
    if target_delivery >= opening_delivery - MIN_DELIVERY_DIFF:
        target_delivery = max(5, opening_delivery - max(MIN_DELIVERY_DIFF, int(opening_delivery * 0.15)))
    if reservation_delivery >= target_delivery - MIN_DELIVERY_DIFF:
        reservation_delivery = max(3, target_delivery - max(MIN_DELIVERY_DIFF, int(target_delivery * 0.10)))

    return {
        "price": {
            "opening": opening_price,
            "target": target_price,
            "reservation": reservation_price
        },
        "delivery": {
            "opening": opening_delivery,
            "target": target_delivery,
            "reservation": reservation_delivery
        }
    }

def format_deal_parameters(params):
    """Formats parameters into the prompt template with negotiation strategy."""
    return f"""
--- Our Company: 'ChipSource Inc.' ---
--- Product: CS-1000 Microprocessor ---

--- NEGOTIATION VARIABLES & GOALS ---

1.  **Price Per Unit:**
    * Opening Offer: ${params['price']['opening']}
    * Our Target: ${params['price']['target']} (This is a great outcome for us)
    * Our Reservation Point: ${params['price']['reservation']} (Our absolute walk-away price. Do not go below this.)

2.  **Delivery Date (days from order):**
    * Opening Offer: {params['delivery']['opening']} days (This is comfortable for us)
    * Our Target: {params['delivery']['target']} days
    * Our Reservation Point: {params['delivery']['reservation']} days (This is an expedited rush order, our absolute fastest)

3.  **Volume & Discount Tiers:**
    * Standard orders are for 10,000 units. The prices above apply.
    * Tier 1 Discount: For orders > 20,000 units, a 5% discount on the final per-unit price is possible.
    * Tier 2 Discount: For orders > 50,000 units, an 8% discount on the final per-unit price is possible.

--- NEGOTIATION STRATEGY ---
* Start with your opening offer, but be prepared to make meaningful concessions.
* When the buyer pushes back or makes a counteroffer, reduce your price by $5-15 or delivery by 3-7 days per round.
* Make gradual concessions - don't jump straight to your reservation point.
* Suggest trade-offs: offer better price for higher volume, or faster delivery for higher price.
* If the buyer shows strong interest or urgency, you can move closer to your target.
* Never go below your reservation point, but approach it gradually if needed.
* Be responsive to counteroffers - match concession energy (if they give, you give).

--- YOUR GOAL ---
Your primary objective is to reach a deal that is as close to your TARGETS as possible. A deal is better than no deal, but not if it breaches any of your RESERVATION points.
"""

# --- B2B MASTER PROMPT TEMPLATE ---
MASTER_PROMPT_TEMPLATE = """
You are Alex, a professional Supply Chain Manager for 'ChipSource Inc.'.
Be direct, efficient, and business-like. Keep responses brief.

---
DEAL PARAMETERS:
{deal_parameters}
---
NEGOTIATION BEHAVIOR RULES:
1. Be concise: Limit responses to 2-3 sentences maximum.
2. Be professional: Maintain a business-like tone.
3. Make meaningful concessions: When the buyer pushes back, reduce your offer by $5-15 on price or 3-7 days on delivery.
4. Never make trivial $1-2 reductions - concessions should feel significant to encourage continued negotiation.
5. Seek trade-offs: Propose compromises (e.g., "I can lower the price if you increase volume").
6. Respond to buyer pressure: If they express urgency or strong interest, consider moving toward your target.
7. Gradual approach: Move from opening toward reservation in 2-4 steps, not immediately.
8. Never reveal your Target or Reservation points explicitly.
9. Use plain text only, no markdown formatting.
10. When confirming a deal, state all terms clearly: "Confirmed: Price $X, Delivery Y days, Volume Z units."
---
CONVERSATION HISTORY:
{conversation_history}
---
TASK:
State: '{current_state}'
User said: "{user_input}"
Instruction: {ai_task}
Respond as Alex (2-3 sentences max). Make a meaningful counteroffer or concession if appropriate:
"""

def extract_price(text):
    """Extract price value from text using regex. Handles various formats and edge cases."""
    if not text:
        return None
    # Enhanced regex for better price matching
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
    """Extract volume/quantity from text using regex. Handles various formats."""
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

def clean_ai_response(text):
    """Optimized AI response cleaning with duplicate detection."""
    if not isinstance(text, str):
        return text
    
    # Check for duplicated content (common AI generation issue)
    paragraphs = text.split('\n\n')
    if len(paragraphs) > 1 and len(paragraphs) % 2 == 0:
        mid = len(paragraphs) // 2
        first_half = paragraphs[:mid]
        second_half = paragraphs[mid:]
        if first_half == second_half:
            return '\n\n'.join(first_half)
        
    return text

def enforce_concise_response(text, max_sentences=3):
    """
    Ensures response meets length requirements by truncating to max_sentences.
    Preserves complete sentences and key negotiation terms.
    Handles abbreviations and decimal numbers to avoid incorrect splits.
    """
    if not isinstance(text, str) or not text.strip():
        return text
    
    # Common abbreviations that should not trigger sentence splits (business context)
    abbreviations = [
        'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Inc.', 'Ltd.', 'Corp.', 'Co.', 'LLC',
        'etc.', 'e.g.', 'i.e.', 'vs.', 'dept.', 'approx.', 'qty.', 'no.'
    ]
    
    # Temporarily replace abbreviations to protect them from sentence splitting
    protected_text = text.strip()
    placeholder_map = {}
    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR{i}__"
        if abbr in protected_text:
            placeholder_map[placeholder] = abbr
            protected_text = protected_text.replace(abbr, placeholder)
    
    # Also protect decimal numbers like $15.50, \$15.50 or 3.14
    decimal_pattern = r'((?:\$|\\\$)?\d+\.\d+)'
    decimal_matches = re.findall(decimal_pattern, protected_text)
    for i, match in enumerate(decimal_matches):
        placeholder = f"__DEC{i}__"
        if placeholder not in placeholder_map:
            placeholder_map[placeholder] = match
            protected_text = protected_text.replace(match, placeholder, 1)
    
    # Split into sentences using common sentence endings followed by whitespace
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, protected_text)
    
    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text
    
    # Take the first max_sentences
    truncated = ' '.join(sentences[:max_sentences])
    
    # Restore protected text
    for placeholder, original in placeholder_map.items():
        truncated = truncated.replace(placeholder, original)
    
    # Ensure the response ends with proper punctuation
    if truncated and truncated[-1] not in '.!?':
        truncated += '.'
    
    return truncated

def _find_nearest_proposal_before(history, idx):
    """Optimized search for assistant proposals with caching."""
    for j in range(idx-1, -1, -1):
        msg = history[j]
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        
        # Cache extraction results to avoid repeated regex operations
        if not hasattr(msg, '_cached_extracts'):
            msg['_cached_extracts'] = {
                'price': extract_price(content),
                'delivery': extract_delivery(content),
                'volume': extract_volume(content)
            }
        
        extracts = msg['_cached_extracts']
        if sum(1 for x in extracts.values() if x is not None) >= 2:
            return {**extracts, "index": j}
    return None

def validate_agreement(conversation_history):
    """
    Enhanced agreement validation with better keyword detection and caching.
    Returns (is_valid, missing_terms, agreed_terms)
    """
    agreed_terms = {"price": None, "delivery": None, "volume": None}
    # Expanded agreement keywords for better detection
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
                    
                    # Fallback: find nearest earlier assistant proposal
                    if all(v is None for v in agreed_terms.values()):
                        proposal = _find_nearest_proposal_before(conversation_history, i)
                        if proposal:
                            agreed_terms.update({
                                "price": proposal["price"], 
                                "delivery": proposal["delivery"], 
                                "volume": proposal["volume"]
                            })

                missing_terms = [k for k, v in agreed_terms.items() if v is None]
                is_valid = len(missing_terms) == 0
                return is_valid, missing_terms, agreed_terms

    return False, ["price", "delivery", "volume"], agreed_terms

def get_ai_response(prompt):
    """Enhanced AI response generation with conciseness enforcement."""
    try:
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("Google API key not found. Please check your .env file.")
            return "I'm sorry, but I'm unable to connect to the AI service at the moment."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            return "I apologize, but I didn't receive a proper response. Could you please try again?"
        
        cleaned_response = clean_ai_response(response.text)
        # Enforce concise responses (2-3 sentences max)
        concise_response = enforce_concise_response(cleaned_response, max_sentences=3)
        return concise_response
    except Exception as e:
        st.error(f"Error getting AI response: {e}")
        return "I'm sorry, I seem to be having trouble processing that request. Could you try again?"

def wrap_text(text, width=80):
    """Optimized text wrapping with newline preservation."""
    if not isinstance(text, str):
        return text
    
    # Preserve intentional paragraph breaks
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = []
    
    for paragraph in paragraphs:
        # Replace single newlines with spaces, then wrap
        paragraph = paragraph.replace('\n', ' ')
        wrapped = textwrap.fill(paragraph, width=width)
        wrapped_paragraphs.append(wrapped)
    
    return '\n\n'.join(wrapped_paragraphs)

def sanitize_text_for_display(text):
    """Enhanced text sanitization with better Unicode handling and LaTeX escape."""
    if not isinstance(text, str):
        return text
    
    # Remove invisible/control characters
    invisible_chars = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0']
    for ch in invisible_chars:
        text = text.replace(ch, '')
    
    # Normalize Unicode
    text = unicodedata.normalize('NFC', text)
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Escape dollar signs to prevent LaTeX rendering in Streamlit
    text = text.replace('$', r'\$')
    
    # Normalize whitespace while preserving structure
    text = re.sub(r'[ \t]+', ' ', text)  # Collapse spaces/tabs
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
    text = '\n'.join(line.rstrip() for line in text.split('\n'))  # Trim line endings
    
    return text.strip()

def determine_next_state(current_state, user_input):
    """Enhanced state determination with better keyword detection."""
    agreement_keywords = [
        "agree", "deal", "accept", "agreed", "confirmed", "works for me", 
        "sounds good", "perfect", "let's do it", "that works", "i accept"
    ]
    
    user_lower = user_input.lower()
    if any(keyword in user_lower for keyword in agreement_keywords):
        return "CLOSING"
    else:
        return "NEGOTIATING"

def evaluate_deal(conversation_history, deal_params, final_agreement=None):
    """
    Enhanced deal evaluation with better parameter analysis.
    Accounts for the new 2-5% reduction constraints in scoring.
    """
    # Use persisted agreement or parse from history
    if final_agreement and isinstance(final_agreement, dict):
        final_price = final_agreement.get('price', 'N/A')
        final_delivery = final_agreement.get('delivery', 'N/A')
        final_volume = final_agreement.get('volume', 'N/A')
    else:
        _is_valid, _missing, agreed_terms = validate_agreement(conversation_history)
        final_price = agreed_terms.get('price', 'N/A')
        final_delivery = agreed_terms.get('delivery', 'N/A')
        final_volume = agreed_terms.get('volume', 'N/A')

    evaluation_prompt = f"""
You are an expert negotiation coach and evaluator. Analyze the following B2B negotiation and provide a comprehensive evaluation.

--- SELLER'S (AI's) SECRET PARAMETERS ---
(The AI uses 15-25% reductions between price/delivery levels to enable dynamic negotiation with meaningful concessions)
Price Opening: ${deal_params['price']['opening']}
Price Target (AI's Ideal): ${deal_params['price']['target']}
Price Reservation (AI's Walk-away): ${deal_params['price']['reservation']}

Delivery Opening: {deal_params['delivery']['opening']} days
Delivery Target (AI's Ideal): {deal_params['delivery']['target']} days
Delivery Reservation (AI's Fastest): {deal_params['delivery']['reservation']} days

--- NEGOTIATION CONVERSATION ---
{chr(10).join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])}

--- ACADEMIC EVALUATION RUBRIC (Evaluate the USER) ---
Please evaluate the **USER'S** performance on the following criteria. The AI's parameters use 15-25% reductions to enable meaningful negotiation space.

**1. Deal Quality & Outcome (Weight: 33%)**
* **Excellent (A: 90-100):** Achieved a deal at or very close to the AI's reservation points for both price and delivery.
* **Proficient (B: 80-89):** Achieved a strong deal, significantly better than the AI's opening offers but not quite at reservation limits.
* **Developing (C: 70-79):** Reached an agreement, but the deal is only slightly better than the AI's opening offers.
* **Needs Improvement (D/F: 0-69):** Failed to reach an agreement, or accepted a deal at or worse than the AI's opening offers.

**2. Trade-off Strategy & Analytical Reasoning (Weight: 28%)**
* **Excellent (A: 90-100):** User demonstrates strong analytical reasoning and actively proposes logical, win-win trade-offs.
* **Proficient (B: 80-89):** User identifies at least one meaningful trade-off with sound reasoning.
* **Developing (C: 70-79):** User shows limited recognition of trade-offs; tends to focus on single variables.
* **Needs Improvement (D/F: 0-69):** User made no attempt to use trade-offs; offers were inconsistent or illogical.

**3. Professionalism & Communication (Weight: 17%)**
* **Excellent (A: 90-100):** User maintains professional tone, justifies positions with business logic, shows strong persuasion skills.
* **Proficient (B: 80-89):** User is mostly professional and clear with minor lapses.
* **Developing (C: 70-79):** User has some professional tone but lacks clarity in justifications.
* **Needs Improvement (D/F: 0-69):** User used unprofessional, argumentative, or overly casual tone.

**4. Negotiation Process Management (Weight: 11%)**
* **Excellent (A: 90-100):** User efficiently manages negotiation flow, summarizes progress, confirms offers clearly.
* **Proficient (B: 80-89):** User is mostly structured with minor flow issues.
* **Developing (C: 70-79):** User's conversation flow is disorganized or purely reactive.
* **Needs Improvement (D/F: 0-69):** User's process is chaotic or incomplete.

**5. Creativity & Adaptability (Weight: 11%)**
* **Excellent (A: 90-100):** User employs innovative solutions and adapts effectively to counteroffers.
* **Proficient (B: 80-89):** User shows some creativity or adaptation.
* **Developing (C: 70-79):** User shows limited adaptation, mostly repeats offers.
* **Needs Improvement (D/F: 0-69):** User made no attempt to adjust strategy or be creative.

--- OUTPUT FORMAT ---
**FINAL EVALUATION REPORT**

**Final Deal Achieved:**
* **Price:** ${final_price}
* **Delivery:** {final_delivery} days
* **Volume:** {final_volume} units

**Metrics Scores:**
* Deal Quality: [score]/100 (Weight: 33%)
* Trade-off Strategy: [score]/100 (Weight: 28%)
* Professionalism: [score]/100 (Weight: 17%)
* Process Management: [score]/100 (Weight: 11%)
* Creativity & Adaptability: [score]/100 (Weight: 11%)

**Overall Weighted Score: [calculated_score]/100**

**Key Strengths:**
* [Specific strength based on high-scoring categories]
* [Additional strength]

**Areas for Improvement:**
* [Specific area based on low-scoring categories]
* [Additional area]

**Feedback & Recommendations:**
[2-3 paragraphs of constructive, specific feedback about how the user engaged with the AI's dynamic concession patterns and negotiation flexibility.]
"""
    
    try:
        load_dotenv()
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(evaluation_prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating evaluation: {e}")
        return "Unable to generate evaluation at this time."

# --- STREAMLIT WEB APP INTERFACE ---
st.title("AI Supply Chain Negotiator: Alex")
st.write("Negotiate a bulk order of microprocessors for your company.")

with st.sidebar:
    st.header("Deal Configuration")
    
    # New Chat button at the top of sidebar
    if st.button("🔄 New Chat", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Enhanced configuration options
    seed_option = st.radio("Deal Parameters:", ("Random", "Use Student ID"))
    
    if seed_option == "Use Student ID":
        student_id = st.text_input("Enter your Student ID:", "")
        if student_id:
            seed = hash(student_id) % (2**32)
        else:
            seed = None
    else:
        seed = None
    
    st.markdown("---")
    st.header("Deal Overview")
    st.markdown("Negotiate the **Price**, **Delivery Date**, and **Volume** for the CS-1000 Microprocessor.")
    st.markdown("*Parameters use 15-25% reduction ranges for dynamic, engaging negotiations.*")

# Initialize session state with enhanced error handling
if 'deal_params' not in st.session_state:
    try:
        st.session_state.deal_params = generate_deal_parameters(
            seed=seed if seed_option == "Use Student ID" and 'student_id' in locals() and student_id else None
        )
        st.session_state.deal_parameters_str = format_deal_parameters(st.session_state.deal_params)
    except Exception as e:
        st.error(f"Error generating deal parameters: {e}")
        st.session_state.deal_params = generate_deal_parameters()  # Fallback
        st.session_state.deal_parameters_str = format_deal_parameters(st.session_state.deal_params)

if 'history' not in st.session_state:
    # Dynamic greeting based on current time
    greeting = get_time_based_greeting()
    st.session_state.history = [
        {"role": "assistant", "content": f"{greeting}. Thank you for your interest in the CS-1000 microprocessor. I'm Alex from ChipSource Inc. I have our standard terms here, but I'm confident we can find an arrangement that works well for both our companies. Our standard offering is 10,000 units at our current market price with our normal delivery schedule. What specific requirements does your company have for this order?"}
    ]

if 'state' not in st.session_state:
    st.session_state.state = "NEGOTIATING"

if 'deal_closed' not in st.session_state:
    st.session_state.deal_closed = False

if 'evaluation_shown' not in st.session_state:
    st.session_state.evaluation_shown = False

if 'pending_confirmation' not in st.session_state:
    st.session_state.pending_confirmation = None

if 'pending_agreement' not in st.session_state:
    st.session_state.pending_agreement = None

# Display conversation history with enhanced formatting
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            sanitized_content = sanitize_text_for_display(message["content"])
            wrapped_content = wrap_text(sanitized_content)
            st.markdown(wrapped_content)
        else:
            st.markdown(message["content"])

# Enhanced confirmation UI
if st.session_state.pending_confirmation and not st.session_state.deal_closed:
    agreed = st.session_state.pending_confirmation
    st.divider()
    st.subheader("🤝 Proposed Deal - Confirmation Required")
    
    # Enhanced deal display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Price per Unit", f"${agreed.get('price','?')}")
    with col2:
        st.metric("Delivery Time", f"{agreed.get('delivery','?')} days")
    with col3:
        st.metric("Volume", f"{agreed.get('volume','?'):,} units" if agreed.get('volume') else "? units")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Confirm Agreement", type="primary"):
            st.session_state.final_agreement = agreed.copy() if isinstance(agreed, dict) else agreed
            st.session_state.deal_closed = True
            st.session_state.pending_confirmation = None
            st.rerun()
    with col2:
        if st.button("↩️ Continue Negotiating"):
            st.session_state.pending_confirmation = None
            st.session_state.deal_closed = False
            st.session_state.state = "NEGOTIATING"
            st.rerun()

# Enhanced evaluation display
if st.session_state.deal_closed and not st.session_state.evaluation_shown:
    if 'final_agreement' in st.session_state and st.session_state.final_agreement:
        agreed_terms = st.session_state.final_agreement
        missing_terms = [k for k, v in agreed_terms.items() if v is None]
        is_valid = len(missing_terms) == 0
    else:
        is_valid, missing_terms, agreed_terms = validate_agreement(st.session_state.history)

    if not is_valid:
        st.warning(f"⚠️ **Incomplete Agreement** - Missing consensus on: {', '.join(missing_terms).title()}")
        st.info(f"Agreed terms so far: Price: ${agreed_terms.get('price', '?')} | Delivery: {agreed_terms.get('delivery', '?')} days | Volume: {agreed_terms.get('volume', '?')} units")
        st.markdown("Please continue negotiating to reach explicit agreement on all three terms before evaluation.")
        st.session_state.deal_closed = False
    else:
        st.divider()
        st.subheader("📊 Negotiation Performance Evaluation")
        
        # Enhanced deal summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Price", f"${agreed_terms['price']}")
        with col2:
            st.metric("Final Delivery", f"{agreed_terms['delivery']} days")
        with col3:
            st.metric("Final Volume", f"{agreed_terms['volume']:,} units" if agreed_terms['volume'] else "Standard")
        
        with st.spinner("🤖 Evaluating your negotiation performance..."):
            evaluation = evaluate_deal(
                st.session_state.history,
                st.session_state.deal_params,
                final_agreement=agreed_terms
            )
        
        clean_evaluation = sanitize_text_for_display(evaluation)
        st.markdown(clean_evaluation)
        st.session_state.evaluation_shown = True
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Start New Negotiation", type="primary", use_container_width=True):
                st.session_state.clear()
                st.rerun()

# Enhanced chat interface
if not st.session_state.deal_closed:
    if user_input := st.chat_input("Your proposal...", key="negotiation_input"):
        # Add user message
        st.session_state.history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Determine next state
        st.session_state.state = determine_next_state(st.session_state.state, user_input)
        
        # Generate AI response with concise prompt
        ai_task = "Respond concisely in 2-3 sentences. Be direct and business-like. Propose trade-offs if needed."
        
        conversation_history_for_prompt = "\n".join([
            f'{msg["role"].title()}: {msg["content"]}' for msg in st.session_state.history
        ])
        
        final_prompt = MASTER_PROMPT_TEMPLATE.format(
            deal_parameters=st.session_state.deal_parameters_str,
            conversation_history=conversation_history_for_prompt,
            current_state=st.session_state.state,
            user_input=user_input,
            ai_task=ai_task
        )
        
        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Alex is analyzing your proposal..."):
                ai_response = get_ai_response(final_prompt)
            sanitized_response = sanitize_text_for_display(ai_response)
            wrapped_response = wrap_text(sanitized_response)
            st.markdown(wrapped_response)

        # Add AI response to history
        st.session_state.history.append({"role": "assistant", "content": ai_response})

        # Cache latest assistant proposal for better agreement detection
        price = extract_price(ai_response)
        delivery = extract_delivery(ai_response)
        volume = extract_volume(ai_response)
        if sum(1 for x in (price, delivery, volume) if x is not None) >= 2:
            st.session_state.last_assistant_proposal = {
                "price": price, 
                "delivery": delivery, 
                "volume": volume, 
                "content": ai_response
            }

        # Enhanced agreement detection
        is_valid, missing_terms, agreed_terms = validate_agreement(st.session_state.history)
        if is_valid:
            # Improve agreement terms selection
            last_user_msg = next((m for m in reversed(st.session_state.history) if m["role"] == "user"), None)
            if last_user_msg:
                user_price = extract_price(last_user_msg["content"])
                user_delivery = extract_delivery(last_user_msg["content"])
                user_volume = extract_volume(last_user_msg["content"])

                if sum(1 for x in (user_price, user_delivery, user_volume) if x is not None) < 2:
                    last_prop = st.session_state.get("last_assistant_proposal")
                    if last_prop:
                        agreed_terms = {
                            "price": last_prop["price"], 
                            "delivery": last_prop["delivery"], 
                            "volume": last_prop["volume"]
                        }

            st.session_state.pending_confirmation = agreed_terms
            st.session_state.state = "AWAITING_CONFIRMATION"
            st.rerun()
        else:
            st.session_state.pending_confirmation = None
