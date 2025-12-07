"""
Deal Parameter Generation Service

Generates unique, reproducible negotiation scenarios for each student.
Parameters are seeded by student ID to ensure consistency across attempts.
"""

import random
from typing import Dict, Any


def generate_deal_parameters(seed: int = None) -> Dict[str, Any]:
    """
    Generates unique deal parameters for each student with meaningful negotiation ranges.
    Implements 15-25% reduction steps to enable dynamic and engaging negotiations.
    
    Args:
        seed (int, optional): Random seed for reproducibility. 
                             If None, completely random parameters.
                             If provided (from student ID hash), same student gets same deal.
    
    Returns:
        dict: Contains price and delivery parameters with opening, target, and reservation levels
        
    Example:
        >>> params = generate_deal_parameters(seed=12345)
        >>> params['price']['opening']
        52.50
        >>> params['delivery']['target']
        45
    """
    
    if seed is not None:
        random.seed(seed)
    
    # Configuration constants for negotiation ranges
    MIN_PRICE_DIFF = 5       # Minimum dollar difference between price levels
    MIN_DELIVERY_DIFF = 3    # Minimum day difference between delivery levels
    RESERVATION_FLOOR = 0.50 # Reservation cannot go below 50% of opening price
    
    # ==================== PRICE GENERATION ====================
    
    # Base price generation with wider ranges for meaningful negotiation
    # Range: $5 - $300 (realistic for bulk chip orders)
    opening_price = round(random.uniform(5, 30) * 10, 2)
    
    # Price reductions: 15-25% per step for meaningful negotiation space
    # This ensures students can negotiate down but not trivially
    price_reduction_1 = random.uniform(0.15, 0.25)  # 15-25% reduction for target
    price_reduction_2 = random.uniform(0.10, 0.15)  # Additional 10-15% reduction for reservation
    
    target_price = round(opening_price * (1 - price_reduction_1), 2)
    reservation_price = round(target_price * (1 - price_reduction_2), 2)

    # Ensure minimum price difference between levels for meaningful concessions
    if target_price >= opening_price - MIN_PRICE_DIFF:
        target_price = opening_price - MIN_PRICE_DIFF
        
    if reservation_price >= target_price - MIN_PRICE_DIFF:
        reservation_price = target_price - MIN_PRICE_DIFF
    
    # Ensure reservation doesn't go below floor percentage of opening
    # This prevents unrealistic deals (e.g., 90% discounts)
    min_reservation = round(opening_price * RESERVATION_FLOOR, 2)
    reservation_price = max(reservation_price, min_reservation)

    # ==================== DELIVERY GENERATION ====================
    
    # Delivery generation with meaningful reductions
    # Range: 40 - 100 days (realistic for manufacturing/supply chain)
    opening_delivery = int(round(random.uniform(4, 10) * 10))
    
    # Delivery reductions: 15-25% per step for meaningful negotiation
    delivery_reduction_1 = random.uniform(0.15, 0.25)  # 15-25% reduction for target
    delivery_reduction_2 = random.uniform(0.10, 0.15)  # Additional 10-15% reduction for reservation
    
    target_delivery = int(round(opening_delivery * (1 - delivery_reduction_1)))
    reservation_delivery = int(round(target_delivery * (1 - delivery_reduction_2)))

    # Ensure minimum delivery day difference between levels for meaningful concessions
    if target_delivery >= opening_delivery - MIN_DELIVERY_DIFF:
        target_delivery = opening_delivery - MIN_DELIVERY_DIFF
        
    if reservation_delivery >= target_delivery - MIN_DELIVERY_DIFF:
        reservation_delivery = target_delivery - MIN_DELIVERY_DIFF

    # ==================== VOLUME GENERATION ====================
    
    # Standard volume for negotiation
    # Default order size: 10,000 units
    standard_volume = 10000
    
    # Volume tier thresholds for discounts
    tier_1_volume = 20000  # 5% discount
    tier_2_volume = 50000  # 8% discount

    # ==================== RETURN PARAMETERS ====================
    
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
        },
        "volume": {
            "standard": standard_volume,
            "tier_1_threshold": tier_1_volume,
            "tier_1_discount": 0.05,
            "tier_2_threshold": tier_2_volume,
            "tier_2_discount": 0.08
        }
    }


