"""
Quick test script to verify the API is working correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_plan_retrieval():
    """Test if we can retrieve a plan with conversation history"""
    
    print("🔍 Testing Plan Retrieval...")
    print("=" * 60)
    
    # First, let's check if there are any plans
    print("\n1. Checking for existing plans...")
    
    # You'll need to replace this with your actual token
    # Get it by logging in first
    token = "YOUR_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Get list of plans
    try:
        response = requests.get(f"{BASE_URL}/plans/", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            plans = response.json()
            print(f"   Found {len(plans)} plans")
            
            if plans:
                # Get the first plan
                plan_id = plans[0]['id']
                print(f"\n2. Fetching plan {plan_id} details...")
                
                plan_response = requests.get(f"{BASE_URL}/plans/{plan_id}", headers=headers)
                print(f"   Status: {plan_response.status_code}")
                
                if plan_response.status_code == 200:
                    plan_data = plan_response.json()
                    
                    print(f"\n✅ Plan Retrieved Successfully!")
                    print(f"   Title: {plan_data.get('title')}")
                    print(f"   Destination: {plan_data.get('destination')}")
                    print(f"   Content length: {len(plan_data.get('content', ''))}")
                    print(f"   Conversation history: {len(plan_data.get('conversation_history', []))} messages")
                    
                    # Check conversation history
                    if plan_data.get('conversation_history'):
                        print(f"\n📝 Conversation History:")
                        for i, msg in enumerate(plan_data['conversation_history'][:3]):  # Show first 3
                            print(f"   {i+1}. {msg['role']}: {msg['content'][:100]}...")
                    
                    # Check if content exists
                    if plan_data.get('content'):
                        print(f"\n📄 Content Preview:")
                        print(f"   {plan_data['content'][:200]}...")
                    else:
                        print(f"\n⚠️  WARNING: No content in plan!")
                        
                else:
                    print(f"   ❌ Error: {plan_response.text}")
            else:
                print("   No plans found. Create one first!")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to backend. Is it running on http://localhost:8000?")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  API TEST SCRIPT")
    print("=" * 60)
    print("\nNOTE: You need to:")
    print("1. Start the backend: python main.py")
    print("2. Get your auth token from /auth/token")
    print("3. Replace 'YOUR_TOKEN_HERE' in this script")
    print("=" * 60)
    
    test_plan_retrieval()
