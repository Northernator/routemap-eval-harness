"""Sound minimal JSON schema/constraint checker v1."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from dr_checker_framework_v1 import CheckResult
from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG


class JsonSchemaChecker:
    name = "json_schema_constraints_v1"

    def applies_to(self, claim: Mapping[str, Any]) -> bool:
        return claim.get("type") == "json_schema" and "output" in claim and "schema" in claim

    def check(self, claim: Mapping[str, Any]) -> CheckResult:
        output = claim["output"]
        if isinstance(output, str):
            try:
                value = json.loads(output)
            except json.JSONDecodeError as exc:
                return CheckResult(
                    RULED_OUT_WRONG,
                    f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}",
                    self.name,
                    self.coverage(),
                )
        else:
            value = output
        errors = validate_value(value, claim["schema"], "$")
        if errors:
            return CheckResult(RULED_OUT_WRONG, errors[0], self.name, self.coverage())
        return CheckResult(
            NOT_RULED_OUT,
            "JSON satisfies declared structural constraints; semantic truth is not proven",
            self.name,
            self.coverage(),
        )

    def coverage(self) -> str:
        return (
            "Catches invalid JSON and declared type/required/enum/range violations; "
            "cannot catch schema-valid but semantically wrong values."
        )

    def blind_spot_example(self) -> str:
        return '{"answer": 42, "units": "meters"} can satisfy a schema even when the real answer is 43 meters.'


def validate_value(value: Any, schema: Mapping[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None and not type_matches(value, expected_type):
        errors.append(f"{path} expected {expected_type}, got {json_type_name(value)}")
        return errors
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path} value {value!r} not in enum {schema['enum']!r}")
        return errors
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path} missing required key {key!r}")
                return errors
        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(validate_value(value[key], child_schema, f"{path}.{key}"))
                if errors:
                    return errors
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in value:
                if key not in allowed:
                    errors.append(f"{path} unexpected key {key!r}")
                    return errors
    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            errors.append(f"{path} has fewer than minItems={schema['minItems']}")
            return errors
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            errors.append(f"{path} has more than maxItems={schema['maxItems']}")
            return errors
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(validate_value(item, schema["items"], f"{path}[{index}]"))
                if errors:
                    return errors
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path} below minimum {schema['minimum']}")
            return errors
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path} above maximum {schema['maximum']}")
            return errors
    return errors


def type_matches(value: Any, expected_type: str | list[str]) -> bool:
    if isinstance(expected_type, list):
        return any(type_matches(value, item) for item in expected_type)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {expected_type!r}")


def json_type_name(value: Any) -> str:
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return type(value).__name__
