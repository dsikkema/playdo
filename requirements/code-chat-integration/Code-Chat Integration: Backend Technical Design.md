# Backend Changes: Enhancing the Message Model
## Overview

This document outlines the requirements for integrating the code editor and output display with the chat interface in Playdo. The goal is to ensure the AI tutor always has appropriate context about the student's code and output without cluttering the chat interface or sending redundant information.

## Core Concepts

- Code and output should be attached to user messages when relevant
- The frontend should track what code/output has been previously sent to avoid duplication
- The backend should transform our message structure into an efficient XML format for the AI
- The chat UI should indicate when code has been updated without dominating the conversation

## Current Structure to Updated Structure

The current backend uses a simple model where messages contain only text content:

```
PlaydoMessage:
- role: "user" or "assistant"
- content: List of PlaydoContent objects (which only have "text" fields)
```

We need to enhance this structure to include code context while maintaining compatibility with Anthropic's API:

```
Updated PlaydoMessage:
- role: "user" or "assistant"
- content: List of PlaydoContent objects
- editorCode: Optional[str] - Code from the editor (null if not applicable)
- stdout: Optional[str] - Standard output (null if not run or not applicable)
- stderr: Optional[str] - Standard error (null if not run or not applicable)
```

### Implementation Guide:

1. Extend the `PlaydoMessage` model with the new fields:
   - Add nullable fields for `editorCode`, `stdout`, and `stderr`
   - Update the database model and schema accordingly

2. Create a new method for XML representation:
   ```python
   def to_anthropic_xml(self) -> str:
       """Convert the message to an XML representation for Anthropic API."""
       # Implement XML construction with proper escaping
       # Use efficient XML structure with attributes for status
   ```

3. Update the `to_anthropic_message` method:
   ```python
   def to_anthropic_message(self) -> Message:
       """Convert to Anthropic Message format with XML embedded in text content."""
       # Convert message with XML-structured content including code context
   ```

4. Update message creation methods to handle code context:
   - Modify `user_message()` to accept optional code parameters
   - Ensure clear distinction between null (not run) and empty string (run with no output)

5. Update the conversation API endpoint to:
   - Save messages immediately before API calls
   - Process the enhanced message structure
   - Return complete conversations with the updated structure

## Backend Requirements

### Data Model Updates

1. Update the `Message` model to include new fields:
   - `messageText`: Text content of the message
   - `editorCode`: Code from the editor (nullable)
   - `stdout`: Standard output (nullable)
   - `stderr`: Standard error (nullable)

2. Implement appropriate database schema with these fields

### Message Handling

1. Immediately save incoming user messages to the database before making any API calls
   - This ensures that the message is preserved even if the API call fails

2. Create a transformation layer between the internal message structure and Anthropic's API:
   - Create a dedicated method/function to convert a `Message` into an XML representation
   - Implement using proper XML construction (not string concatenation) to handle escaping

3. Use a token-efficient XML structure:
   ```xml
   <message>
     <text>User's message content</text>
     <code>Python code from editor</code>
     <stdout status="not_run" />
     <stderr status="not_run" />
   </message>
   ```
   - Empty or null output fields should use the empty element with status attribute
   - Utilize XML structure efficiently rather than verbose text explanations

4. Create a `Message.to_anthropic_message()` method that:
   - Converts the message structure to the appropriate XML
   - Packages this into Anthropic's message format

### API Integration

1. Update the message sending endpoint to:
   - Accept and parse the new message structure
   - Save the message to the database immediately
   - Transform the message to Anthropic's format
   - Send to Anthropic's API
   - Process the response and save it to the database
   - Return the updated conversation to the frontend

## Implementation Milestones

### Milestone 1: Backend Data Model
1. Update the `Message` model with new fields
2. Create the database schema
3. Update the repository layer to handle the new fields

### Milestone 2: Backend Transformation Layer
1. Implement the XML conversion logic
2. Add the Anthropic message transformation function
3. Update the API endpoint to use the new transformation

### Milestone 3: Frontend State Tracking
1. Implement the lastSentCode and lastSentOutput state
2. Add the comparison logic to determine when to send code/output
3. Update the message sending function

### Milestone 4: Frontend UI Updates
1. Update the message rendering to show the "Code updated" indicator
2. Implement UI blocking during message sending
3. Add timeout handling

## Edge Cases to Handle

1. **Code Run Status**: If a user runs code without changing it, ensure the new output is sent even though the code hasn't changed.

   ```typescript
   const shouldSendUpdate =
     currentCode !== lastSentCode ||
     (runStatus.hasRun && (lastSentOutput.stdout === null || lastSentOutput.stderr === null));
   ```

2. **API Failures**: Save the user's message to the database before making the API call so that it's preserved even if the call fails.

3. **Null vs. Empty String**: Maintain the distinction between null (code not run) and empty string (code run with no output).

## Future Considerations (Not for MVP)

- Message pagination for efficiency
- Detailed code change indicators
- Expandable code views in messages
- Advanced error handling and retries for API calls
- State rollback functionality to show code at time of message

## Technical Notes

- Frontend should handle state comparison locally (not via backend)
- Use simple string comparison for code matching (no need for hashing at this stage)
- Focus on a working MVP first; optimize for performance later
- Pydantic models should be used for data validation and transformation
