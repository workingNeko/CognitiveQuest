import pandas as pd
import json
from typing import Dict, List, Any, Optional
from database.db_conn import get_connection
from services.column_mapper import column_mapper


class ExportService:
    """
    Export service that reconstructs original data structure including extra columns
    """

    def __init__(self):
        self.db_fields = list(column_mapper.DB_SCHEMA.keys())

    def export_students(self, include_extra_data: bool = True, include_archived: bool = False) -> pd.DataFrame:
        """
        Export all students with full data reconstruction

        Args:
            include_extra_data: Whether to include extra_data JSON fields
            include_archived: Whether to include archived students (default: False - only enrolled)

        Returns:
            DataFrame with student data
        """
        conn = get_connection()

        try:
            # Query base student data with status filter
            if include_archived:
                query = """
                SELECT 
                    student_id,
                    firstName,
                    lastName,
                    score,
                    progress,
                    level,
                    status,
                    added_on,
                    extra_data
                FROM Student
                ORDER BY student_id
                """
            else:
                query = """
                SELECT 
                    student_id,
                    firstName,
                    lastName,
                    score,
                    progress,
                    level,
                    status,
                    added_on,
                    extra_data
                FROM Student
                WHERE status = 'Enrolled'
                ORDER BY student_id
                """

            df = pd.read_sql(query, conn)

            if df.empty:
                return pd.DataFrame()

            # Reconstruct full data including extra columns
            reconstructed_rows = []

            for _, row in df.iterrows():
                # Base data
                base_record = {
                    "student_id": row["student_id"],
                    "firstName": row["firstName"],
                    "lastName": row["lastName"],
                    "score": row["score"],
                    "progress": row["progress"],
                    "level": row["level"],
                    "status": row["status"],
                    "added_on": row["added_on"]
                }

                # Merge extra data from JSON
                if include_extra_data and row["extra_data"]:
                    try:
                        extra_data = json.loads(row["extra_data"])
                        # Merge extra fields, but don't overwrite base fields
                        for key, value in extra_data.items():
                            if key not in base_record:
                                base_record[key] = value
                    except (json.JSONDecodeError, TypeError):
                        pass

                reconstructed_rows.append(base_record)

            result_df = pd.DataFrame(reconstructed_rows)

            if not result_df.empty:
                # Reorder columns for better readability
                priority_columns = ["student_id", "firstName", "lastName", "score",
                                    "progress", "level", "status", "added_on"]
                existing_priority = [col for col in priority_columns if col in result_df.columns]
                other_columns = [col for col in result_df.columns if col not in priority_columns]

                result_df = result_df[existing_priority + other_columns]

            return result_df

        except Exception as e:
            raise Exception(f"Export error: {str(e)}")
        finally:
            conn.close()

    def export_filtered(self, student_ids: List[int] = None,
                        status: str = None,
                        level: str = None,
                        include_archived: bool = False) -> pd.DataFrame:
        """
        Export filtered students

        Args:
            student_ids: List of student IDs to export
            status: Filter by status (e.g., 'Enrolled', 'Archived')
            level: Filter by level
            include_archived: If True, include archived students in results (default: False)

        Returns:
            DataFrame with filtered student data
        """
        conn = get_connection()

        try:
            query = """
            SELECT 
                student_id,
                firstName,
                lastName,
                score,
                progress,
                level,
                status,
                added_on,
                extra_data
            FROM Student
            WHERE 1=1
            """
            params = []

            # Add status filter
            if not include_archived and status is None:
                query += " AND status = 'Enrolled'"
            elif status:
                query += " AND status = %s"
                params.append(status)
            elif not include_archived:
                query += " AND status = 'Enrolled'"

            if student_ids:
                placeholders = ','.join(['%s'] * len(student_ids))
                query += f" AND student_id IN ({placeholders})"
                params.extend(student_ids)

            if level:
                query += " AND level = %s"
                params.append(level)

            query += " ORDER BY student_id"

            df = pd.read_sql(query, conn, params=params)

            if df.empty:
                return pd.DataFrame()

            # Reconstruct extra data
            reconstructed_rows = []
            for _, row in df.iterrows():
                base_record = {
                    "student_id": row["student_id"],
                    "firstName": row["firstName"],
                    "lastName": row["lastName"],
                    "score": row["score"],
                    "progress": row["progress"],
                    "level": row["level"],
                    "status": row["status"],
                    "added_on": row["added_on"]
                }

                if row["extra_data"]:
                    try:
                        extra_data = json.loads(row["extra_data"])
                        for key, value in extra_data.items():
                            if key not in base_record:
                                base_record[key] = value
                    except:
                        pass

                reconstructed_rows.append(base_record)

            result_df = pd.DataFrame(reconstructed_rows)

            if not result_df.empty:
                # Reorder columns
                priority_columns = ["student_id", "firstName", "lastName", "score",
                                    "progress", "level", "status", "added_on"]
                existing_priority = [col for col in priority_columns if col in result_df.columns]
                other_columns = [col for col in result_df.columns if col not in priority_columns]
                result_df = result_df[existing_priority + other_columns]

            return result_df

        except Exception as e:
            raise Exception(f"Export error: {str(e)}")
        finally:
            conn.close()

    def get_export_preview(self, limit: int = 10, include_archived: bool = False) -> pd.DataFrame:
        """
        Get preview of export data

        Args:
            limit: Number of rows to preview
            include_archived: Whether to include archived students

        Returns:
            DataFrame with preview data
        """
        df = self.export_students(include_archived=include_archived)
        if not df.empty:
            return df.head(limit)
        return df

    def export_archived_students(self, include_extra_data: bool = True) -> pd.DataFrame:
        """
        Export only archived students

        Args:
            include_extra_data: Whether to include extra_data JSON fields

        Returns:
            DataFrame with archived student data
        """
        conn = get_connection()

        try:
            query = """
            SELECT 
                student_id,
                firstName,
                lastName,
                score,
                progress,
                level,
                status,
                added_on,
                extra_data
            FROM Student
            WHERE status = 'Archived'
            ORDER BY student_id
            """

            df = pd.read_sql(query, conn)

            if df.empty:
                return pd.DataFrame()

            # Reconstruct full data including extra columns
            reconstructed_rows = []

            for _, row in df.iterrows():
                # Base data
                base_record = {
                    "student_id": row["student_id"],
                    "firstName": row["firstName"],
                    "lastName": row["lastName"],
                    "score": row["score"],
                    "progress": row["progress"],
                    "level": row["level"],
                    "status": row["status"],
                    "added_on": row["added_on"]
                }

                # Merge extra data from JSON
                if include_extra_data and row["extra_data"]:
                    try:
                        extra_data = json.loads(row["extra_data"])
                        for key, value in extra_data.items():
                            if key not in base_record:
                                base_record[key] = value
                    except (json.JSONDecodeError, TypeError):
                        pass

                reconstructed_rows.append(base_record)

            result_df = pd.DataFrame(reconstructed_rows)

            # Reorder columns for better readability
            priority_columns = ["student_id", "firstName", "lastName", "score",
                                "progress", "level", "status", "added_on"]
            existing_priority = [col for col in priority_columns if col in result_df.columns]
            other_columns = [col for col in result_df.columns if col not in priority_columns]

            if existing_priority:
                result_df = result_df[existing_priority + other_columns]

            return result_df

        except Exception as e:
            raise Exception(f"Export error: {str(e)}")
        finally:
            conn.close()


# Singleton instance
export_service = ExportService()


# Convenience functions
def export_students(include_archived: bool = False) -> pd.DataFrame:
    """Export students (excludes archived by default)"""
    return export_service.export_students(include_archived=include_archived)


def export_archived_students() -> pd.DataFrame:
    """Export only archived students"""
    return export_service.export_archived_students()