# Playdo API Migration Specification

## Overview

This specification outlines the migration of Playdo's backend from a standard Flask application using Pydantic models to APIFlask with marshmallow-dataclass models. The primary goal is to establish proper OpenAPI integration for future API documentation while maintaining the existing database schema and functionality. This migration will enable interactive API documentation through Swagger UI and provide a cleaner separation between data models and their serialization/validation logic.

## Migration Guide

### Important Note to AI Developer

The guidance in this document is based on the code samples provided. The actual codebase may contain variations in naming, structure, or additional functionality not covered here. Use your judgment to adapt these recommendations to the specific context of the application. Critically evaluate all suggestions and integrate them intelligently rather than following them verbatim.

### Milestone 1: Dependencies and Application Setup

#### 1.1 Add Required Dependencies

Update `pyproject.toml` to include the necessary dependencies:

```python
dependencies = [
    # Existing dependencies...
    "anthropic>=0.46.0",
    "flask>=3.1.0",
    "ipdb>=0.13.13",
    "mypy>=1.15.0",
    "pre-commit>=4.1.0",
    "pydantic>=2.10.6",  # Keep for transitional period
    "pytest>=8.3.4",
    "requests>=2.32.3",
    "ruff>=0.9.8",
    # New dependencies
    "apiflask>=2.0.0",
    "marshmallow>=3.19.0",
    "marshmallow-dataclass>=8.5.14",
]
```

#### 1.2 Replace Flask with APIFlask

Modify `playdo/app.py` to use APIFlask instead of standard Flask:

- Replace the Flask import with APIFlask
- Update the application creation function to initialize an APIFlask instance
- Configure basic OpenAPI information

Considerations:
- APIFlask is a drop-in replacement for Flask, so minimal changes are needed
- Keep existing configuration logic and parameter handling

#### 1.3 Update Custom Application Class

Modify `playdo/playdo_app.py` to extend APIFlask instead of Flask:

- Update class definition to inherit from APIFlask
- Maintain existing utility methods for accessing repositories
- Add OpenAPI configuration methods

### Milestone 2: Data Model Conversion

#### 2.1 Convert Models to Dataclasses

Convert the Pydantic models in `playdo/models.py` to dataclasses with marshmallow-dataclass:

- Replace Pydantic imports with dataclass imports
- Maintain the same field structure and validation rules
- Keep the same method signatures and functionality
- Use marshmallow-dataclass decorators and field metadata for validation

No separate schema files are needed as marshmallow-dataclass automatically generates schemas from dataclass definitions using `marshmallow_dataclass.class_schema()`.

#### 2.2 Convert PlaydoContent Model

Convert the `PlaydoContent` model from Pydantic to dataclass:

- Maintain the same structure and validation rules
- Ensure compatibility with existing database serialization

Example conversion:

```python
from dataclasses import dataclass, field
from typing import Literal, ClassVar, Type
import marshmallow_dataclass
from marshmallow import Schema
from anthropic.types import ContentBlock

@dataclass
class PlaydoContent:
    type: Literal["text"]
    text: str

    # Class method for converting from Anthropic content
    @classmethod
    def from_anthropic_content(cls, content: ContentBlock):
        assert content.type == "text"
        return cls(type="text", text=content.text)
```

#### 2.3 Convert PlaydoMessage Model

Convert the `PlaydoMessage` model to a dataclass:

- Preserve all fields including optional fields for editor code and outputs
- Maintain XML transformation methods for Anthropic API communication
- Keep the model conversion methods between Playdo and Anthropic formats

#### 2.4 Convert ConversationHistory Model

Convert the `ConversationHistory` model to a dataclass:

- Maintain relationships between models
- Ensure datetime field handling is consistent

### Milestone 3: API Endpoint Updates

#### 3.1 Update Endpoint Decorators

Modify each endpoint in `playdo/endpoints/conversations.py` to use APIFlask decorators:

- Use `@app.input` for request validation with generated marshmallow schemas
- Use `@app.output` for response serialization with generated marshmallow schemas
- Add appropriate documentation for each endpoint
- Look at the error responses in the existing endpoints (like custom validation errors) and ensure that these possible
  error responses are properly represented in the schema, and communicated appropriately inside the annotations that
  decorate the endpoint functions.

For example, for input validation, you can use the schema generated from a dataclass:

```python
# Create a dataclass for the input
@dataclass
class SendMessageRequest:
    message: str
    editor_code: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

# Use it in the endpoint
@conversations_bp.route("/conversations/<int:conversation_id>/send_message", methods=["POST"])
@app.input(marshmallow_dataclass.class_schema(SendMessageRequest)())
@app.output(marshmallow_dataclass.class_schema(ConversationHistory)())
# also make sure to document the validation errors and status codes for display in OpenAPI schema
def send_new_message(conversation_id, data):
    # Function implementation using validated data
    # Return value will be automatically serialized
```

