"""Simple script to test if backend is running and accessible"""
import requests

try:
    # Test health endpoint
    print("Testing backend connection...")
    response = requests.get("http://127.0.0.1:5000/api/health")
    print(f"✓ Health check: Status {response.status_code}")
    print(f"  Response: {response.json()}")
    
    # Test users endpoint
    response = requests.get("http://127.0.0.1:5000/api/users")
    print(f"✓ Users endpoint: Status {response.status_code}")
    users = response.json().get("users", [])
    print(f"  Found {len(users)} users:")
    for u in users:
        print(f"    - {u['name']} ({u['email']}) - Role: {u['role']}")
    
    print("\n✅ Backend is running and accessible!")
    
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to backend at http://127.0.0.1:5000")
    print("   Make sure Flask is running: python app.py")
except Exception as e:
    print(f"❌ ERROR: {e}")
