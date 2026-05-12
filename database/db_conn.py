import mysql.connector
from mysql.connector import Error
import streamlit as st
from contextlib import contextmanager
import bcrypt


class DatabaseConnection:
    """Database connection manager with context handling"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "cognitivequest",
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": False
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)
            yield conn, cursor
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            st.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def get_connection_simple(self):
        """Simple connection for pandas"""
        return mysql.connector.connect(**self.config)


# Singleton instance
db = DatabaseConnection()


def get_connection():
    """Get database connection for backward compatibility"""
    return db.get_connection_simple()


# =========================================
# HASH PASSWORD FUNCTION
# =========================================
def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# =========================================
# ADMIN MANAGEMENT FUNCTIONS
# =========================================
def admin_exists():
    """Check if admin account exists in the database"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM users WHERE role = 'admin' LIMIT 1"
        cursor.execute(query)
        admin = cursor.fetchone()

        return admin is not None

    except Error as e:
        print(f"Database error in admin_exists: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def create_admin(username, email, password):
    """Create admin account with email"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        hashed_password = hash_password(password)

        query = """
        INSERT INTO users (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(query, (username, email, hashed_password, "admin"))
        conn.commit()

        return True

    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            raise Exception("Username already exists. Please choose a different username.")
        raise
    except Error as e:
        raise Exception(f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# =========================================
# USER MANAGEMENT FUNCTIONS
# =========================================
def get_user_by_username(username):
    """Get user by username"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        return user

    except Error as e:
        print(f"Database error in get_user_by_username: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_user_by_email(email):
    """Get user by email"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        return user

    except Error as e:
        print(f"Database error in get_user_by_email: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def create_user(username, email, password, role="teacher"):
    """Create a new user"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        hashed_password = hash_password(password)

        query = """
        INSERT INTO users (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(query, (username, email, hashed_password, role))
        conn.commit()

        return cursor.lastrowid

    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            if "username" in str(e):
                raise Exception("Username already exists. Please choose a different username.")
            elif "email" in str(e):
                raise Exception("Email already registered. Please use a different email.")
        raise
    except Error as e:
        raise Exception(f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_user_last_login(user_id):
    """Update user's last login timestamp"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        conn.commit()

    except Error as e:
        print(f"Database error in update_user_last_login: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_all_users():
    """Get all users for admin"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, username, email, role, created_at, last_login 
            FROM users 
            ORDER BY user_id
        """)
        users = cursor.fetchall()

        return users

    except Error as e:
        print(f"Database error in get_all_users: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_user(user_id, username=None, email=None, role=None):
    """Update user information"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        updates = []
        values = []

        if username:
            updates.append("username = %s")
            values.append(username)
        if email:
            updates.append("email = %s")
            values.append(email)
        if role:
            updates.append("role = %s")
            values.append(role)

        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
            values.append(user_id)
            cursor.execute(query, values)
            conn.commit()

        return True

    except Error as e:
        print(f"Database error in update_user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def delete_user(user_id):
    """Delete a user"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()

        return cursor.rowcount > 0

    except Error as e:
        print(f"Database error in delete_user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def change_user_password(user_id, new_password):
    """Change user password"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        hashed_password = hash_password(new_password)

        query = "UPDATE users SET password_hash = %s WHERE user_id = %s"
        cursor.execute(query, (hashed_password, user_id))
        conn.commit()

        return cursor.rowcount > 0

    except Error as e:
        print(f"Database error in change_user_password: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()



