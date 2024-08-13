import os
import sys
from typing import Generator

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection

from crimson.pymongo_bridge.simple_chatbot import (
    ChatBotClient,
    ChatBotServer,
    IDManager,
    SimpleSession
)

# Get Python version
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture(scope="session")
def mongo_client() -> Generator[MongoClient, None, None]:
    load_dotenv("../../.env")
    client: MongoClient = MongoClient(
        os.getenv("PYMONGO_CONNECTION_STRING0"), serverSelectionTimeoutMS=5000
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_collection(mongo_client: MongoClient) -> Generator[Collection, None, None]:
    db = mongo_client.get_database("pymongo-bridge")
    collection_name = f"pytest_{PYTHON_VERSION}_{os.getpid()}"  # Include Python version and process ID
    collection: Collection = db.get_collection(collection_name)
    yield collection
    collection.drop()


@pytest.fixture(scope="function")
def chatbot_client(test_collection: Collection) -> Generator[ChatBotClient, None, None]:
    namespace = f"pytest_namespace_{PYTHON_VERSION}_{os.getpid()}"  # Include Python version and process ID
    client = ChatBotClient(test_collection, namespace)
    client.clear_chats()
    yield client
    client.clear_chats()


@pytest.fixture(scope="function")
def chatbot_server(test_collection: Collection) -> Generator[ChatBotServer, None, None]:
    namespace = f"pytest_namespace_{PYTHON_VERSION}_{os.getpid()}"  # Include Python version and process ID
    server = ChatBotServer(test_collection, namespace)
    yield server


def test_chat_client(chatbot_client: ChatBotClient) -> None:
    # Test chat method
    chatbot_client.chat("Hello, chatbot!")
    chatbot_client.refresh_chats()
    assert len(chatbot_client.chats) == 1
    assert chatbot_client.chats[0].prompt == "Hello, chatbot!"

    # Test rechat method
    chatbot_client.rechat("How are you?")
    chatbot_client.refresh_chats()
    assert len(chatbot_client.chats) == 1
    assert chatbot_client.chats[0].prompt == "How are you?"


def test_chat_server(
    chatbot_client: ChatBotClient, chatbot_server: ChatBotServer
) -> None:
    # Prepare a chat message
    chatbot_client.chat("Hello, server!")

    # Test answer method
    chatbot_server.answer()
    chatbot_server.refresh_chats()
    assert len(chatbot_server.chats) == 1
    assert chatbot_server.chats[0].generated_text is not None
    assert chatbot_server.chats[0].generated_text == "Message from chatbot."


def test_multiple_chats(chatbot_client: ChatBotClient) -> None:
    # Add multiple chat messages
    chatbot_client.chat("First message")
    chatbot_client.chat("Second message")
    chatbot_client.chat("Third message")

    # Check if all messages are stored
    chatbot_client.refresh_chats()
    assert len(chatbot_client.chats) == 3
    assert chatbot_client.chats[0].prompt == "First message"
    assert chatbot_client.chats[1].prompt == "Second message"
    assert chatbot_client.chats[2].prompt == "Third message"


def test_clear_chats(chatbot_client: ChatBotClient) -> None:
    # Add some chats
    chatbot_client.chat("Test message")
    chatbot_client.refresh_chats()
    assert len(chatbot_client.chats) == 1

    # Clear chats
    chatbot_client.clear_chats()
    chatbot_client.refresh_chats()
    assert len(chatbot_client.chats) == 0


def test_id_manager_register_duplicate_id():
    id_manager = IDManager("test_namespace")
    id_manager.register_id(1)

    with pytest.raises(Exception) as exc_info:
        id_manager.register_id(1)
    assert str(exc_info.value) == "ID 1 was already registered."


def test_chatbot_force_chats(chatbot_client: ChatBotClient):
    # Add some chats
    chatbot_client.chat("First message")
    chatbot_client.chat("Second message")
    chatbot_client.refresh_chats()

    # Modify chats in memory without updating the database
    chatbot_client.chats.append(
        SimpleSession(
            name_space=chatbot_client.name_space, id=100, prompt="Test message"
        )
    )

    # Force chats (this should update the database with the in-memory state)
    chatbot_client.force_chats()

    # Refresh chats from the database
    chatbot_client.refresh_chats()

    # Check if the forced chat is now in the database
    assert len(chatbot_client.chats) == 3
    assert any(chat.id == 100 for chat in chatbot_client.chats)


def test_chatbot_client_rechat_no_existing_session(chatbot_client: ChatBotClient):
    chatbot_client.clear_chats()  # Ensure no existing chats

    with pytest.raises(Exception) as exc_info:
        chatbot_client.rechat("This should fail")
    assert str(exc_info.value) == "No existing chat session to update."


def test_chatbot_server_answer_no_valid_id(chatbot_server: ChatBotServer):
    chatbot_server.clear_chats()  # Ensure no existing chats

    with pytest.raises(Exception) as exc_info:
        chatbot_server.answer()
    assert str(exc_info.value) == "No valid ID found in IDManager."