def format_deal_parameters(params: Dict[str, Any]) -> str:
    """
    Formats deal parameters into a human-readable prompt template for the AI.
    This is the secret information given to the AI seller.
    
    Args:
        params (dict): Deal parameters from generate_deal_parameters()
        
    Returns:
        str: Formatted prompt template with negotiation strategy instructions
        
    Example:
        >>> params = generate_deal_parameters(seed=12345)
        >>> prompt = format_deal_parameters(params)
        >>> print(prompt[:100])
        --- Our Company: 'ChipSource Inc.' ---
    """
    
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
    * Standard orders are for {params['volume']['standard']:,} units. The prices above apply.
    * Tier 1 Discount: For orders > {params['volume']['tier_1_threshold']:,} units, a {params['volume']['tier_1_discount']*100:.0f}% discount on the final per-unit price is possible.
    * Tier 2 Discount: For orders > {params['volume']['tier_2_threshold']:,} units, a {params['volume']['tier_2_discount']*100:.0f}% discount on the final per-unit price is possible.

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


def validate_parameters(params: Dict[str, Any]) -> bool:
    """
    Validates that generated parameters are reasonable and follow constraints.
    
    Args:
        params (dict): Deal parameters to validate
        
    Returns:
        bool: True if parameters are valid, False otherwise
        
    Raises:
        ValueError: If parameters violate constraints
    """
    
    # Price constraints
    if not (params['price']['target'] < params['price']['opening']):
        raise ValueError("Target price must be less than opening price")
    
    if not (params['price']['reservation'] < params['price']['target']):
        raise ValueError("Reservation price must be less than target price")
    
    if not (params['price']['reservation'] > 0):
        raise ValueError("Reservation price must be positive")
    
    # Delivery constraints
    if not (params['delivery']['target'] < params['delivery']['opening']):
        raise ValueError("Target delivery must be less than opening delivery")
    
    if not (params['delivery']['reservation'] < params['delivery']['target']):
        raise ValueError("Reservation delivery must be less than target delivery")
    
    if not (params['delivery']['reservation'] > 0):
        raise ValueError("Reservation delivery must be positive")
    
    # Volume constraints
    if not (params['volume']['standard'] > 0):
        raise ValueError("Standard volume must be positive")
    
    if not (params['volume']['tier_1_threshold'] > params['volume']['standard']):
        raise ValueError("Tier 1 threshold must be greater than standard volume")
    
    if not (params['volume']['tier_2_threshold'] > params['volume']['tier_1_threshold']):
        raise ValueError("Tier 2 threshold must be greater than Tier 1 threshold")
    
    return True


def get_student_seed(student_id: str) -> int:
    """
    Converts student ID string to a reproducible random seed.
    Same student ID always produces same seed, ensuring consistent parameters.
    
    Args:
        student_id (str): Student identifier (e.g., "S12345" or "john.doe@university.edu")
        
    Returns:
        int: Seed value suitable for random.seed()
        
    Example:
        >>> seed1 = get_student_seed("S12345")
        >>> seed2 = get_student_seed("S12345")
        >>> seed1 == seed2  # Always same
        True
        >>> seed3 = get_student_seed("S12346")
        >>> seed1 == seed3  # Different student ID
        False
    """
    
    # Hash the student ID and convert to 32-bit integer
    # Modulo 2**32 ensures it fits in random.seed() range
    return hash(student_id) % (2**32)


def get_parameters_by_student(student_id: str) -> Dict[str, Any]:
    """
    Convenience function: Get consistent parameters for a specific student.
    
    Args:
        student_id (str): Student identifier
        
    Returns:
        dict: Deal parameters specific to this student
    """
    seed = get_student_seed(student_id)
    return generate_deal_parameters(seed=seed)


if __name__ == "__main__":
    """
    Example usage and testing
    """
    
    print("=" * 70)
    print("EXAMPLE 1: Random Parameters")
    print("=" * 70)
    params1 = generate_deal_parameters()
    print(f"Price: ${params1['price']['opening']} → ${params1['price']['target']} → ${params1['price']['reservation']}")
    print(f"Delivery: {params1['delivery']['opening']} → {params1['delivery']['target']} → {params1['delivery']['reservation']} days")
    
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Student-Specific Parameters (Reproducible)")
    print("=" * 70)
    student_id = "S12345"
    params2a = get_parameters_by_student(student_id)
    params2b = get_parameters_by_student(student_id)
    print(f"First generation: ${params2a['price']['opening']}")
    print(f"Second generation: ${params2b['price']['opening']}")
    print(f"Same? {params2a == params2b}")
    
    print("\n" + "=" * 70)
    print("EXAMPLE 3: AI Prompt Template")
    print("=" * 70)
    print(format_deal_parameters(params2a)[:500] + "...")
    
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Parameter Validation")
    print("=" * 70)
    try:
        validate_parameters(params1)
        print("✓ Parameters are valid!")
    except ValueError as e:
        print(f"✗ Validation error: {e}")