# data_structures.py

class Node:
    """Represents a single flashcard in the linked list."""
    def __init__(self, question, answer, card_id=None):
        self.question = question
        self.answer = answer
        self.card_id = card_id
        self.next = None
        self.prev = None

class LinkedList:
    """Manages the collection of flashcards."""
    def __init__(self):
        self.head = None
        self.tail = None

    def add_card(self, question, answer):
        """Adds a new flashcard to the end of the list."""
        new_card = Node(question, answer)
        if not self.head:
            self.head = new_card
            self.tail = new_card
        else:
            self.tail.next = new_card
            new_card.prev = self.tail
            self.tail = new_card
        return new_card

    def find_card(self, card_id):
        """Finds a card by its ID."""
        current = self.head
        while current:
            if current.card_id == card_id:
                return current
            current = current.next
        return None

    def edit_card(self, card_id, new_question, new_answer):
        """Edits the content of an existing flashcard."""
        card_to_edit = self.find_card(card_id)
        if card_to_edit:
            card_to_edit.question = new_question
            card_to_edit.answer = new_answer
            return True
        return False

    def delete_card(self, card_id):
        """Deletes a flashcard from the list."""
        card_to_delete = self.find_card(card_id)
        if not card_to_delete:
            return False

        if card_to_delete.prev:
            card_to_delete.prev.next = card_to_delete.next
        else: # It's the head
            self.head = card_to_delete.next

        if card_to_delete.next:
            card_to_delete.next.prev = card_to_delete.prev
        else: # It's the tail
            self.tail = card_to_delete.prev

        return True