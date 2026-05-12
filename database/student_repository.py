import json
from typing import List, Dict, Optional
from database.db_conn import db
import mysql.connector
from datetime import datetime


class StudentRepository:
    """
    Repository for student database operations
    """

    def __init__(self):
        self.table = "student"  # Changed to lowercase to match schema

    def insert_students(self, students: List[Dict], mode: str = "Append", school_year: str = None) -> int:
        """
        Insert students into database

        Args:
            students: List of student dictionaries
            mode: "Append" or "Replace"
                - Append: Just add new students
                - Replace: Archive existing students for the specific school year and insert new batch
            school_year: School year for the students (required for Replace mode)

        Returns:
            Number of records inserted
        """
        if not students:
            return 0

        with db.get_connection() as (conn, cursor):
            if mode == "Replace" and school_year:
                # Archive only students from the selected school year
                self._archive_students_by_schoolyear(cursor, school_year)

            # Prepare insert query with schoolyear_id
            query = """
            INSERT INTO student 
            (firstName, lastName, score, progress, level, status, schoolyear_id, extra_data)
            VALUES (%(firstName)s, %(lastName)s, %(score)s, %(progress)s, 
                    %(level)s, %(status)s, %(schoolyear_id)s, %(extra_data)s)
            """

            # Process students to handle school year and extra_data
            processed_students = []
            for student in students:
                # Handle school year - prioritize passed school_year parameter
                if 'school_year' in student:
                    schoolyear_id = self._get_or_create_schoolyear(cursor, student['school_year'])
                    student['schoolyear_id'] = schoolyear_id
                elif school_year:  # Use the parameter if provided
                    schoolyear_id = self._get_or_create_schoolyear(cursor, school_year)
                    student['schoolyear_id'] = schoolyear_id
                elif 'schoolyear_id' not in student:
                    # Get active school year
                    schoolyear_id = self._get_active_schoolyear(cursor)
                    if schoolyear_id is None:
                        # Create a default school year if none exists
                        schoolyear_id = self._get_or_create_schoolyear(cursor, "2024-2025")
                    student['schoolyear_id'] = schoolyear_id

                # Handle extra_data JSON
                if 'extra_data' in student and student['extra_data']:
                    if isinstance(student['extra_data'], dict):
                        student['extra_data'] = json.dumps(student['extra_data'])
                else:
                    student['extra_data'] = None

                # Set default status if not provided
                if 'status' not in student:
                    student['status'] = 'Enrolled'

                processed_students.append(student)

            # Execute batch insert
            cursor.executemany(query, processed_students)
            conn.commit()

            return len(processed_students)

    def _archive_students_by_schoolyear(self, cursor, school_year: str) -> int:
        """
        Archive all students from a specific school year

        Args:
            cursor: Database cursor
            school_year: School year string

        Returns:
            Number of students archived
        """
        # Get schoolyear_id
        cursor.execute(
            "SELECT schoolyear_id FROM schoolyear WHERE school_year = %s",
            (school_year,)
        )
        result = cursor.fetchone()

        if not result:
            return 0

        schoolyear_id = result[0] if not isinstance(result, dict) else result['schoolyear_id']

        # Archive students from that school year
        query = """
        UPDATE student 
        SET status = 'Archived',
            extra_data = JSON_SET(
                COALESCE(extra_data, '{}'),
                '$.archived_date', %s,
                '$.previous_status', status,
                '$.archived_from_schoolyear', %s
            )
        WHERE schoolyear_id = %s AND status = 'Enrolled'
        """

        cursor.execute(query, (datetime.now().isoformat(), school_year, schoolyear_id))
        return cursor.rowcount

    def _archive_all_students(self, cursor) -> int:
        """
        Archive all currently enrolled students (used for old functionality)

        Args:
            cursor: Database cursor

        Returns:
            Number of students archived
        """
        # Update all enrolled students to Archived status
        query = """
        UPDATE student 
        SET status = 'Archived',
            extra_data = JSON_SET(
                COALESCE(extra_data, '{}'),
                '$.archived_date', %s,
                '$.previous_status', status
            )
        WHERE status = 'Enrolled'
        """

        cursor.execute(query, (datetime.now().isoformat(),))
        return cursor.rowcount

    def _get_or_create_schoolyear(self, cursor, school_year_str: str) -> int:
        """
        Get existing school year ID or create a new one

        Args:
            cursor: Database cursor
            school_year_str: School year string (e.g., "2024-2025")

        Returns:
            schoolyear_id
        """
        # Check if school year exists
        cursor.execute(
            "SELECT schoolyear_id FROM schoolyear WHERE school_year = %s",
            (school_year_str,)
        )

        result = cursor.fetchone()

        if result:
            return result[0] if not isinstance(result, dict) else result['schoolyear_id']
        else:
            # Create new school year
            cursor.execute(
                "INSERT INTO schoolyear (school_year, is_active) VALUES (%s, %s)",
                (school_year_str, 0)
            )
            return cursor.lastrowid

    def _get_active_schoolyear(self, cursor) -> Optional[int]:
        """
        Get the currently active school year ID

        Args:
            cursor: Database cursor

        Returns:
            schoolyear_id or None if no active school year
        """
        cursor.execute(
            "SELECT schoolyear_id FROM schoolyear WHERE is_active = 1 LIMIT 1"
        )
        result = cursor.fetchone()

        if result:
            return result[0] if not isinstance(result, dict) else result['schoolyear_id']
        return None

    def get_all_students(self, include_archived: bool = False) -> List[Dict]:
        """
        Get all students with decoded extra_data

        Args:
            include_archived: If True, includes archived students; if False, only enrolled
        """
        with db.get_connection() as (conn, cursor):
            if include_archived:
                status_filter = ""
            else:
                status_filter = "WHERE s.status = 'Enrolled'"

            cursor.execute(f"""
                SELECT s.student_id, s.firstName, s.lastName, s.score, s.progress, 
                       s.level, s.status, s.added_on, s.extra_data, s.schoolyear_id,
                       sy.school_year
                FROM student s
                LEFT JOIN schoolyear sy ON s.schoolyear_id = sy.schoolyear_id
                {status_filter}
                ORDER BY s.student_id
            """)
            results = cursor.fetchall()

            # Parse extra_data JSON
            for row in results:
                if row.get("extra_data"):
                    try:
                        row["extra_data"] = json.loads(row["extra_data"])
                    except:
                        row["extra_data"] = {}
                else:
                    row["extra_data"] = {}

                # Add school_year field for convenience
                if row.get("school_year"):
                    row["school_year"] = row["school_year"]

            return results

    def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get student by ID"""
        with db.get_connection() as (conn, cursor):
            cursor.execute("""
                SELECT s.*, sy.school_year
                FROM student s
                LEFT JOIN schoolyear sy ON s.schoolyear_id = sy.schoolyear_id
                WHERE s.student_id = %s
            """, (student_id,))
            result = cursor.fetchone()

            if result and result.get("extra_data"):
                try:
                    result["extra_data"] = json.loads(result["extra_data"])
                except:
                    result["extra_data"] = {}

            return result

    def update_student(self, student_id: int, updates: Dict) -> bool:
        """Update a single student"""
        with db.get_connection() as (conn, cursor):
            # Handle school_year to schoolyear_id conversion
            if 'school_year' in updates:
                schoolyear_id = self._get_or_create_schoolyear(cursor, updates['school_year'])
                updates['schoolyear_id'] = schoolyear_id
                del updates['school_year']

            # Handle extra_data JSON conversion
            if 'extra_data' in updates and updates['extra_data']:
                if isinstance(updates['extra_data'], dict):
                    updates['extra_data'] = json.dumps(updates['extra_data'])

            # Build dynamic update query
            set_clause = ", ".join([f"{key} = %s" for key in updates.keys() if key != "student_id"])
            values = [updates[key] for key in updates.keys() if key != "student_id"]
            values.append(student_id)

            query = f"UPDATE {self.table} SET {set_clause} WHERE student_id = %s"
            cursor.execute(query, values)
            conn.commit()

            return cursor.rowcount > 0

    def delete_student(self, student_id: int) -> bool:
        """Delete a student (soft delete by archiving)"""
        with db.get_connection() as (conn, cursor):
            cursor.execute("""
                UPDATE student 
                SET status = 'Archived',
                    extra_data = JSON_SET(
                        COALESCE(extra_data, '{}'),
                        '$.archived_date', %s
                    )
                WHERE student_id = %s
            """, (datetime.now().isoformat(), student_id))
            conn.commit()
            return cursor.rowcount > 0

    def restore_student(self, student_id: int) -> bool:
        """Restore an archived student back to Enrolled status"""
        with db.get_connection() as (conn, cursor):
            cursor.execute("""
                UPDATE student 
                SET status = 'Enrolled',
                    extra_data = JSON_REMOVE(extra_data, '$.archived_date', '$.previous_status')
                WHERE student_id = %s
            """, (student_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_student_count(self, include_archived: bool = False) -> int:
        """Get total number of students"""
        with db.get_connection() as (conn, cursor):
            if include_archived:
                cursor.execute(f"SELECT COUNT(*) as count FROM {self.table}")
            else:
                cursor.execute(f"SELECT COUNT(*) as count FROM {self.table} WHERE status = 'Enrolled'")
            result = cursor.fetchone()
            return result["count"] if result else 0

    def get_statistics(self) -> Dict:
        """Get student statistics"""
        with db.get_connection() as (conn, cursor):
            # Get enrolled students statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_students,
                    AVG(score) as avg_score,
                    AVG(progress) as avg_progress,
                    MIN(score) as min_score,
                    MAX(score) as max_score
                FROM student
                WHERE status = 'Enrolled'
            """)
            stats = cursor.fetchone()

            # Get counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM student
                GROUP BY status
            """)
            status_counts = cursor.fetchall()

            # Get level distribution for enrolled students
            cursor.execute("""
                SELECT level, COUNT(*) as count
                FROM student
                WHERE status = 'Enrolled' AND level IS NOT NULL
                GROUP BY level
                ORDER BY level
            """)
            level_dist = cursor.fetchall()

            # Get school year distribution
            cursor.execute("""
                SELECT sy.school_year, COUNT(*) as count
                FROM student s
                LEFT JOIN schoolyear sy ON s.schoolyear_id = sy.schoolyear_id
                WHERE s.status = 'Enrolled'
                GROUP BY sy.school_year
                ORDER BY sy.school_year DESC
            """)
            schoolyear_dist = cursor.fetchall()

            # Get archived count
            cursor.execute("""
                SELECT COUNT(*) as archived_count
                FROM student
                WHERE status = 'Archived'
            """)
            archived_result = cursor.fetchone()

            return {
                "total_students": stats["total_students"] or 0,
                "avg_score": round(stats["avg_score"] or 0, 2),
                "avg_progress": round(stats["avg_progress"] or 0, 2),
                "min_score": stats["min_score"] or 0,
                "max_score": stats["max_score"] or 0,
                "status_counts": status_counts,
                "level_distribution": level_dist,
                "schoolyear_distribution": schoolyear_dist,
                "archived_count": archived_result["archived_count"] if archived_result else 0
            }

    def archive_by_schoolyear(self, school_year: str) -> int:
        """
        Archive all students from a specific school year

        Args:
            school_year: School year string

        Returns:
            Number of students archived
        """
        with db.get_connection() as (conn, cursor):
            return self._archive_students_by_schoolyear(cursor, school_year)

    def archive_students(self, school_year: str) -> int:
        """
        Archive all students from a specific school year
        (Alias for archive_by_schoolyear for compatibility)

        Args:
            school_year: School year string

        Returns:
            Number of students archived
        """
        return self.archive_by_schoolyear(school_year)


# Singleton instance
student_repo = StudentRepository()


# Convenience functions
def insert_students(students: List[Dict], mode: str = "Append", school_year: str = None) -> int:
    return student_repo.insert_students(students, mode, school_year)


def get_all_students(include_archived: bool = False) -> List[Dict]:
    return student_repo.get_all_students(include_archived)


def get_student_count(include_archived: bool = False) -> int:
    return student_repo.get_student_count(include_archived)


def get_statistics() -> Dict:
    return student_repo.get_statistics()


def archive_by_schoolyear(school_year: str) -> int:
    return student_repo.archive_by_schoolyear(school_year)


def restore_student(student_id: int) -> bool:
    return student_repo.restore_student(student_id)


def delete_student(student_id: int) -> bool:
    return student_repo.delete_student(student_id)


def update_student(student_id: int, updates: Dict) -> bool:
    return student_repo.update_student(student_id, updates)


def get_student_by_id(student_id: int) -> Optional[Dict]:
    return student_repo.get_student_by_id(student_id)