#### 3.2 Update Blueprint Registration

Modify the blueprint registration in `playdo/app.py` to work with APIFlask:

- Register blueprints with APIFlask instead of Flask
- Configure blueprint-specific OpenAPI tags

#### 3.3 Implement Field Validation Rules

Ensure that the validation rules for code-related fields are properly implemented:

- If `editor_code` is null, then `stdout` and `stderr` must also be null
- If `editor_code` is not null, `stdout` and `stderr` may be null or have values
- Empty string values for these fields are distinct from null values

These validation rules can be implemented with marshmallow validators in the dataclass field metadata.

### Milestone 4: Conversation Saving Enhancements

#### 4.1 Maintain the Conversation Saving Loop

Preserve the key pattern described in the technical notes:

- User message is first saved to the database
- Complete conversation history is sent to ResponseGetter
- ResponseGetter returns only the assistant's response message
- Assistant message is then saved to the database

Ensure this pattern is maintained when updating the endpoints to use APIFlask's validation and serialization.

#### 4.2 Update ResponseGetter Integration

Ensure the ResponseGetter continues to work with the new dataclass models:

- Update the model conversion "bubble" pattern to work with dataclasses
- Maintain the conversion between PlaydoMessage objects and Anthropic message formats
- Keep the editor code XML transformation for Anthropic API communication

### Milestone 5: Documentation and Testing

#### 5.1 Configure OpenAPI Documentation

Add detailed OpenAPI configuration to `playdo/app.py`:

- Set title, version, and description
- Configure Swagger UI and/or Redoc
- Organize endpoints by tags for better documentation

```python
app = APIFlask(
    __name__,
    title="Playdo API",
    version="1.0.0",
    spec_path="/api/openapi.json",
    docs_path="/api/docs"
)
```

#### 5.2 Enhance Schema Documentation

Add documentation to the dataclasses that will be reflected in the OpenAPI documentation:

- Add docstrings to classes
- Use field metadata to add description and examples
- Document validation rules

Example of adding field documentation:

```python
@dataclass
class PlaydoMessage:
    role: Literal["user", "assistant"] = field(
        metadata={"description": "The role of the message sender (user or assistant)"}
    )
    content: list[PlaydoContent] = field(
        metadata={"description": "List of content blocks in the message"}
    )
    editor_code: Optional[str] = field(
        default=None,
        metadata={"description": "Code from the editor (null if not applicable)"}
    )
    # Other fields...
```

#### 5.3 Test Suite Updates

Update existing tests to work with the new dataclass models:

- Modify test fixtures to use dataclass models instead of Pydantic
- Ensure all API functionality is covered
- Add tests for new OpenAPI functionality

### Implementation Considerations

1. **Gradual Migration**: Consider migrating one model or endpoint at a time to minimize disruption.

2. **Compatibility**: During migration, you may need temporary compatibility code to handle both Pydantic and dataclass models.

3. **Error Handling**: Ensure APIFlask error responses match your current error format or update the frontend to handle the new format.

4. **Database Impact**: The migration should not impact the database schema, but verify this with tests.

5. **Field Validation**: Pay special attention to the validation rules for editor code, stdout, and stderr fields, ensuring they match the requirements in the technical notes.

6. **XML Transformation**: Ensure the XML transformation for Anthropic API communication continues to work correctly with the dataclass models.

### Technical Decisions

1. **Why APIFlask over Flask-RESTful or Flask-RESTX?**
   APIFlask provides better integration with marshmallow and more modern OpenAPI support.

2. **Why marshmallow-dataclass over direct marshmallow?**
   To avoid duplication between data models and their serialization rules, similar to how Pydantic works.

3. **No separate schema files needed:**
   Unlike traditional marshmallow usage, marshmallow-dataclass generates schemas directly from dataclass definitions, eliminating the need for separate schema classes.

## Conclusion

This migration will modernize the Playdo API by providing automatic OpenAPI documentation while maintaining a clean separation of concerns. The use of marshmallow-dataclass will provide a familiar pattern to the development team used to working with Pydantic, while enabling better integration with Flask through APIFlask.

Remember that this is an MVP-focused migration. Features like authentication, advanced validation, and complex OpenAPI customizations can be added in future iterations once the basic migration is complete.

## Reminder

Please follow all existing code standards and rules in place for linting, typechecking, and testing. Ensure that your implementation passes all linters (ruff), type checkers (mypy), and tests (pytest) according to the project's established standards. The DETAILED_TECHNICAL_NOTES.md file contains important guidelines that should be followed when modifying the codebase.
