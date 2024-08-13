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


class ChatBotClient:
    def __init__(self, collection: Collection, name_space: str):
        self.collection = collection
        collection.create_index("id", unique=True)
        self.id_manager = IDManager()
        self.name_space = name_space
        self.chats = List[SimpleSession]

    def chat(self, prompt):
        chat = SimpleSession(
            name_space=self.name_space,
            id=self.id_manager.generate_next_max_id(register=True),
            prompt=prompt,
            generated_text=None,
        )

        self.collection.insert_one(chat.model_dump())

    def rechat(self, prompt):
        current_id = self.id_manager.max_id

        if current_id is None:
            raise Exception("No existing chat session to update.")

        generated_text = None

        self.collection.update_one(
            {"id": current_id, "name_space": self.name_space},
            {"$set": {"prompt": prompt, "generated_text": generated_text}},
        )

    def refresh_chats(self):
        cursor = self.collection.find({"name_space": self.name_space})

        chats = [SimpleSession(**doc) for doc in cursor]
        ids = [chat.id for chat in chats]

        self.id_manager.ids = ids
        self.chats = chats


def generate_fn(chats):
    return "Message from chatbot."


class ChatBotServer:
    def __init__(
        self,
        collection: Collection,
        name_space: str,
        generate_fn: Callable = generate_fn,
    ):
        self.collection = collection
        collection.create_index("id", unique=True)
        self.id_manager = IDManager()
        self.name_space = name_space
        self.chats = List[SimpleSession]
        self.generate_fn = generate_fn

    def answer(self):
        self.refresh_chats()

        # 텍스트 생성
        generated_text = self.generate_fn(self.chats)

        # 현재 최대 ID 가져오기
        current_id = self.id_manager.max_id

        if current_id is not None:
            # 특정 ID의 generated_text 필드만 업데이트
            self.collection.update_one(
                {"id": current_id, "name_space": self.name_space},
                {"$set": {"generated_text": generated_text}},
            )
        else:
            raise Exception("No valid ID found in IDManager.")

    def refresh_chats(self):
        cursor = self.collection.find({"name_space": self.name_space})

        chats = [SimpleSession(**doc) for doc in cursor]
        ids = [chat.id for chat in chats]

        self.id_manager.ids = ids
        self.chats = chats
