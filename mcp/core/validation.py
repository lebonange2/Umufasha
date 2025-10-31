"""JSON Schema validation for MCP messages."""
from typing import Any, Dict, Optional
import jsonschema
from jsonschema import validate, ValidationError

from mcp.core.protocol.messages import JSONRPCError, JSONRPCErrorCode


class SchemaValidator:
    """JSON Schema validator."""
    
    def __init__(self):
        self.schemas: Dict[str, Dict[str, Any]] = {}
    
    def register_schema(self, name: str, schema: Dict[str, Any]):
        """Register a JSON schema."""
        self.schemas[name] = schema
    
    def validate(
        self,
        instance: Any,
        schema_name: str,
        allow_additional_properties: bool = False
    ) -> Optional[JSONRPCError]:
        """Validate instance against a registered schema.
        
        Args:
            instance: Data to validate
            schema_name: Name of registered schema
            allow_additional_properties: If True, ignore extra properties
            
        Returns:
            JSONRPCError if validation fails, None otherwise
        """
        if schema_name not in self.schemas:
            return JSONRPCError(
                code=JSONRPCErrorCode.INTERNAL_ERROR,
                message=f"Schema '{schema_name}' not found"
            )
        
        schema = self.schemas[schema_name].copy()
        if allow_additional_properties and "additionalProperties" not in schema:
            # Wrap in allOf to add additionalProperties
            schema = {
                "allOf": [schema, {"additionalProperties": allow_additional_properties}]
            }
        
        try:
            validate(instance=instance, schema=schema)
            return None
        except ValidationError as e:
            error_path = ".".join(str(p) for p in e.path) if e.path else "root"
            return JSONRPCError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message=f"Validation error at {error_path}: {e.message}",
                data={
                    "path": list(e.path),
                    "schema_path": list(e.schema_path),
                    "validator": e.validator,
                    "validator_value": e.validator_value
                }
            )


# Common JSON schemas for MCP
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "properties": {"type": "object"},
                "required": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["type"]
        }
    },
    "required": ["name", "description", "inputSchema"]
}

RESOURCE_SCHEMA = {
    "type": "object",
    "properties": {
        "uri": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "mimeType": {"type": "string"}
    },
    "required": ["uri", "name"]
}

PROMPT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "arguments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "required": {"type": "boolean"}
                },
                "required": ["name", "description"]
            }
        }
    },
    "required": ["name", "description"]
}

