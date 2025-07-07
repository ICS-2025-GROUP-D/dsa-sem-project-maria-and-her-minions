# flashcard_db.py
from pymongo import MongoClient
from bson.objectid import ObjectId
from collections import deque
from typing import Optional, Any

from linkedlist import LinkedList          
from review_history import ReviewHistory   
from category_manager import CategoryManager  


class FlashcardDB:
    def __init__(
        self,
        connection_string: str,
        db_name: str = "flashcard_app",
        collection_name: str = "flashcards",
    ) -> None:
        # MongoDB setup
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        # In-memory structures
        self.linked_list: LinkedList = LinkedList()                # Task 1
        self.practice_queue: deque = deque()                        # Task 3
        self.review_history: ReviewHistory = ReviewHistory()       # Task 2
        self.category_manager: CategoryManager = CategoryManager() # Task 5
        self._node_index: dict[ObjectId, Any] = {}                 # Fast lookup

        # Load from DB
        self._load_cards_into_memory()

    def _ensure_oid(self, card_id) -> ObjectId:
        return card_id if isinstance(card_id, ObjectId) else ObjectId(card_id)

    def _load_cards_into_memory(self) -> None:
        for card_data in self.collection.find():
            node = self.linked_list.add_card(card_data["question"], card_data["answer"])
            node.card_id = card_data["_id"]
            node.category = card_data.get("category", "Uncategorized")

            self._node_index[node.card_id] = node
            self.practice_queue.append(node)
            self.category_manager.add_to_category(node.category, node)

    def add_card(self, question: str, answer: str, category: str):
        doc = {"question": question, "answer": answer, "category": category}
        result = self.collection.insert_one(doc)

        node = self.linked_list.add_card(question, answer)
        node.card_id = result.inserted_id
        node.category = category

        self._node_index[node.card_id] = node
        self.practice_queue.append(node)
        self.category_manager.add_to_category(category, node)

        print(f"[\u2713] Card added with ID: {result.inserted_id}")
        return node

    def edit_card(self, card_id, new_q: str, new_a: str, new_cat: Optional[str] = None) -> bool:
        oid = self._ensure_oid(card_id)
        ok_list = self.linked_list.edit_card(oid, new_q, new_a)
        update_fields = {"question": new_q, "answer": new_a}
        if new_cat:
            update_fields["category"] = new_cat

        ok_db = (
            self.collection.update_one({"_id": oid}, {"$set": update_fields}).modified_count > 0
        )

        if oid in self._node_index:
            node = self._node_index[oid]
            node.question = new_q
            node.answer = new_a
            if new_cat:
                old_cat = node.category
                node.category = new_cat
                self.category_manager.update_category(old_cat, new_cat, node)

        if ok_list and ok_db:
            print(f"[\u2713] Card {oid} updated.")
            return True
        print(f"[!] Card {oid} not found.")
        return False

    def delete_card(self, card_id) -> bool:
        oid = self._ensure_oid(card_id)
        ok_list = self.linked_list.delete_card(oid)
        ok_db = self.collection.delete_one({"_id": oid}).deleted_count > 0

        node = self._node_index.pop(oid, None)
        if node:
            if node in self.practice_queue:
                self.practice_queue.remove(node)
            if node in self.review_history.stack:
                self.review_history.stack.remove(node)
            self.category_manager.remove_from_category(node.category, node)

        if ok_list and ok_db:
            print(f"[\u2713] Card {oid} deleted.")
            return True
        print(f"[!] Card {oid} not found.")
        return False

    def next_card(self) -> Optional[Any]:
        return self.practice_queue.popleft() if self.practice_queue else None

    def mark_reviewed(self, card_id, correct: bool) -> bool:
        oid = self._ensure_oid(card_id)
        node = self._node_index.get(oid)
        if not node:
            print(f"[!] Card {oid} not found.")
            return False

        self.review_history.push(node)
        if not correct:
            self.practice_queue.append(node)
        return True

    def revisit_last(self) -> Optional[Any]:
        return self.review_history.pop()

    def get_by_category(self, category: str):
        return self.category_manager.get_by_category(category)

    def list_categories(self):
        return self.category_manager.list_categories()

    def queue_size(self) -> int:
        return len(self.practice_queue)

    def review_stack_size(self) -> int:
        return self.review_history.size()

    def list_all(self) -> None:
        for node in self.linked_list.traverse():
            print(f"{node.card_id}: {node.question} -> {node.answer} [{node.category}]")


if __name__ == "__main__":
    MONGO_URI = (
        "mongodb+srv://Achar:12345@flashcardappcluster.sqpcmki.mongodb.net/"
        "?retryWrites=true&w=majority&appName=FlashCardAppCluster"
    )

    manager = FlashcardDB(MONGO_URI)

    # Add sample flashcards
    manager.add_card("What is 9 + 10?", "19", category="Math")
    manager.add_card("Who discovered gravity?", "Newton", category="Science")

    # Show categories
    print("\nCategories:", manager.list_categories())

    # Show flashcards in a category
    print("\nScience Flashcards:")
    for card in manager.get_by_category("Science"):
        print(f"- {card.question} -> {card.answer}")
