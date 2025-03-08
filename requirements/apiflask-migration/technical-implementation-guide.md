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

#### 2.1 Create Base Schema Models

Create a new file `playdo/schemas.py` to contain marshmallow-dataclass models:

- Define base conversion patterns between Pydantic and marshmallow-dataclass
- Create utility functions for schema generation
- Set up common schema configurations (like error handling)

#### 2.2 Convert PlaydoContent Model

Convert the `PlaydoContent` model from Pydantic to marshmallow-dataclass:

- Maintain the same structure and validation rules
- Ensure compatibility with existing database serialization

Example conversion:

```python
from dataclasses import dataclass, field
from typing import Literal
import marshmallow_dataclass
from marshmallow import Schema

@dataclass
class PlaydoContent:
    type: Literal["text"]
    text: str

    # Class method for converting from Anthropic content
    @classmethod
    def from_anthropic_content(cls, content):
        assert content.type == "text"
        return cls(type="text", text=content.text)

    # Schema generation
    Schema: ClassVar[Type[Schema]] = Schema
```

#### 2.3 Convert PlaydoMessage Model

Convert the `PlaydoMessage` model:

- Ensure all fields and methods are preserved
- Pay special attention to the XML conversion methods and the fields (like `status="stale_or_not_run"` etc) to preserve this xml structure.
- Maintain compatibility with Anthropic message formats

#### 2.4 Convert ConversationHistory Model

Convert the `ConversationHistory` model:

- Maintain relationships between models
- Ensure datetime field handling is consistent

### Milestone 3: API Endpoint Updates

#### 3.1 Define Request/Response Schemas

Create request and response schemas for each endpoint:

- Define input validation schemas
- Define response serialization schemas
- Include appropriate documentation strings for OpenAPI

Example for creating a conversation:

```python
@dataclass
class ConversationResponse:
    id: int
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    messages: List[PlaydoMessage] = field(default_factory=list)

    class Meta:
        ordered = True
```

#### 3.2 Update Blueprint Registration

Modify the blueprint registration in `playdo/app.py`:

- Register blueprints with APIFlask instead of Flask
- Configure blueprint-specific OpenAPI tags

#### 3.3 Update Conversation Endpoints

Refactor each endpoint in `playdo/endpoints/conversations.py` to use APIFlask decorators:

- Replace manual request validation with `@app.input`
- Replace manual response serialization with `@app.output`
- Add appropriate documentation for each endpoint

Example endpoint conversion:

```python
@conversations_bp.route("/conversations/<int:conversation_id>/send_message", methods=["POST"])
@app.input(SendMessageSchema)
@app.output(ConversationSchema)
def send_new_message(conversation_id, data):
    """
    Add a user message to a conversation and get the assistant's response.

    The request JSON should contain:
    - message: The user's message text (required)
    - editor_code: The code in the editor (optional)
    - stdout: Standard output from running the code (optional)
    - stderr: Standard error from running the code (optional)
    """
    # Function implementation
    # Now 'data' is already validated against SendMessageSchema
    # Return value will be automatically serialized using ConversationSchema
```

### Milestone 4: Documentation and Testing

#### 4.1 Configure OpenAPI Documentation

Add detailed OpenAPI configuration to `playdo/app.py`:

- Set title, version, and description
- Configure Swagger UI and/or Redoc
- Add security schemes if needed in the future

```python
app = APIFlask(
    __name__,
    title="Playdo API",
    version="1.0.0",
    spec_path="/api/openapi.json",
    docs_path="/api/docs",
    docs_ui="swagger_ui",  # or "redoc"
)
```

#### 4.2 Add Schema Documentation

Enhance schemas with documentation:

- Add field descriptions
- Specify example values
- Document validation rules

#### 4.3 Test Suite Updates

Update existing tests to work with the new schemas:

- Modify test fixtures to use marshmallow-dataclass models
- Ensure all API functionality is covered
- Add tests for new OpenAPI functionality

### Implementation Considerations

1. **Gradual Migration**: Consider migrating one model or endpoint at a time to minimize disruption.

2. **Compatibility Layer**: During migration, you may need a compatibility layer to convert between Pydantic and marshmallow-dataclass models.

3. **Error Handling**: Ensure APIFlask error responses match your current error format.

4. **Database Impact**: The migration should not impact the database schema, but verify this with tests.

5. **Performance**: Check for any performance differences between Pydantic and marshmallow-dataclass, especially for large payloads.

6. **Type Annotations**: Make sure to maintain proper type annotations for mypy.

7. **API errors**: Look at the error responses in the existing endpoints (like custom validation errors) and ensure that these possible
error responses are properly represented in the schema, and communicated appropriately inside the annotations that decorate the endpoint functions.
### Technical Decisions

1. **Why APIFlask over Flask-RESTful or Flask-RESTX?**
   APIFlask provides better integration with marshmallow and more modern OpenAPI support.

2. **Why marshmallow-dataclass over direct marshmallow?**
   To avoid duplication between data models and their serialization rules, similar to how Pydantic works.

3. **Keeping the existing database schema:**
   The current schema is well-designed and the changes are focused on the API layer, not the data storage.

## Conclusion

This migration will modernize the Playdo API by providing automatic OpenAPI documentation while maintaining a clean separation of concerns. The use of marshmallow-dataclass will provide a familiar pattern to the development team used to working with Pydantic, while enabling better integration with Flask through APIFlask.

Remember that this is an MVP-focused migration. Features like authentication, advanced validation, and complex OpenAPI customizations can be added in future iterations once the basic migration is complete.

## Reminder

Please follow all existing code standards and rules in place for linting, typechecking, and testing. Ensure that your implementation passes all linters (ruff), type checkers (mypy), and tests (pytest) according to the project's established standards. The DETAILED_TECHNICAL_NOTES.md file contains important guidelines that should be followed when modifying the codebase.
