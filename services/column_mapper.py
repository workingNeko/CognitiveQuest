import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MatchType(Enum):
    EXACT = "exact"
    CASE_INSENSITIVE = "case_insensitive"
    SIMILAR = "similar"
    PATTERN = "pattern"


@dataclass
class ColumnMapping:
    """Represents a column mapping rule"""
    source_pattern: str
    target_field: str
    match_type: MatchType
    priority: int = 0
    required: bool = False
    default_value: any = None


class ColumnMapper:
    """
    Advanced column mapping system with multiple matching strategies
    """

    # Database schema definition
    DB_SCHEMA = {
        "firstName": {
            "type": "string",
            "required": True,
            "default": "Unknown",
            "aliases": ["firstname", "first_name", "fname", "given_name", "first", "name"]
        },
        "lastName": {
            "type": "string",
            "required": True,
            "default": "Unknown",
            "aliases": ["lastname", "last_name", "lname", "surname", "family_name", "last"]
        },
        "score": {
            "type": "int",
            "required": False,
            "default": 0,
            "aliases": ["score", "points", "total_score", "assessment_score", "grade"]
        },
        "progress": {
            "type": "int",
            "required": False,
            "default": 0,
            "aliases": ["progress", "completion", "progress_percent", "completion_rate"]
        },
        "level": {
            "type": "string",
            "required": False,
            "default": "Level 1",
            "aliases": ["level", "grade_level", "class_level", "student_level"]
        },
        "status": {
            "type": "string",
            "required": False,
            "default": "Enrolled",
            "aliases": ["status", "enrollment_status", "student_status", "active_status"]
        }
    }

    # Fuzzy matching patterns for common variations
    PATTERNS = {
        "firstName": r"(first|given|fname|first_?name)",
        "lastName": r"(last|surname|lname|family|last_?name)",
        "score": r"(score|points|total|grade|assessment)",
        "progress": r"(progress|completion|percent|rate)",
        "level": r"(level|grade|class)",
        "status": r"(status|enrollment|active)"
    }

    def __init__(self):
        self.mapping_rules = self._build_mapping_rules()

    def _build_mapping_rules(self) -> List[ColumnMapping]:
        """Build mapping rules from schema"""
        rules = []
        priority = 0

        for field, schema in self.DB_SCHEMA.items():
            # Exact match rule (highest priority)
            rules.append(ColumnMapping(
                source_pattern=field,
                target_field=field,
                match_type=MatchType.EXACT,
                priority=priority,
                required=schema["required"],
                default_value=schema["default"]
            ))
            priority += 1

            # Case insensitive rule
            rules.append(ColumnMapping(
                source_pattern=field,
                target_field=field,
                match_type=MatchType.CASE_INSENSITIVE,
                priority=priority,
                required=schema["required"],
                default_value=schema["default"]
            ))
            priority += 1

            # Aliases
            for alias in schema.get("aliases", []):
                rules.append(ColumnMapping(
                    source_pattern=alias,
                    target_field=field,
                    match_type=MatchType.EXACT,
                    priority=priority,
                    required=False,
                    default_value=schema["default"]
                ))
                priority += 1

            # Pattern matching rule
            if field in self.PATTERNS:
                rules.append(ColumnMapping(
                    source_pattern=self.PATTERNS[field],
                    target_field=field,
                    match_type=MatchType.PATTERN,
                    priority=priority,
                    required=False,
                    default_value=schema["default"]
                ))
                priority += 1

        return rules

    def normalize_column_name(self, col_name: str) -> str:
        """Normalize column name for matching"""
        # Convert to lowercase
        normalized = col_name.lower().strip()
        # Remove special characters and spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)
        return normalized

    def match_column(self, source_col: str) -> Tuple[Optional[str], float]:
        """
        Match a source column to a database field with confidence score
        Returns (target_field, confidence_score)
        """
        best_match = None
        best_confidence = 0.0

        for rule in self.mapping_rules:
            confidence = self._calculate_confidence(source_col, rule)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = rule.target_field

        # Only return match if confidence is above threshold
        threshold = 0.6
        if best_confidence >= threshold:
            return best_match, best_confidence

        return None, 0.0

    def _calculate_confidence(self, source_col: str, rule: ColumnMapping) -> float:
        """Calculate confidence score for a mapping rule"""
        source_normalized = self.normalize_column_name(source_col)
        pattern_normalized = self.normalize_column_name(rule.source_pattern)

        if rule.match_type == MatchType.EXACT:
            return 1.0 if source_normalized == pattern_normalized else 0.0

        elif rule.match_type == MatchType.CASE_INSENSITIVE:
            return 0.95 if source_normalized == pattern_normalized else 0.0

        elif rule.match_type == MatchType.PATTERN:
            match = re.search(rule.source_pattern, source_normalized, re.IGNORECASE)
            return 0.85 if match else 0.0

        return 0.0

    def map_columns(self, df_columns: List[str]) -> Dict[str, str]:
        """
        Map all DataFrame columns to database fields
        Returns mapping of {source_column: target_field}
        """
        mapping = {}
        used_fields = set()
        confidence_scores = {}

        # First pass: match all columns
        for col in df_columns:
            target_field, confidence = self.match_column(col)
            if target_field:
                mapping[col] = target_field
                confidence_scores[col] = confidence

        # Second pass: resolve conflicts (multiple columns mapping to same field)
        field_columns = {}
        for col, target in mapping.items():
            if target not in field_columns:
                field_columns[target] = []
            field_columns[target].append((col, confidence_scores[col]))

        resolved_mapping = {}
        for target, columns in field_columns.items():
            # Keep the column with highest confidence
            best_col = max(columns, key=lambda x: x[1])[0]
            resolved_mapping[best_col] = target

        return resolved_mapping

    def get_required_fields(self) -> List[str]:
        """Get list of required fields"""
        return [field for field, schema in self.DB_SCHEMA.items()
                if schema.get("required", False)]

    def get_default_value(self, field: str) -> any:
        """Get default value for a field"""
        if field in self.DB_SCHEMA:
            return self.DB_SCHEMA[field].get("default")
        return None

    def get_field_type(self, field: str) -> str:
        """Get the data type for a field"""
        if field in self.DB_SCHEMA:
            return self.DB_SCHEMA[field].get("type", "string")
        return "string"


# Singleton instance
column_mapper = ColumnMapper()


def map_columns(df_columns: List[str]) -> Dict[str, str]:
    """Convenience function for column mapping"""
    return column_mapper.map_columns(df_columns)


def normalize_column(column_name: str) -> str:
    """Normalize column name for display"""
    return column_mapper.normalize_column_name(column_name)