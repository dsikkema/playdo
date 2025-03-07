#!/bin/bash
# Example of sending a message with code context

# Create a new conversation first if needed
# curl -X POST http://localhost:5000/api/conversations

# Replace 1 with your conversation ID
CONVERSATION_ID=1

curl -X POST http://localhost:5000/api/conversations/$CONVERSATION_ID/send_message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you explain what this code does?",
    "editor_code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    else:\n        return fibonacci(n-1) + fibonacci(n-2)\n\nresult = fibonacci(10)\nprint(result)",
    "stdout": "55",
    "stderr": ""
  }'
