from typing import Any, Optional

from backend.utils.supabase_client import supabase


class SignupError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def sign_up_user(email: str, password: str, name: Optional[str] = None) -> Any:
    """
    Creates a new user account via Supabase.

    Args:
        email (str): The user's email address.
        password (str): The user's chosen password.
        name (Optional[str]): Optional display name.

    Returns:
        AuthResponse object if successful.

    Raises:
        SignupError: If signup fails.
    """
    print(f"Attempting to sign up user: {email}")
    try:
        clean_name = (name or "").strip()
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": clean_name,
                        "role": "driver",
                    }
                },
            }
        )
        print("Signup successful")
        return response
    except Exception as e:
        err = str(e)
        print(f"Signup failed for {email}: {err}")
        raise SignupError(err) from e


def login_user(email: str, password: str) -> Optional[Any]:
    """
    Authenticates an existing user and establishes a session.
    """
    print(f"Attempting to log in user: {email}")
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )
        print(f"Login successful! Welcome back, {response.user.email}")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id,
        }
    except Exception as e:
        print(f"Login failed for {email}: {str(e)}")
        return None


def logout_user() -> bool:
    """
    Returns:
        bool: True if logout was successful, False otherwise.
    """
    print("Attempting to log out...")
    try:
        supabase.auth.sign_out()
        print("Log out successful")
        return True
    except Exception as e:
        print(f"Log out failed: {str(e)}")
        return False
