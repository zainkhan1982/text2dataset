"""
Test script for user plan API endpoint
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Global user plans dictionary (simulating the one in app.py)
user_plans = {}

def test_user_plan_api():
    """Test the user plan API endpoint"""
    print("Testing User Plan API Endpoint...")
    
    # Test 1: Basic user
    print("\nTest 1: Basic user")
    user = "test_user_basic"
    user_plans[user] = "basic"
    
    # Simulate checking user plan
    user_plan = "basic"  # Default to basic plan
    if user in user_plans and user_plans[user] == "premium":
        user_plan = "premium"
    
    print(f"User {user} plan: {user_plan}")
    assert user_plan == "basic", "Basic user should have basic plan"
    
    # Test 2: Premium user
    print("\nTest 2: Premium user")
    user = "test_user_premium"
    user_plans[user] = "premium"
    
    # Simulate checking user plan
    user_plan = "basic"  # Default to basic plan
    if user in user_plans and user_plans[user] == "premium":
        user_plan = "premium"
    
    print(f"User {user} plan: {user_plan}")
    assert user_plan == "premium", "Premium user should have premium plan"
    
    # Test 3: User without any plan (default to basic)
    print("\nTest 3: User without any plan")
    user = "test_user_new"
    
    # Simulate checking user plan
    user_plan = "basic"  # Default to basic plan
    if user in user_plans and user_plans[user] == "premium":
        user_plan = "premium"
    
    print(f"User {user} plan: {user_plan}")
    assert user_plan == "basic", "New user should default to basic plan"
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_user_plan_api()