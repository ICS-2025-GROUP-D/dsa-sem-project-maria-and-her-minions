import tkinter as tk
from tkinter import messagebox
from bson import ObjectId  # Simulate MongoDB-style unique IDs

from ReviewHistory import ReviewHistory
from linkedlist import Node  # ✅ Updated import

# Create mock flashcards using the Node class
mock_node1 = Node("What is Python?", "A high-level programming language", ObjectId())
mock_node2 = Node("What is 2 + 2?", "4", ObjectId())

# Initialize the review history and add mock cards
history = ReviewHistory()
history.push(mock_node1, "Correct")
history.push(mock_node2, "Incorrect")


class ReviewHistoryGUI:
    def __init__(self, master, review_history):
        self.master = master
        self.master.title("Flashcard Review History")
        self.review_history = review_history

        self.frame = tk.Frame(master)
        self.frame.pack(padx=20, pady=20)

        self.title = tk.Label(self.frame, text="Reviewed Flashcards", font=("Arial", 16, "bold"))
        self.title.pack()

        self.listbox = tk.Listbox(self.frame, width=60, height=10)
        self.listbox.pack(pady=10)

        self.clear_button = tk.Button(self.frame, text="Clear History", command=self.clear_history, bg="red", fg="white")
        self.clear_button.pack()

        self.refresh_history()

    def refresh_history(self):
        self.listbox.delete(0, tk.END)
        if not self.review_history.history:
            self.listbox.insert(tk.END, "No review history available.")
        else:
            for entry in self.review_history.history.values():
                line = f"{entry['question']} -> {entry['answer']} [Review: {entry['review']}]"
                self.listbox.insert(tk.END, line)

    def clear_history(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the review history?"):
            self.review_history.clear_history()
            self.refresh_history()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewHistoryGUI(root, history)
    root.mainloop()
