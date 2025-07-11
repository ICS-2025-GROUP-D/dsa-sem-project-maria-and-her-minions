# review_history.py

from linkedlist import Node  # Import Node class used in review history

class ReviewHistory:
    def __init__(self):
        # Key: card_id (or node.card_id); Value: review entry dict
        self.history = {}  # {card_id: {"question": str, "answer": str, "review": str}}

    def push(self, node, review_note):
        """
        Add a flashcard to review history.
        review_note can be 'Correct', 'Incorrect', 'Needs Review', etc.
        """
        self.history[node.card_id] = {
            "question": node.question,
            "answer": node.answer,
            "review": review_note
        }

    def get_review(self, card_id):
        """Retrieve review entry for a specific flashcard."""
        return self.history.get(card_id)

    def has_reviewed(self, card_id):
        return card_id in self.history

    def size(self):
        return len(self.history)

    def display_all(self):
        """Print all reviewed flashcards and their notes."""
        print("\nReviewed Flashcards:")
        for card_id, entry in self.history.items():
            print(f"- {entry['question']} -> {entry['answer']} [Review: {entry['review']}]")
