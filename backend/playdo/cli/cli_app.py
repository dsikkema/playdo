from playdo.settings import settings
from playdo.response_getter import ResponseGetter
from playdo.conversation_repository import conversation_repository
from playdo.cli.historical_conversation import HistoricalConversation
import logging

if __name__ == "__main__":
    logger = logging.getLogger("playdo")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    with conversation_repository(settings.DATABASE_PATH) as conversation_history:
        response_getter: ResponseGetter = ResponseGetter()
        historical_conversation = HistoricalConversation(conversation_history, response_getter)
        historical_conversation.run_historical_conversation()
