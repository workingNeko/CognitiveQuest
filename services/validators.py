import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationRule:
    field: str
    rule_type: str
    params: Dict[str, Any]
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


class StudentValidator:
    """
    Comprehensive validator for student data
    """

    def __init__(self):
        self.rules = self._build_validation_rules()

    def _build_validation_rules(self) -> List[ValidationRule]:
        """Build validation rules for student data"""
        return [
            ValidationRule(
                field="firstName",
                rule_type="required",
                params={},
                message="First name is required"
            ),
            ValidationRule(
                field="firstName",
                rule_type="min_length",
                params={"min": 1},
                message="First name must be at least 1 character"
            ),
            ValidationRule(
                field="firstName",
                rule_type="max_length",
                params={"max": 50},
                message="First name cannot exceed 50 characters"
            ),
            ValidationRule(
                field="lastName",
                rule_type="required",
                params={},
                message="Last name is required"
            ),
            ValidationRule(
                field="lastName",
                rule_type="max_length",
                params={"max": 50},
                message="Last name cannot exceed 50 characters"
            ),
            ValidationRule(
                field="score",
                rule_type="range",
                params={"min": 0, "max": 100},
                message="Score must be between 0 and 100"
            ),
            ValidationRule(
                field="progress",
                rule_type="range",
                params={"min": 0, "max": 100},
                message="Progress must be between 0 and 100"
            ),
            ValidationRule(
                field="level",
                rule_type="pattern",
                params={"pattern": r"^Level\s*\d+$|^Bonus$"},
                message="Level must be 'Level X' (e.g., Level 1) or 'Bonus'"
            ),
            ValidationRule(
                field="status",
                rule_type="in_list",
                params={"allowed": ["Enrolled", "Unenrolled"]},
                message="Status must be 'Enrolled' or 'Unenrolled'"
            )
        ]

    def validate_record(self, record: Dict) -> Tuple[bool, List[Dict]]:
        """
        Validate a single student record
        Returns (is_valid, list_of_errors)
        """
        errors = []

        for rule in self.rules:
            value = record.get(rule.field)
            is_valid = self._apply_rule(value, rule)

            if not is_valid:
                errors.append({
                    "field": rule.field,
                    "message": rule.message,
                    "severity": rule.severity.value
                })

        return len(errors) == 0, errors

    def _apply_rule(self, value: any, rule: ValidationRule) -> bool:
        """Apply a specific validation rule"""

        if rule.rule_type == "required":
            return value is not None and str(value).strip() != ""

        elif rule.rule_type == "min_length":
            return len(str(value)) >= rule.params.get("min", 0)

        elif rule.rule_type == "max_length":
            return len(str(value)) <= rule.params.get("max", float('inf'))

        elif rule.rule_type == "range":
            try:
                num_value = float(value)
                return (rule.params.get("min", float('-inf')) <= num_value <=
                        rule.params.get("max", float('inf')))
            except (ValueError, TypeError):
                return False

        elif rule.rule_type == "pattern":
            pattern = rule.params.get("pattern", "")
            return re.match(pattern, str(value)) is not None

        elif rule.rule_type == "in_list":
            allowed = rule.params.get("allowed", [])
            return value in allowed

        return True

    def validate_batch(self, records: List[Dict]) -> Dict:
        """
        Validate multiple records and return summary
        """
        results = {
            "total": len(records),
            "valid": 0,
            "invalid": 0,
            "errors_by_field": {},
            "records_with_errors": []
        }

        for idx, record in enumerate(records):
            is_valid, errors = self.validate_record(record)

            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["records_with_errors"].append({
                    "index": idx,
                    "record": record,
                    "errors": errors
                })

                for error in errors:
                    field = error["field"]
                    if field not in results["errors_by_field"]:
                        results["errors_by_field"][field] = []
                    results["errors_by_field"][field].append(error["message"])

        return results