import pandas as pd
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import streamlit as st

from services.column_mapper import column_mapper
from services.validators import StudentValidator


class ImportService:
    """
    Flexible import service for student data with full data preservation
    """

    ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self.validator = StudentValidator()

    def read_uploaded_file(self, uploaded_file) -> pd.DataFrame:
        """
        Read CSV or Excel file with error handling
        """
        if uploaded_file is None:
            raise ValueError("No file provided")

        # Check file size
        if uploaded_file.size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Max size: {self.MAX_FILE_SIZE / 1024 / 1024:.0f}MB")

        file_name = uploaded_file.name.lower()

        try:
            if file_name.endswith('.csv'):
                # Try different encodings for CSV
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not decode CSV file with any supported encoding")

            elif file_name.endswith(('.xlsx', '.xls')):
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            else:
                raise ValueError(f"Unsupported file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}")

            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]

            if df.empty:
                raise ValueError("File is empty")

            return df

        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")

    def detect_headers(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Detect and categorize headers in the uploaded file
        """
        analysis = {
            "matched_columns": {},
            "unmatched_columns": [],
            "potential_matches": []
        }

        for col in df.columns:
            target_field, confidence = column_mapper.match_column(col)

            if target_field and confidence >= 0.7:
                analysis["matched_columns"][col] = {
                    "target": target_field,
                    "confidence": confidence
                }
            else:
                analysis["unmatched_columns"].append(col)
                # Find potential matches with lower confidence
                for field in column_mapper.DB_SCHEMA.keys():
                    _, conf = column_mapper.match_column(col + "_" + field)
                    if conf > 0.3:
                        analysis["potential_matches"].append({
                            "source": col,
                            "suggested": field,
                            "confidence": conf
                        })

        return analysis

    def process_student_import(self, df: pd.DataFrame, mode: str = "Append") -> Tuple[List[Dict], Dict]:
        """
        Process imported data with flexible column mapping and full data preservation

        Args:
            df: DataFrame to process
            mode: "Append" or "Replace"

        Returns:
            Tuple of (processed_rows, import_summary)
        """
        original_columns = list(df.columns)

        # Step 1: Map columns to database fields
        column_mapping = column_mapper.map_columns(df.columns)

        # Step 2: Create a working copy
        working_df = df.copy()

        # Step 3: Rename columns based on mapping
        rename_dict = {}
        for source_col, target_field in column_mapping.items():
            if source_col in working_df.columns:
                rename_dict[source_col] = target_field

        if rename_dict:
            working_df.rename(columns=rename_dict, inplace=True)

        # Step 4: Ensure all required columns exist with defaults
        # Check for first name (required)
        if 'firstName' not in working_df.columns:
            # Try to find any name column
            name_cols = [col for col in working_df.columns if 'name' in col.lower()]
            if name_cols:
                working_df['firstName'] = working_df[name_cols[0]]
            else:
                working_df['firstName'] = 'Unknown'

        # Check for last name (required)
        if 'lastName' not in working_df.columns:
            working_df['lastName'] = ''

        # Check for score (optional)
        if 'score' not in working_df.columns:
            working_df['score'] = 0
        else:
            working_df['score'] = pd.to_numeric(working_df['score'], errors='coerce').fillna(0).astype(int)

        # Check for progress (optional)
        if 'progress' not in working_df.columns:
            working_df['progress'] = 0
        else:
            working_df['progress'] = pd.to_numeric(working_df['progress'], errors='coerce').fillna(0).astype(int)

        # Check for level (optional)
        if 'level' not in working_df.columns:
            working_df['level'] = 'Level 1'
        else:
            working_df['level'] = working_df['level'].fillna('Level 1').astype(str)

        # Check for status (optional)
        if 'status' not in working_df.columns:
            working_df['status'] = 'Enrolled'
        else:
            working_df['status'] = working_df['status'].fillna('Enrolled').astype(str)

        # Step 5: Process each row
        processed_rows = []
        skipped_rows = []
        validation_errors = []

        # Identify extra columns (not in database schema and not mapped)
        db_fields = {'firstName', 'lastName', 'score', 'progress', 'level', 'status'}
        mapped_source_cols = set(column_mapping.keys())
        extra_columns = [col for col in original_columns if col not in mapped_source_cols]

        for idx in range(len(working_df)):
            try:
                row = working_df.iloc[idx]

                # Extract extra data from original columns
                extra_data = {}
                for col in extra_columns:
                    if col in df.columns:
                        value = df.iloc[idx][col] if col in df.columns else None
                        if pd.notna(value) and value != '':
                            # Convert non-serializable types
                            if isinstance(value, (pd.Timestamp, datetime)):
                                value = value.isoformat()
                            elif isinstance(value, (pd.Series, pd.DataFrame)):
                                value = value.tolist()
                            extra_data[col] = str(value)

                # Handle firstName
                firstName = row.get('firstName', 'Unknown')
                if pd.isna(firstName) or str(firstName).strip() == '':
                    firstName = 'Unknown'
                else:
                    firstName = str(firstName).strip()

                # Handle lastName
                lastName = row.get('lastName', '')
                if pd.isna(lastName):
                    lastName = ''
                else:
                    lastName = str(lastName).strip()

                # If lastName is empty, try to split firstName
                if lastName == '' and ' ' in firstName:
                    name_parts = firstName.split(' ', 1)
                    firstName = name_parts[0]
                    lastName = name_parts[1] if len(name_parts) > 1 else ''

                # Build student record
                student_record = {
                    "firstName": firstName,
                    "lastName": lastName if lastName else 'Unknown',
                    "score": int(row.get('score', 0)),
                    "progress": int(row.get('progress', 0)),
                    "level": str(row.get('level', 'Level 1')).strip(),
                    "status": str(row.get('status', 'Enrolled')).strip(),
                    "extra_data": json.dumps(extra_data, default=str) if extra_data else None
                }

                # Validate record
                is_valid, errors = self.validator.validate_record(student_record)

                # Override validation for lastName if it's just 'Unknown'
                if not is_valid and len(errors) == 1 and errors[0].get('field') == 'lastName':
                    if student_record['lastName'] == 'Unknown':
                        is_valid = True
                        errors = []

                if is_valid:
                    processed_rows.append(student_record)
                else:
                    validation_errors.append({
                        "row": idx + 1,
                        "errors": errors,
                        "data": student_record
                    })
                    skipped_rows.append(idx)

            except Exception as e:
                validation_errors.append({
                    "row": idx + 1,
                    "errors": [f"Processing error: {str(e)}"],
                    "data": {}
                })
                skipped_rows.append(idx)

        # If no rows were processed but we have data, try a more aggressive approach
        if len(processed_rows) == 0 and len(df) > 0:
            # Fallback: try to extract from any columns available
            for idx in range(len(df)):
                try:
                    row = df.iloc[idx]
                    student_record = {
                        "firstName": "Student",
                        "lastName": str(idx + 1),
                        "score": 0,
                        "progress": 0,
                        "level": "Level 1",
                        "status": "Enrolled",
                        "extra_data": None
                    }

                    # Try to find name from any column
                    for col in df.columns:
                        value = row.get(col)
                        if pd.notna(value) and str(value).strip():
                            if any(name_indicator in col.lower() for name_indicator in ['name', 'student', 'first']):
                                student_record['firstName'] = str(value).strip()
                                break

                    extra_data = {}
                    for col in df.columns:
                        value = row.get(col)
                        if pd.notna(value) and str(value).strip():
                            if col.lower() not in ['firstname', 'lastname', 'first_name', 'last_name', 'name']:
                                extra_data[col] = str(value)

                    if extra_data:
                        student_record['extra_data'] = json.dumps(extra_data, default=str)

                    processed_rows.append(student_record)

                except Exception as e:
                    validation_errors.append({
                        "row": idx + 1,
                        "errors": [f"Fallback processing error: {str(e)}"],
                        "data": {}
                    })

        # Generate import summary
        summary = {
            "total_rows": len(df),
            "processed_rows": len(processed_rows),
            "skipped_rows": len(skipped_rows),
            "extra_columns_found": extra_columns,
            "column_mapping_used": column_mapping,
            "validation_errors": validation_errors,
            "original_columns": original_columns,
            "mapped_columns": list(column_mapping.keys())
        }

        return processed_rows, summary

    def preview_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Generate preview of how data will be imported
        """
        preview = df.copy()

        # Show detected column mapping
        mapping = column_mapper.map_columns(df.columns)

        # Add mapping info to preview
        mapping_info = {}
        for col in preview.columns:
            if col in mapping:
                mapping_info[col] = f"→ {mapping[col]}"
            else:
                mapping_info[col] = "→ (extra data)"

        # Create preview with first 5 rows
        preview_display = preview.head(10).copy()

        return preview_display, mapping_info


# Singleton instance
import_service = ImportService()


# Convenience functions for backward compatibility
def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    return import_service.read_uploaded_file(uploaded_file)


def process_student_import(df: pd.DataFrame, mode: str = "Append") -> Tuple[List[Dict], Dict]:
    """Process student import and return processed rows and summary"""
    return import_service.process_student_import(df, mode)


def preview_import_data(df: pd.DataFrame):
    return import_service.preview_data(df)


def detect_headers(df: pd.DataFrame):
    """Detect headers and return analysis"""
    return import_service.detect_headers(df)