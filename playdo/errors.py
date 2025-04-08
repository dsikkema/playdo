class NotAuthorizedForConversation(Exception):
    """
    Raised when a user attempts to access a conversation that they are not authorized to access.
    """
    def __init__(self, conversation_id: int, user_id: int):
        super().__init__(f"User with id {user_id} is not authorized to access conversation with id {conversation_id}")

class UserAlreadyExistsError(Exception):
    """Exception raised when a user already exists in the database."""
    pass

class UserNotFoundError(Exception):
    """Exception raised when a user is not found in the database."""
    pass

class ConversationNotFoundError(Exception):
    """Exception raised when a conversation is not found in the database."""
    def __init__(self, conversation_id: int):
        super().__init__(f"Conversation with id {conversation_id} not found")

