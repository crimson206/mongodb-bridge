# File: conftest.py
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection

from crimson.pymongo_bridge.simple_chatbot import ChatBotClient, ChatBotServer


@pytest.fixture(scope="session")
def mongo_client() -> Generator[MongoClient, None, None]:
    load_dotenv("../../.env")
    client: MongoClient = MongoClient(os.getenv("PYMONGO_CONNECTION_STRING0"))
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_collection(mongo_client: MongoClient) -> Generator[Collection, None, None]:
    db = mongo_client.get_database("pymongo-bridge")
    collection: Collection = db.get_collection("pytest_13_08_2024")
    yield collection
    collection.drop()


@pytest.fixture(scope="function")
def chatbot_client(test_collection: Collection) -> Generator[ChatBotClient, None, None]:
    client = ChatBotClient(test_collection, "pytest_namespace")
    client.clear_chats()
    yield client
    client.clear_chats()


@pytest.fixture(scope="function")
def chatbot_server(test_collection: Collection) -> Generator[ChatBotServer, None, None]:
    server = ChatBotServer(test_collection, "pytest_namespace")
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
