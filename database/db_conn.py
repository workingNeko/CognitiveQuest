import mysql.connector
from mysql.connector import Error
import streamlit as st
from contextlib import contextmanager
import bcrypt
import logging
import time
from typing import Optional, Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager with context handling"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Localhost configuration (currently active)
        # self.config = {
        #     "host": "localhost",
        #     "user": "root",
        #     "password": "",
        #     "database": "cognitivequest",
        #     "charset": "utf8mb4",
        #     "use_unicode": True,
        #     "autocommit": False,
        # }

        #Online Railway configuration (commented out - switch to this when needed)
        self.config = {
            "host": "yamabiko.proxy.rlwy.net",
            "user": "root",
            "password": "KGJzKnCwbldVqELfuesOqxFSboLfmLBq",
            "database": "railway",
            "port": 3306,
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": False,
        }



        self.connection = None
        self.cursor = None
        self.max_retries = 3
        self.retry_delay = 1

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

    def connect(self):
        """Establish database connection with retry logic for pygame"""
        for attempt in range(self.max_retries):
            try:
                if self.connection and self.connection.is_connected():
                    return True

                self.connection = mysql.connector.connect(**self.config)
                if self.connection.is_connected():
                    self.cursor = self.connection.cursor(dictionary=True)
                    logger.info("Successfully connected to database")
                    return True
            except Error as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to connect after {self.max_retries} attempts")
                    return False
        return False

    def ensure_connection(self):
        """Ensure database connection is alive, reconnect if needed"""
        if not self.connection or not self.connection.is_connected():
            logger.warning("Database connection lost, attempting to reconnect...")
            return self.connect()
        return True

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")

    def begin_transaction(self):
        """Start a new transaction"""
        if self.ensure_connection():
            try:
                self.connection.start_transaction()
                return True
            except Error as e:
                logger.error(f"Failed to start transaction: {e}")
                return False
        return False

    def commit(self):
        """Commit current transaction"""
        if self.connection and self.connection.is_connected():
            try:
                self.connection.commit()
                return True
            except Error as e:
                logger.error(f"Failed to commit transaction: {e}")
                return False
        return False

    def rollback(self):
        """Rollback current transaction"""
        if self.connection and self.connection.is_connected():
            try:
                self.connection.rollback()
                logger.info("Transaction rolled back")
                return True
            except Error as e:
                logger.error(f"Failed to rollback: {e}")
                return False
        return False

    def get_game_settings(self, game_id=2):
        """Get Catch Game settings from database"""
        try:
            if not self.ensure_connection():
                return self.get_default_settings()

            with self.get_connection() as (conn, cursor):
                query = """
                    SELECT cgs.*, g.game_name, g.difficulty, g.time_limit
                    FROM catchgamesettings cgs
                    JOIN game g ON cgs.game_id = g.game_id
                    WHERE cgs.game_id = %s
                """
                cursor.execute(query, (game_id,))
                result = cursor.fetchone()

                if result:
                    return {
                        'target_circles': result.get('target_circles', 5),
                        'target_squares': result.get('target_squares', 5),
                        'target_triangles': result.get('target_triangles', 5),
                        'starting_lives': result.get('starting_lives', 5),
                        'points_per_shape': result.get('points_per_shape', 10),
                        'completion_percentage': result.get('completion_percentage', 100),
                        'fall_speed_min': result.get('fall_speed_min', 4),
                        'fall_speed_max': result.get('fall_speed_max', 7),
                        'spawn_delay': float(result.get('spawn_delay', 2.0)),
                        'basket_speed': result.get('basket_speed', 12),
                        'game_name': result.get('game_name', 'Catch Game'),
                        'difficulty': result.get('difficulty', 'Easy'),
                        'time_limit': result.get('time_limit', 60)
                    }
                else:
                    logger.warning(f"No settings found for game_id {game_id}, using defaults")
                    return self.get_default_settings()
        except Error as e:
            logger.error(f"Error fetching game settings: {e}")
            return self.get_default_settings()

    def get_default_settings(self):
        """Return default game settings"""
        return {
            'target_circles': 5,
            'target_squares': 5,
            'target_triangles': 5,
            'starting_lives': 5,
            'points_per_shape': 10,
            'completion_percentage': 100,
            'fall_speed_min': 4,
            'fall_speed_max': 7,
            'spawn_delay': 2.0,
            'basket_speed': 12,
            'game_name': 'Catch Game',
            'difficulty': 'Easy',
            'time_limit': 60
        }

    def start_game_session(self, student_id: int, game_id: int = 2) -> Optional[int]:
        """
        Start a new game session in the database
        Returns session_id if successful, None otherwise
        """
        if not self.ensure_connection():
            logger.error("Cannot start game session: No database connection")
            return None

        try:
            with self.get_connection() as (conn, cursor):
                # First, verify student exists
                cursor.execute("SELECT student_id FROM student WHERE student_id = %s", (student_id,))
                if not cursor.fetchone():
                    logger.error(f"Student ID {student_id} does not exist in database")
                    return None

                query = """
                    INSERT INTO gamesession (student_id, game_id, score_earned, completion_percentage, status, start_time)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """
                cursor.execute(query, (student_id, game_id, 0, 0, 'failed'))
                session_id = cursor.lastrowid

                if not session_id:
                    logger.error("Failed to create game session: No session ID returned")
                    return None

                logger.info(f"Game session started successfully with ID: {session_id}")
                return session_id

        except Error as e:
            logger.error(f"Error starting game session: {e}")
            return None

    def update_game_session(self, session_id: int, score: int, completion_percentage: int,
                            status: str = 'completed', won: bool = False) -> bool:
        """
        Update game session with final results
        """
        if not self.ensure_connection():
            logger.error("Cannot update game session: No database connection")
            return False

        try:
            with self.get_connection() as (conn, cursor):
                allowed_statuses = ['completed', 'failed', 'quit']
                if status not in allowed_statuses:
                    logger.warning(f"Invalid status '{status}', defaulting to 'failed'")
                    status = 'failed'

                final_status = 'completed' if won else status

                update_query = """
                    UPDATE gamesession 
                    SET score_earned = %s, completion_percentage = %s, status = %s, end_time = NOW()
                    WHERE session_id = %s
                """
                cursor.execute(update_query, (score, completion_percentage, final_status, session_id))

                logger.info(
                    f"Game session {session_id} updated: score={score}, completion={completion_percentage}%, status={final_status}")
                return True

        except Error as e:
            logger.error(f"Error updating game session {session_id}: {e}")
            return False

    def log_game_event(self, session_id: int, event_type: str, event_value: str) -> bool:
        """
        Log game events to gamelog table
        """
        if not session_id:
            logger.warning(f"Cannot log event '{event_type}' - session_id is None")
            return False

        if not self.ensure_connection():
            logger.warning(f"Cannot log event '{event_type}' - no database connection")
            return False

        try:
            with self.get_connection() as (conn, cursor):
                query = """
                    INSERT INTO gamelog (session_id, event_type, event_value, timestamp)
                    VALUES (%s, %s, %s, NOW())
                """
                cursor.execute(query, (session_id, event_type, str(event_value)))
                logger.debug(f"Event logged: {event_type} = {event_value} (session={session_id})")
                return True
        except Error as e:
            logger.error(f"Error logging event (session={session_id}, event={event_type}): {e}")
            return False

    def save_assessment(self, student_id: int, score: int, remarks: str = None) -> bool:
        """
        Save assessment record when game is completed/won
        """
        if not self.ensure_connection():
            logger.error("Cannot save assessment: No database connection")
            return False

        try:
            with self.get_connection() as (conn, cursor):
                # Check if assessment already exists for today
                check_query = """
                    SELECT assessment_id, assessed_at 
                    FROM assessment 
                    WHERE student_id = %s AND assessment_type = 'Post-Test'
                    ORDER BY assessed_at DESC 
                    LIMIT 1
                """
                cursor.execute(check_query, (student_id,))
                existing = cursor.fetchone()

                if existing:
                    from datetime import datetime, timedelta
                    if existing['assessed_at'] and existing['assessed_at'] > datetime.now() - timedelta(hours=1):
                        logger.warning(
                            f"Assessment for student {student_id} already exists in last hour, skipping duplicate")
                        return False

                if remarks is None:
                    remarks = f"Catch Game completed with score {score}"

                insert_query = """
                    INSERT INTO assessment (student_id, assessment_type, assesment_score, remarks, assessed_at)
                    VALUES (%s, 'Post-Test', %s, %s, NOW())
                """
                cursor.execute(insert_query, (student_id, score, remarks))

                logger.info(f"Assessment saved for student {student_id} with score {score}")
                return True

        except Error as e:
            logger.error(f"Error saving assessment for student {student_id}: {e}")
            return False

    def update_student_score(self, student_id: int, additional_score: int) -> bool:
        """
        Update student's total score in student table
        """
        if not self.ensure_connection():
            logger.error("Cannot update student score: No database connection")
            return False

        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("SELECT score FROM student WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()

                if not student:
                    logger.error(f"Student ID {student_id} not found")
                    return False

                new_score = student['score'] + additional_score

                update_query = "UPDATE student SET score = %s WHERE student_id = %s"
                cursor.execute(update_query, (new_score, student_id))

                logger.info(f"Student {student_id} score updated: +{additional_score} (Total: {new_score})")
                return True

        except Error as e:
            logger.error(f"Error updating student score for {student_id}: {e}")
            return False

    def get_student_info(self, student_id: int) -> Optional[Dict]:
        """Get student information"""
        try:
            if not self.ensure_connection():
                return None

            with self.get_connection() as (conn, cursor):
                query = """
                    SELECT s.*, sy.school_year 
                    FROM student s
                    JOIN schoolyear sy ON s.schoolyear_id = sy.schoolyear_id
                    WHERE s.student_id = %s AND s.status = 'Enrolled'
                """
                cursor.execute(query, (student_id,))
                return cursor.fetchone()
        except Error as e:
            logger.error(f"Error fetching student info for {student_id}: {e}")
            return None


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