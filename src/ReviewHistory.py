# review_history.py

from linkedlist import Node  
class ReviewHistory:
    def __init__(self):
       
        self.history = {}  

    def push(self, node, review_note):
  
        self.history[node.card_id] = {
            "question": node.question,
            "answer": node.answer,
            "review": review_note
        }

    def get_review(self, card_id):
      
        return self.history.get(card_id)

    def has_reviewed(self, card_id):
        return card_id in self.history

    def size(self):
        return len(self.history)

    def display_all(self):
       
        print("Reviewed Flashcards:")
        for card_id, entry in self.history.items():
            print(f"- {entry['question']} -> {entry['answer']} [Review: {entry['review']}]")
