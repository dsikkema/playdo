from pathlib import Path
from playdo.settings import settings
from playdo.response_getter import ResponseGetter
from playdo.conversation_repository import conversation_repository
from playdo.svc.conversation_service import ConversationService
from playdo.cli.historical_conversation import HistoricalConversation
import logging


def main() -> None:
    logger = logging.getLogger("playdo")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    with conversation_repository(Path(settings.DATABASE_PATH)) as conv_repository:
        response_getter: ResponseGetter = ResponseGetter()
        conversation_service = ConversationService(conv_repository)
        historical_conversation = HistoricalConversation(conversation_service, response_getter)
        historical_conversation.run_historical_conversation()


if __name__ == "__main__":
    main()
