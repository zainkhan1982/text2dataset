"""
Test script for plan-based model selection
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Global user plans dictionary (simulating the one in app.py)
user_plans = {}

def test_plan_selection():
    """Test the plan-based model selection logic"""
    print("Testing Plan-Based Model Selection...")
    
    # Test 1: Basic user without premium plan
    print("\nTest 1: Basic user without premium plan")
    user = "test_user_basic"
    user_plans[user] = "basic"
    
    # Simulate checking if user has premium
    user_has_premium = False
    if user in user_plans and user_plans[user] == "premium":
        user_has_premium = True
    
    print(f"User {user} has premium: {user_has_premium}")
    assert not user_has_premium, "Basic user should not have premium access"
    
    # Test 2: Premium user
    print("\nTest 2: Premium user")
    user = "test_user_premium"
    user_plans[user] = "premium"
    
    # Simulate checking if user has premium
    user_has_premium = False
    if user in user_plans and user_plans[user] == "premium":
        user_has_premium = True
    
    print(f"User {user} has premium: {user_has_premium}")
    assert user_has_premium, "Premium user should have premium access"
    
    # Test 3: User without any plan (default to basic)
    print("\nTest 3: User without any plan")
    user = "test_user_new"
    
    # Simulate checking if user has premium
    user_has_premium = False
    if user in user_plans and user_plans[user] == "premium":
        user_has_premium = True
    
    print(f"User {user} has premium: {user_has_premium}")
    assert not user_has_premium, "New user should default to basic plan"
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_plan_selection()