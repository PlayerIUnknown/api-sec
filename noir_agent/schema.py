"""JSON schema shared with the Groq LLM."""

API_COLLECTION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ApiCollection",
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "version", "baseUrl", "endpoints"],
    "properties": {
        "title": {"type": "string"},
        "version": {"type": "string"},
        "baseUrl": {"type": "string", "minLength": 1},
        "endpoints": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "method",
                    "path",
                    "summary",
                    "description",
                    "pathParams",
                    "queryParams",
                    "headers",
                    "responses",
                    "source"
                ],
                "properties": {
                    "method": {"type": "string"},
                    "path": {"type": "string"},
                    "summary": {"type": "string"},
                    "description": {"type": "string"},
                    "pathParams": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/ApiParam"}
                    },
                    "queryParams": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/ApiParam"}
                    },
                    "headers": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/ApiParam"}
                    },
                    "requestBody": {
                        "type": ["object", "null"],
                        "additionalProperties": True
                    },
                    "responses": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/ApiResponse"},
                        "minItems": 1
                    },
                    "source": {
                        "type": "object",
                        "additionalProperties": True
                    }
                }
            }
        }
    },
    "definitions": {
        "ApiParam": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "in", "required"],
            "properties": {
                "name": {"type": "string"},
                "in": {
                    "type": "string",
                    "enum": ["path", "query", "header"]
                },
                "required": {"type": "boolean"},
                "type": {"type": "string", "default": "string"},
                "description": {"type": "string", "default": ""}
            }
        },
        "ApiResponse": {
            "type": "object",
            "additionalProperties": False,
            "required": ["status"],
            "properties": {
                "status": {"type": "integer"},
                "contentType": {
                    "type": "string",
                    "default": "application/json"
                },
                "schema": {
                    "type": "object",
                    "default": {},
                    "additionalProperties": True
                },
                "example": {}
            }
        }
    }
}

__all__ = ["API_COLLECTION_SCHEMA"]
