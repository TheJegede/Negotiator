"""
Deal Evaluation Service

Generates comprehensive performance evaluations after negotiations complete.
Scores students on 5 metrics and provides detailed feedback for learning.
"""

from typing import Dict, Any, List, Tuple
import json


class NegotiationEvaluator:
    """
    Evaluates negotiation performance across 5 dimensions.
    Provides scoring and detailed feedback for student learning.
    """
    
    # Scoring weights for final score calculation
    METRIC_WEIGHTS = {
        "deal_quality": 0.33,           # 33% weight
        "trade_off_strategy": 0.28,     # 28% weight
        "professionalism": 0.17,        # 17% weight
        "process_management": 0.11,     # 11% weight
        "creativity_adaptability": 0.11 # 11% weight
    }
    
    # Score thresholds for letter grades
    GRADE_THRESHOLDS = {
        "A": 90,   # Excellent
        "B": 80,   # Good
        "C": 70,   # Satisfactory
        "D": 60,   # Needs Improvement
        "F": 0     # Failing
    }
    
    def __init__(self, conversation_history: List[Dict[str, str]], 
                 deal_params: Dict[str, Any],
                 agreed_terms: Dict[str, float]):
        """
        Initialize evaluator with negotiation data.
        
        Args:
            conversation_history: Full chat history with user and assistant messages
            deal_params: Original deal parameters (the AI's secret targets)
            agreed_terms: Final agreed price, delivery, volume
        """
        self.history = conversation_history
        self.deal_params = deal_params
        self.agreed_terms = agreed_terms
    
    def evaluate(self) -> Dict[str, Any]:
        """
        Performs comprehensive evaluation across all 5 metrics.
        
        Returns:
            dict: Contains all scores, feedback, and analysis
        """
        
        # Calculate individual metric scores
        deal_quality_score = self._score_deal_quality()
        strategy_score = self._score_trade_off_strategy()
        professionalism_score = self._score_professionalism()
        process_score = self._score_process_management()
        creativity_score = self._score_creativity_adaptability()
        
        # Calculate weighted overall score
        overall_score = self._calculate_overall_score(
            deal_quality_score,
            strategy_score,
            professionalism_score,
            process_score,
            creativity_score
        )
        
        # Generate detailed feedback
        feedback = self._generate_feedback(
            deal_quality_score,
            strategy_score,
            professionalism_score,
            process_score,
            creativity_score,
            overall_score
        )
        
        # Compile analysis
        analysis = self._analyze_deal_metrics()
        
        return {
            "overall_score": overall_score,
            "overall_grade": self._score_to_grade(overall_score),
            "metrics": {
                "deal_quality": {
                    "score": deal_quality_score,
                    "grade": self._score_to_grade(deal_quality_score),
                    "weight": "33%"
                },
                "trade_off_strategy": {
                    "score": strategy_score,
                    "grade": self._score_to_grade(strategy_score),
                    "weight": "28%"
                },
                "professionalism": {
                    "score": professionalism_score,
                    "grade": self._score_to_grade(professionalism_score),
                    "weight": "17%"
                },
                "process_management": {
                    "score": process_score,
                    "grade": self._score_to_grade(process_score),
                    "weight": "11%"
                },
                "creativity_adaptability": {
                    "score": creativity_score,
                    "grade": self._score_to_grade(creativity_score),
                    "weight": "11%"
                }
            },
            "negotiation_analysis": analysis,
            "feedback": feedback,
            "agreed_terms": self.agreed_terms,
            "negotiation_rounds": len([m for m in self.history if m["role"] == "user"])
        }
    
    def _score_deal_quality(self) -> float:
        """
        Scores how favorable the final deal is compared to opening offers.
        Measures distance from AI's targets and openings.
        
        Returns:
            float: Score 0-100
        """
        
        if not self.agreed_terms:
            return 0.0
        
        final_price = self.agreed_terms.get("price")
        final_delivery = self.agreed_terms.get("delivery")
        opening_price = self.deal_params["price"]["opening"]
        opening_delivery = self.deal_params["delivery"]["opening"]
        target_price = self.deal_params["price"]["target"]
        target_delivery = self.deal_params["delivery"]["target"]
        reservation_price = self.deal_params["price"]["reservation"]
        
        # Calculate price score (how much better than opening?)
        price_reduction_pct = ((opening_price - final_price) / opening_price) * 100
        
        # Ideal: Reached target price or better (20%+ reduction)
        if final_price <= target_price:
            price_component = 95
        # Good: 15-20% reduction
        elif price_reduction_pct >= 15:
            price_component = 80
        # Acceptable: 10-15% reduction
        elif price_reduction_pct >= 10:
            price_component = 70
        # Mediocre: 5-10% reduction
        elif price_reduction_pct >= 5:
            price_component = 50
        # Poor: Less than 5% reduction
        else:
            price_component = 30
        
        # Calculate delivery score
        delivery_reduction = opening_delivery - final_delivery
        delivery_reduction_pct = (delivery_reduction / opening_delivery) * 100
        
        # Ideal: Reached target or better (15%+ reduction)
        if final_delivery <= target_delivery:
            delivery_component = 95
        # Good: 15-20% reduction
        elif delivery_reduction_pct >= 15:
            delivery_component = 80
        # Acceptable: 10-15% reduction
        elif delivery_reduction_pct >= 10:
            delivery_component = 70
        # Mediocre: 5-10% reduction
        elif delivery_reduction_pct >= 5:
            delivery_component = 50
        # Poor: Less than 5% reduction
        else:
            delivery_component = 30
        
        # Combined score (60% price, 40% delivery importance)
        deal_quality_score = (price_component * 0.6) + (delivery_component * 0.4)
        
        return round(deal_quality_score, 1)
    
    def _score_trade_off_strategy(self) -> float:
        """
        Scores understanding of trade-offs and win-win opportunities.
        Looks for explicit trade-off proposals and volume negotiations.
        
        Returns:
            float: Score 0-100
        """
        
        # Extract user messages only
        user_messages = [m["content"] for m in self.history if m["role"] == "user"]
        
        # Scan for trade-off keywords
        trade_off_keywords = [
            "if you", "in exchange", "trade", "volume", "order more",
            "larger order", "bulk", "quantity", "conditional", "deal",
            "discount", "lower price if", "faster delivery if"
        ]
        
        trade_off_count = 0
        for message in user_messages:
            message_lower = message.lower()
            for keyword in trade_off_keywords:
                if keyword in message_lower:
                    trade_off_count += 1
                    break
        
        # Score based on trade-off attempts
        total_rounds = len(user_messages)
        
        if trade_off_count == 0:
            # No trade-off attempts - pure anchoring
            return 30.0
        elif trade_off_count == 1:
            # One attempt - minimal strategy
            return 50.0
        elif trade_off_count >= 2 and trade_off_count <= total_rounds * 0.5:
            # Multiple attempts, good frequency (50%+ of rounds)
            return 75.0
        else:
            # Consistent trade-off thinking throughout
            return 90.0
    
    def _score_professionalism(self) -> float:
        """
        Scores communication quality, tone, and persuasiveness.
        Analyzes professionalism indicators and red flags.
        
        Returns:
            float: Score 0-100
        """
        
        user_messages = [m["content"] for m in self.history if m["role"] == "user"]
        
        professionalism_score = 85  # Start with good score
        
        # Red flags that reduce score
        red_flags = {
            "rude": ["stupid", "ridiculous", "unacceptable", "outrageous", "idiot"],
            "aggressive": ["demand", "must", "have to", "forced to"],
            "unprofessional": ["lol", "omg", "ur", "gonna"],
            "uninformed": ["no idea", "don't know", "clueless"]
        }
        
        for message in user_messages:
            message_lower = message.lower()
            for category, keywords in red_flags.items():
                for keyword in keywords:
                    if keyword in message_lower:
                        professionalism_score -= 10
        
        # Positive indicators that increase score
        positive_indicators = {
            "please": 5,
            "thank": 5,
            "appreciate": 5,
            "understand": 3,
            "reasonable": 3,
            "flexible": 5,
            "partnership": 5,
            "professional": 5
        }
        
        for message in user_messages:
            message_lower = message.lower()
            for indicator, bonus in positive_indicators.items():
                if indicator in message_lower:
                    professionalism_score = min(100, professionalism_score + bonus)
        
        return max(0, round(professionalism_score, 1))
    
    def _score_process_management(self) -> float:
        """
        Scores negotiation flow, clarity, and summaries.
        Measures organization and communication effectiveness.
        
        Returns:
            float: Score 0-100
        """
        
        user_messages = [m["content"] for m in self.history if m["role"] == "user"]
        
        process_score = 70  # Base score
        
        # Check for explicit confirmations
        confirmation_keywords = ["confirm", "agree", "deal", "accept", "correct", "agreed"]
        has_confirmations = any(
            any(keyword in msg.lower() for keyword in confirmation_keywords)
            for msg in user_messages
        )
        if has_confirmations:
            process_score += 15
        
        # Check message length - balanced messages are better
        avg_message_length = sum(len(msg.split()) for msg in user_messages) / len(user_messages)
        if 10 <= avg_message_length <= 40:
            # Sweet spot: detailed but concise
            process_score += 10
        elif avg_message_length > 100:
            # Too verbose
            process_score -= 10
        elif avg_message_length < 5:
            # Too terse, lacking detail
            process_score -= 5
        
        # Check for multiple offers/counteroffers
        offer_count = sum(1 for msg in user_messages if "$" in msg or "day" in msg.lower())
        if offer_count >= len(user_messages) * 0.7:
            # Most messages contain actual offers
            process_score += 10
        
        return min(100, max(0, round(process_score, 1)))
    
    def _score_creativity_adaptability(self) -> float:
        """
        Scores innovation, flexibility, and strategy adjustment.
        Measures if student adapted to AI responses or stuck with same approach.
        
        Returns:
            float: Score 0-100
        """
        
        user_messages = [m["content"] for m in self.history if m["role"] == "user"]
        
        if len(user_messages) < 2:
            return 50.0  # Not enough data to evaluate
        
        # Check for offer variation - are numbers changing?
        offers = []
        for msg in user_messages:
            # Extract all numbers that look like prices or days
            import re
            numbers = re.findall(r'\$?(\d+(?:\.\d{2})?)', msg)
            if numbers:
                offers.append(numbers)
        
        # Analyze variation in offers
        if len(offers) == 0:
            return 30.0  # No numerical offers
        
        # Count unique offers
        unique_offers = len(set(tuple(sorted(o)) for o in offers))
        unique_ratio = unique_offers / len(offers) if offers else 0
        
        # Score based on adaptation
        if unique_ratio >= 0.8:
            # High variation - good adaptation
            adaptation_score = 90
        elif unique_ratio >= 0.6:
            # Some variation
            adaptation_score = 75
        elif unique_ratio >= 0.4:
            # Limited variation
            adaptation_score = 55
        else:
            # Repetitive offers, poor adaptation
            adaptation_score = 35
        
        # Bonus for attempting new strategies
        strategy_keywords = ["alternative", "instead", "different", "volume", "terms", "creative"]
        strategy_attempts = sum(
            1 for msg in user_messages
            if any(keyword in msg.lower() for keyword in strategy_keywords)
        )
        
        if strategy_attempts >= 2:
            adaptation_score = min(100, adaptation_score + 15)
        
        return round(adaptation_score, 1)
    
    def _calculate_overall_score(self, deal_quality: float, strategy: float,
                                 professionalism: float, process: float,
                                 creativity: float) -> float:
        """
        Calculates weighted overall score from 5 metrics.
        
        Returns:
            float: Overall score 0-100
        """
        
        overall = (
            deal_quality * self.METRIC_WEIGHTS["deal_quality"] +
            strategy * self.METRIC_WEIGHTS["trade_off_strategy"] +
            professionalism * self.METRIC_WEIGHTS["professionalism"] +
            process * self.METRIC_WEIGHTS["process_management"] +
            creativity * self.METRIC_WEIGHTS["creativity_adaptability"]
        )
        
        return round(overall, 1)
    
    def _score_to_grade(self, score: float) -> str:
        """
        Converts numerical score to letter grade.
        
        Args:
            score: Score 0-100
            
        Returns:
            str: Letter grade (A, B, C, D, F)
        """
        
        for grade, threshold in sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return grade
        return "F"
    
    def _analyze_deal_metrics(self) -> Dict[str, Any]:
        """
        Analyzes deal metrics: price achieved, delivery, volume.
        Compares against opening and target offers.
        
        Returns:
            dict: Detailed deal analysis
        """
        
        if not self.agreed_terms:
            return {"status": "No agreement reached"}
        
        final_price = self.agreed_terms.get("price", 0)
        final_delivery = self.agreed_terms.get("delivery", 0)
        final_volume = self.agreed_terms.get("volume", 0)
        
        opening_price = self.deal_params["price"]["opening"]
        target_price = self.deal_params["price"]["target"]
        opening_delivery = self.deal_params["delivery"]["opening"]
        target_delivery = self.deal_params["delivery"]["target"]
        
        price_reduction = opening_price - final_price
        price_reduction_pct = (price_reduction / opening_price) * 100
        distance_from_target = final_price - target_price
        
        delivery_reduction = opening_delivery - final_delivery
        delivery_reduction_pct = (delivery_reduction / opening_delivery) * 100 if opening_delivery > 0 else 0
        
        return {
            "price_analysis": {
                "final": final_price,
                "opening": opening_price,
                "target": target_price,
                "reduction": price_reduction,
                "reduction_pct": f"{price_reduction_pct:.1f}%",
                "distance_from_target": distance_from_target,
                "beat_target": final_price <= target_price
            },
            "delivery_analysis": {
                "final": final_delivery,
                "opening": opening_delivery,
                "target": target_delivery,
                "reduction": delivery_reduction,
                "reduction_pct": f"{delivery_reduction_pct:.1f}%",
                "distance_from_target": final_delivery - target_delivery,
                "beat_target": final_delivery <= target_delivery
            },
            "volume": final_volume,
            "rounds": len([m for m in self.history if m["role"] == "user"])
        }
    
    def _generate_feedback(self, deal_quality: float, strategy: float,
                          professionalism: float, process: float,
                          creativity: float, overall: float) -> str:
        """
        Generates personalized, constructive feedback.
        Highlights strengths and areas for improvement.
        
        Returns:
            str: Comprehensive feedback text
        """
        
        feedback_parts = []
        
        # Overall assessment
        if overall >= 90:
            feedback_parts.append(f"🌟 Outstanding negotiation! Score: {overall}/100")
        elif overall >= 80:
            feedback_parts.append(f"✅ Strong performance. Score: {overall}/100")
        elif overall >= 70:
            feedback_parts.append(f"📈 Solid effort. Score: {overall}/100")
        elif overall >= 60:
            feedback_parts.append(f"⚠️ Room for improvement. Score: {overall}/100")
        else:
            feedback_parts.append(f"❌ Needs significant improvement. Score: {overall}/100")
        
        # Deal Quality feedback
        feedback_parts.append("\n**Deal Quality:**")
        if deal_quality >= 90:
            feedback_parts.append("- Excellent! You achieved pricing at or near the target range.")
        elif deal_quality >= 80:
            feedback_parts.append("- Good negotiation! You secured meaningful price and delivery reductions.")
        elif deal_quality >= 70:
            feedback_parts.append("- You reached agreement with moderate savings on initial offers.")
        elif deal_quality >= 60:
            feedback_parts.append("- Limited concessions achieved. Consider more assertive negotiation next time.")
        else:
            feedback_parts.append("- The final deal was not significantly better than opening offers.")
        
        # Strategy feedback
        feedback_parts.append("\n**Trade-off Strategy:**")
        if strategy >= 90:
            feedback_parts.append("- Excellent! You consistently identified and proposed win-win trade-offs.")
        elif strategy >= 75:
            feedback_parts.append("- Good! You recognized trade-off opportunities between price, delivery, and volume.")
        elif strategy >= 50:
            feedback_parts.append("- You made some trade-off attempts, but could explore more creative combinations.")
        else:
            feedback_parts.append("- Consider using trade-offs: 'I can accept X if you offer Y'")
        
        # Professionalism feedback
        feedback_parts.append("\n**Professionalism:**")
        if professionalism >= 90:
            feedback_parts.append("- Outstanding tone and communication. Respectful and persuasive throughout.")
        elif professionalism >= 80:
            feedback_parts.append("- Professional communication with clear reasoning behind your offers.")
        elif professionalism >= 70:
            feedback_parts.append("- Generally professional with occasional informal language.")
        else:
            feedback_parts.append("- Focus on maintaining professional tone. Avoid aggressive or dismissive language.")
        
        # Process feedback
        feedback_parts.append("\n**Process Management:**")
        if process >= 90:
            feedback_parts.append("- Excellent organization! Clear offers, explicit confirmations, strong flow.")
        elif process >= 80:
            feedback_parts.append("- Good structure. Your offers were clear and progression was logical.")
        elif process >= 70:
            feedback_parts.append("- Adequate process. Consider summarizing agreed points periodically.")
        else:
            feedback_parts.append("- Work on clarity: make specific offers and confirm mutual understanding.")
        
        # Creativity feedback
        feedback_parts.append("\n**Creativity & Adaptability:**")
        if creativity >= 90:
            feedback_parts.append("- Excellent! You adapted strategy based on responses and tried multiple approaches.")
        elif creativity >= 75:
            feedback_parts.append("- Good adaptability. You adjusted offers based on feedback and explored alternatives.")
        elif creativity >= 55:
            feedback_parts.append("- Some adaptation shown, but offers were somewhat repetitive overall.")
        else:
            feedback_parts.append("- Next time, try varying your proposals more based on counteroffers.")
        
        # Key recommendations
        feedback_parts.append("\n**Key Recommendations:**")
        top_weakness = min([
            ("deal_quality", deal_quality),
            ("strategy", strategy),
            ("professionalism", professionalism),
            ("process", process),
            ("creativity", creativity)
        ], key=lambda x: x[1])
        
        if top_weakness[0] == "deal_quality":
            feedback_parts.append("- Focus on achieving better price/delivery concessions. Plan your walk-away point before negotiating.")
        elif top_weakness[0] == "strategy":
            feedback_parts.append("- Develop a strategy sheet before negotiating: identify trade-offs (price for volume, delivery for price).")
        elif top_weakness[0] == "professionalism":
            feedback_parts.append("- Practice maintaining professional tone even when frustrated. Justify your positions calmly.")
        elif top_weakness[0] == "process":
            feedback_parts.append("- Create a structured template: 'So we have: Price X, Delivery Y, Volume Z. Agreed?' Build mutual understanding.")
        else:
            feedback_parts.append("- Be flexible! When an offer is rejected, immediately propose a different combination rather than repeating.")
        
        return "\n".join(feedback_parts)


