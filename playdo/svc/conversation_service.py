"""
One of the main pieces of application logic contained in this service is authorization checks: a user
can only access/modify conversations that they own, and this service handles performing those checks
with minimal redunant DB queries.

Also handles send_message which is a more involved back-and-forth between various components.
"""
from playdo.conversation_repository import ConversationRepository
from playdo.models import ConversationHistory, PlaydoMessage
from playdo.errors import NotAuthorizedForConversation
from playdo.response_getter import ResponseGetter
import logging

logger = logging.getLogger(__name__)
class ConversationService:
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    def list_conversations(self, user_id: int) -> list[ConversationHistory]:
        return self.conversation_repository.get_all_conversation_ids_for_user(user_id)

    def create_conversation(self, user_id: int) -> ConversationHistory:
        return self.conversation_repository.create_new_conversation(user_id)

    def get_conversation_for_user(self, conversation_id: int, user_id: int) -> ConversationHistory:
        conversation = self.conversation_repository.get_conversation(conversation_id)
        if conversation.user_id != user_id:
            raise NotAuthorizedForConversation(conversation_id, user_id)
        return conversation
    
    def send_new_message(self, conversation_id: int, user_id: int, new_msg: PlaydoMessage) -> ConversationHistory:
        conversation = self.get_conversation_for_user(conversation_id, user_id)
        if conversation.user_id != user_id:
            raise NotAuthorizedForConversation(conversation_id, user_id)
        response_getter = ResponseGetter()
        updated_conversation = self.conversation_repository.add_messages_to_conversation(conversation_id, [new_msg])

        # Get the assistant's response (using the existing conversation messages plus our new user message)
        resp_message: PlaydoMessage = response_getter._get_next_assistant_resp(updated_conversation.messages)

        # Save the new messages
        updated_conversation = self.conversation_repository.add_messages_to_conversation(conversation_id, [resp_message])
        # Return the updated conversation with the new messages
        return updated_conversation


        
