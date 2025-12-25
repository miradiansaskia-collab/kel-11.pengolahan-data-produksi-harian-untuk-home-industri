# modules/auth.py - Fungsi Authentication
import os
import json

def load_users():
    """Load user data dari file JSON"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "admin": {"password": "admin123", "role": "admin"}
    }

def save_users(users):
    """Save user data ke file JSON"""
    with open('users.json', 'w') as f:
        json.dump(users, f)

def authenticate_user(username, password):
    """Authenticate user"""
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True, users[username]['role']
    return False, None

def create_user(username, password, role):
    """Buat user baru"""
    users = load_users()
    
    if username in users:
        return False, f"❌ Username '{username}' sudah ada!"
    
    users[username] = {"password": password, "role": role}
    save_users(users)
    return True, f"✅ User '{username}' berhasil dibuat sebagai {role}!"