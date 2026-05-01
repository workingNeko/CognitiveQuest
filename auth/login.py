import json
import streamlit as st
from datetime import datetime, timedelta


def load_users():
    """Load users from JSON file"""
    try:
        with open("auth/users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default users file if it doesn't exist
        default_users = [
            {"username": "admin", "password": "admin123", "role": "admin", "name": "Administrator"},
            {"username": "teacher", "password": "teacher123", "role": "teacher", "name": "Teacher User"}
        ]
        save_users(default_users)
        return default_users


def save_users(users):
    """Save users to JSON file"""
    with open("auth/users.json", "w") as f:
        json.dump(users, f, indent=2)


def login_user(username, password):
    """Authenticate user and set session state"""
    users = load_users()

    for user in users:
        if user["username"] == username and user["password"] == password:
            # Set session state for logged in user
            st.session_state.logged_in = True
            st.session_state.user = {
                "username": user["username"],
                "role": user.get("role", "user"),
                "name": user.get("name", user["username"]),
                "login_time": datetime.now().isoformat()
            }
            return True

    return False


def logout_user():
    """Log out user and clear session"""
    # Clear all session state related to user
    st.session_state.logged_in = False
    st.session_state.user = None

    # Optional: Clear other session data
    keys_to_clear = ['user', 'login_time', 'user_data']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("logged_in", False)


def get_current_user():
    """Get current user info"""
    return st.session_state.get("user", None)


def require_auth():
    """Decorator-like function to protect pages"""
    if not is_authenticated():
        st.warning("Please login to access this page.")
        st.stop()


def check_session_expiry():
    """Check if session has expired (e.g., after 24 hours)"""
    user = get_current_user()
    if user and "login_time" in user:
        login_time = datetime.fromisoformat(user["login_time"])
        if datetime.now() - login_time > timedelta(hours=24):
            logout_user()
            return False
    return True