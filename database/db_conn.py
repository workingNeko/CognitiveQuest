import mysql.connector
import bcrypt


def get_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="cognitivequest"
    )


def hash_password(password):
    """Hash a password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def admin_exists():
    """Check if admin account exists"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE role='admin'"
    cursor.execute(query)
    admin = cursor.fetchone()

    cursor.close()
    conn.close()

    return admin is not None


def create_admin(username, email, password):
    """Create admin account with email"""
    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = hash_password(password)

    query = """
    INSERT INTO users (username, email, password_hash, role)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (username, email, hashed_password, "admin"))
    conn.commit()

    cursor.close()
    conn.close()