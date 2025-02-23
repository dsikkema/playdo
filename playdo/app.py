from playdo.response_getter import ResponseGetter
from playdo.conversation_history_repository import conversation_history_manager
from playdo.historical_conversation import HistoricalConversation
import logging
if __name__ == "__main__":
    logger = logging.getLogger('playdo')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.debug("test debug ")
    with conversation_history_manager("data/app.db") as conversation_history:
        response_getter = ResponseGetter()
        historical_conversation = HistoricalConversation(conversation_history, response_getter)
        historical_conversation.run_historical_conversation()