class StackNode:
    def __init__(self, question, answer, card_id=None):
        self.question = question
        self.answer = answer
        self.card_id = card_id
        self.next = None
    
class Stack:
    """Manages flashcards using a LIFO stack structure."""
    def __init__(self):
        self.top = None
    
    def push_card(self, question, answer):
        """Adds a new flashcard to the top of the stack."""
        new_card = StackNode(question, answer)
        new_card.next = self.top
        self.top = new_card
        return new_card

    def pop_card(self):
        """Removes and returns the flashcard from the top of the stack."""
        if not self.top:
            return None
        popped_card = self.top
        self.top = self.top.next
        return popped_card
    
    def peek_card(self):
        """Returns the flashcard at the top without removing it."""
        return self.top
    
    def is_empty(self):
        """Checks if the stack is empty."""
        return self.top is None
    
    def size(self):
        """Returns the number of flashcards in the stack."""
        count = 0
        current = self.top
        while current:
            count += 1
            current = current.next
        return count
    
    def list_cards(self):
        """Returns a list of flashcards from top to bottom (for debug or display)."""
        cards = []
        current = self.top
        while current:
            cards.append({
                "question": current.question,
                "answer": current.answer,
                "card_id": current.card_id
            })
            current = current.next
        return cards
    
    
        