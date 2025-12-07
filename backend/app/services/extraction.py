import re

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
