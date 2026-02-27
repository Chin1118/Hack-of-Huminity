from typing import Any, Optional
from backend.utils.supabase_client import supabase

def sign_up_user(email: str, password: str) -> Optional[Any]:
    """
    Creates a new user account via Supabase.
    
    Args:
        email (str): The user's email address.
        password (str): The user's chosen password.
        
    Returns:
        AuthResponse object if successful, None if it fails.
    """
    print(f"Attempting to sign up user: {email}")
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        print("✅ Sign up successful!")
        return response
    except Exception as e:
        print(f"❌ Sign up failed for {email}: {str(e)}")
        return None

def login_user(email: str, password: str) -> Optional[Any]:
    """
    Authenticates an existing user and establishes a session.
    """
    print(f"Attempting to log in user: {email}")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        print(f"✅ Login successful! Welcome back, {response.user.email}")
        # Extract the tokens to send back to the client/frontend
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id
        }
    except Exception as e:
        print(f"❌ Login failed for {email}: {str(e)}")
        return None

def logout_user() -> bool:
    """
    Returns:
        bool: True if logout was successful, False otherwise.
    """
    print("Attempting to log out...")
    try:
        supabase.auth.sign_out()
        print("✅ Log out successful!")
        return True
    except Exception as e:
        print(f"❌ Log out failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_email = "honger1206@gmail.com"
    test_password = "12345678"

    login_user(test_email, test_password)