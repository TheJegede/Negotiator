#!/usr/bin/env python3
"""
Demo script showing how to interact with the AI Supply Chain Negotiator
"""
import requests
import json

# API URL - update port to match your running server
API_URL = "http://localhost:8000"  # Default port from README

def demo_negotiation():
    print("=" * 60)
    print("AI Supply Chain Negotiator Demo")
    print("=" * 60)
    print()
    
    # Step 1: Create a new session
    print("1. Creating new negotiation session...")
    student_id = "DEMO123"
    response = requests.post(
        f"{API_URL}/api/sessions/new",
        json={"student_id": student_id}
    )
    session_data = response.json()
    session_id = session_data["session_id"]
    
    print(f"   Session ID: {session_id}")
    print(f"   Student ID: {student_id}")
    print()
    
    # Display deal parameters
    params = session_data["deal_parameters"]
    print("2. Deal Parameters:")
    print(f"   Base Price: ${params['base_price']}/unit")
    print(f"   Target Quantity: {params['target_quantity']} units")
    print(f"   Delivery: {params['delivery_days']} days")
    print(f"   Quality: Grade {params['quality_grade']}")
    print(f"   Warranty: {params['warranty_months']} months")
    print()
    
    # Display Alex's initial message
    print("3. Alex says:")
    print(f"   '{session_data['initial_message']['content']}'")
    print()
    
    # Step 2: Negotiate
    messages = [
        f"Can you do ${params['base_price'] - 10} per unit?",
        f"What about {params['target_quantity'] + 200} units?",
        "I accept the deal"
    ]
    
    print("4. Negotiation:")
    for i, msg in enumerate(messages, 1):
        print(f"   You: {msg}")
        response = requests.post(
            f"{API_URL}/api/chat",
            json={
                "session_id": session_id,
                "message": msg
            }
        )
        chat_data = response.json()
        print(f"   Alex: {chat_data['alex_response']}")
        print()
        
        if chat_data.get("deal_closed"):
            print("5. Deal Closed! Evaluation Results:")
            eval_data = chat_data["evaluation"]
            if eval_data and eval_data.get("deal_completed"):
                print(f"   Overall Score: {eval_data['overall_score']}/100")
                print()
                print("   Metrics:")
                for metric, score in eval_data["metrics"].items():
                    print(f"     - {metric.replace('_', ' ').title()}: {score}/100")
                print()
                print("   Final Deal:")
                details = eval_data["deal_details"]
                print(f"     - Price: ${details['final_price']}/unit (was ${details['base_price']})")
                print(f"     - Quantity: {details['quantity']} units")
                print(f"     - Delivery: {details['delivery_days']} days")
                print(f"     - Turns: {details['turns_taken']}")
            break
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    try:
        demo_negotiation()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server.")
        print("Please start the server with: uvicorn app:app --reload --port 8001")
    except Exception as e:
        print(f"Error: {e}")
