from linkedlist import Node

class FlashcardQueue:
    def __init__(self):
        """Initializes an empty queue."""
        self.front = None
        self.rear = None
        self.size = 0

    def enqueue_card(self, node):
        """Adds a new flashcard node to the end of the queue."""
        if not isinstance(node, Node):
            raise TypeError("Only Node objects can be enqueued.")

        node.next = None  # Reset just in case
        node.prev = None

        if self.rear is None:
            # Queue is empty — this node is both front and rear
            self.front = self.rear = node
        else:
            # Link the new node at the rear
            self.rear.next = node
            node.prev = self.rear
            self.rear = node

        self.size += 1
        print(f"Enqueued: {node.question}")

    def dequeue_card(self):
        """Removes and returns the front node (the next flashcard)."""
        if self.front is None:
            raise IndexError("Queue is empty, cannot dequeue.")

        dequeued_node = self.front
        self.front = self.front.next

        if self.front is None:
            # Queue is now empty
            self.rear = None
        else:
            self.front.prev = None

        dequeued_node.next = None  # Cleanup
        dequeued_node.prev = None
        self.size -= 1

        print(f"Dequeued: {dequeued_node.question}")
        return dequeued_node

    def peek_card(self):
        """Returns the next flashcard without removing it."""
        if self.front is None:
            raise IndexError("Queue is empty, cannot peek.")

        return self.front

    def is_empty(self):
        """Returns True if the queue is empty."""
        return self.size == 0

    def show_queue(self):
        """Displays all cards in the queue."""
        current = self.front
        if not current:
            print("Queue is empty.")
            return

        print("Current Flashcard Queue:")
        while current:
            print(f"{current.question} (ID: {current.card_id})")
            current = current.next
        print("End of Queue\n")
