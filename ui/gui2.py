from main import FlashcardDB

class FlashCardManager:
    def __init__(self, connection_string):
        self.db = FlashcardDB(connection_string)
        
    def get_categories(self):
        """Get all unique categories"""
        return ["All"] + sorted(self.db.get_categories())
    
    def get_next_card(self, category_filter="All"):
        """get next card to study"""
        if category_filter == "All":
            return self.db.queue.dequeue_card()
        else:
            # Find first card matching category
            prev = None
            current = self.db.queue.front    
            while current:
                if current.category == category_filter:
                    # Remove this card from queue
                    if prev is None:
                     return self.db.queue.front
                else:
                     prev.next = current.next
                    
                if current == self.db.queue.front:
                    return self.db.queue.dequeue_card()
                else:
                        # implementation of the removal from middle of queue
                        ##returning the first matching card
                    temp = current
                    current = None # Break loop
                    return temp
                return None
                    
    def add_card(self, front, back, category):
        """Add new flashcard"""
        return self.db.add_card_to_db(front, back, category)
    
    def record_review(self, card_id, difficulty):
        """record card review results"""
        self.db.update_card_after_review(card_id, difficulty)
        if difficulty >= 4:
            #Re-add difficult cards to queue
            card = self.db.linked_list.find_card(card_id)
            if card:
                self.db.queue.enqueue_card(card)
    
        
          
        
                
                
                