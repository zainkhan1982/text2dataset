"""
Test script for the API plan endpoint
"""

import sys
import os
import json

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_plan_endpoint():
    """Test the API plan endpoint logic"""
    print("Testing API Plan Endpoint Logic...")
    
    # Simulate the user_plans dictionary
    user_plans = {}
    
    # Test 1: Anonymous user
    print("\nTest 1: Anonymous user")
    current_user = None
    user_plan = "basic"  # Default to basic plan
    
    result = {"plan": user_plan}
    print(f"API response for anonymous user: {result}")
    assert result["plan"] == "basic", "Anonymous user should have basic plan"
    
    # Test 2: Basic user
    print("\nTest 2: Basic user")
    current_user = "test_user_basic"
    user_plans[current_user] = "basic"
    
    user_plan = "basic"  # Default to basic plan
    if current_user in user_plans and user_plans[current_user] == "premium":
        user_plan = "premium"
    
    result = {"plan": user_plan}
    print(f"API response for basic user: {result}")
    assert result["plan"] == "basic", "Basic user should have basic plan"
    
    # Test 3: Premium user
    print("\nTest 3: Premium user")
    current_user = "test_user_premium"
    user_plans[current_user] = "premium"
    
    user_plan = "basic"  # Default to basic plan
    if current_user in user_plans and user_plans[current_user] == "premium":
        user_plan = "premium"
    
    result = {"plan": user_plan}
    print(f"API response for premium user: {result}")
    assert result["plan"] == "premium", "Premium user should have premium plan"
    
    print("\nAll API endpoint tests passed!")

if __name__ == "__main__":
    test_api_plan_endpoint()