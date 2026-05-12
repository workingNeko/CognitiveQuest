import streamlit as st
from datetime import datetime, timedelta
from database.db_conn import get_connection
from .security import verify_password


def login_user(username, password):
    """Authenticate user"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE username=%s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    if user and verify_password(password, user["password_hash"]):
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user["user_id"],)
        )
        conn.commit()

        # Create session
        st.session_state.logged_in = True
        st.session_state.user = {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "created_at": str(user["created_at"]),
            "last_login": str(datetime.now()),
            "name": user["username"],
            "login_time": datetime.now().isoformat()
        }

        cursor.close()
        conn.close()
        return True

    cursor.close()
    conn.close()
    return False


def logout_user():
    """Logout user"""
    st.session_state.logged_in = False
    st.session_state.user = None

    for key in ["user", "login_time", "user_data"]:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("logged_in", False)


def get_current_user():
    """Get current user"""
    return st.session_state.get("user", None)


def check_session_expiry():
    """Check if session has expired"""
    user = get_current_user()

    if user and "login_time" in user:
        login_time = datetime.fromisoformat(user["login_time"])
        if datetime.now() - login_time > timedelta(hours=24):
            logout_user()
            return False

    return True