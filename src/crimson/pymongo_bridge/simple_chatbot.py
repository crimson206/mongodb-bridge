from pymongo.collection import Collection
from pydantic import BaseModel
from typing import Optional, List, Any, Callable


class IDManager:
    def __init__(self, name_space: str = "default"):
        self.name_space = name_space
        self.ids: List[int] = []

    def register_id(self, id: int):
        if id not in self.ids:
            self.ids.append(id)
        else:
            raise Exception(f"ID {id} was already registered.")

    def generate_next_max_id(self, register: bool = True):
        if len(self.ids) == 0:
            next_id = 0
        else:
            next_id = max(self.ids) + 1
        if register:
            self.register_id(next_id)
        return next_id

    @property
    def max_id(self) -> Optional[int]:
        if len(self.ids) == 0:
            return None
        else:
            return max(self.ids)


class SimpleSession(BaseModel):
    name_space: str
    id: int
    prompt: str
    generated_text: Optional[str] = None
    user_meta: Optional[Any] = None
    ai_meta: Optional[Any] = None


class ChatBot:
    def __init__(self, collection: Collection, name_space: str):
        self.collection = collection
        collection.create_index("id", unique=True)
        self.id_manager = IDManager(name_space)
        self.name_space = name_space
        self.chats: List[SimpleSession] = []

    def refresh_chats(self):
        cursor = self.collection.find({"name_space": self.name_space})

        chats = [SimpleSession(**doc) for doc in cursor]
        ids = [chat.id for chat in chats]

        self.id_manager.ids = ids
        self.chats = chats

    def empty_db(self):
        self.collection.delete_many({"name_space": self.name_space})

    def clear_chats(self):
        self.empty_db()
        self.id_manager.ids = []
        self.chats = []

    def force_chats(self):
        self.empty_db()

        if self.chats:
            chat_dicts = [chat.model_dump() for chat in self.chats]
            self.collection.insert_many(chat_dicts)

        self.id_manager.ids = [chat.id for chat in self.chats]


class ChatBotClient(ChatBot):
    def chat(self, prompt: str):
        chat = SimpleSession(
            name_space=self.name_space,
            id=self.id_manager.generate_next_max_id(register=True),
            prompt=prompt,
            generated_text=None,
        )

        self.collection.insert_one(chat.model_dump())

    def rechat(self, prompt: str):
        current_id = self.id_manager.max_id

        if current_id is None:
            raise Exception("No existing chat session to update.")

        generated_text = None

        self.collection.update_one(
            {"id": current_id, "name_space": self.name_space},
            {"$set": {"prompt": prompt, "generated_text": generated_text}},
        )


def generate_fn(chats: List[SimpleSession]) -> str:
    return "Message from chatbot."


class ChatBotServer(ChatBot):
    def __init__(
        self,
        collection: Collection,
        name_space: str,
        generate_fn: Callable[[List[SimpleSession]], str] = generate_fn,
    ):
        super().__init__(collection, name_space)
        self.generate_fn = generate_fn

    def answer(self):
        self.refresh_chats()

        # Generate text
        generated_text = self.generate_fn(self.chats)

        # Get the current max ID
        current_id = self.id_manager.max_id

        if current_id is not None:
            # Update only the generated_text field for the specific ID
            self.collection.update_one(
                {"id": current_id, "name_space": self.name_space},
                {"$set": {"generated_text": generated_text}},
            )
        else:
            raise Exception("No valid ID found in IDManager.")