def evaluate_negotiation(conversation_history: List[Dict[str, str]],
                        deal_params: Dict[str, Any],
                        agreed_terms: Dict[str, float]) -> Dict[str, Any]:
    """
    Convenience function to evaluate a complete negotiation.
    
    Args:
        conversation_history: Full chat history
        deal_params: Original deal parameters
        agreed_terms: Final agreed terms
        
    Returns:
        dict: Complete evaluation results
    """
    
    evaluator = NegotiationEvaluator(conversation_history, deal_params, agreed_terms)
    return evaluator.evaluate()


if __name__ == "__main__":
    """
    Example usage and testing
    """
    
    # Sample data for testing
    sample_history = [
        {"role": "assistant", "content": "Good morning, I'm Alex from ChipSource. Our standard price is $52.50 per unit with 60-day delivery."},
        {"role": "user", "content": "That's quite high. Can you reduce it to $40 per unit with 30-day delivery?"},
        {"role": "assistant", "content": "I appreciate the interest, but $40 is below our range. I can offer $48 per unit with 50-day delivery if you commit to 15,000 units."},
        {"role": "user", "content": "What if we did $45 per unit and 40 days if we order 20,000 units? That's a good volume commitment."},
        {"role": "assistant", "content": "That's a fair proposal! I can accept $44 per unit, 42-day delivery for 20,000 units. This volume qualifies you for our Tier 1 discount."},
        {"role": "user", "content": "Perfect! So we have a deal: $44 per unit, 42 days, 20,000 units. I confirm this agreement."},
    ]
    
    sample_params = {
        "price": {"opening": 52.50, "target": 42.00, "reservation": 38.50},
        "delivery": {"opening": 60, "target": 45, "reservation": 35}
    }
    
    sample_agreed = {"price": 44.0, "delivery": 42, "volume": 20000}
    
    print("=" * 70)
    print("NEGOTIATION EVALUATION REPORT")
    print("=" * 70)
    
    evaluation = evaluate_negotiation(sample_history, sample_params, sample_agreed)
    
    print(f"\nOverall Score: {evaluation['overall_score']}/100 ({evaluation['overall_grade']})")
    print("\nMetric Scores:")
    for metric, data in evaluation['metrics'].items():
        print(f"  {metric.replace('_', ' ').title()}: {data['score']}/100 ({data['grade']}) - Weight: {data['weight']}")
    
    print("\nDeal Analysis:")
    price_analysis = evaluation['negotiation_analysis']['price_analysis']
    print(f"  Price: ${price_analysis['final']} (opened at ${price_analysis['opening']}, target ${price_analysis['target']})")
    print(f"  Reduction: {price_analysis['reduction_pct']} savings")
    
    delivery_analysis = evaluation['negotiation_analysis']['delivery_analysis']
    print(f"  Delivery: {delivery_analysis['final']} days (opened at {delivery_analysis['opening']}, target {delivery_analysis['target']})")
    print(f"  Reduction: {delivery_analysis['reduction_pct']} faster")
    
    print(f"\nNegotiation Rounds: {evaluation['negotiation_rounds']}")
    
    print("\nFeedback:")
    print(evaluation['feedback'])