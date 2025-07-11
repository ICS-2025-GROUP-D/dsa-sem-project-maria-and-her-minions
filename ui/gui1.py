from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from main import FlashcardDB
import tkinter as tk
from tkinter import ttk, messagebox
import random

class FlashCard:
    def __init__(self, front, back, category="General", last_reviewed=None, difficulty=1):
        self.front = front
        self.back = back
        self.category = category
        self.last_reviewed = last_reviewed or datetime.now()
        self.difficulty = difficulty  # 1-5 scale (1=easy, 5=hard)
        self.times_reviewed = 0

class FlashCardApp:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Flash Card System")
        self.window.geometry("800x600")
        
        MONGO_URI = "mongodb+srv://dominicwaithaka6:12345@flashcardappcluster.sqpcmki.mongodb.net/?retryWrites=true&w=majority&appName=FlashCardAppCluster"
        self.manager = FlashcardDB(MONGO_URI)

        self.cards = []
        self.current_card = None
        self.review_queue = []
        
        self.card_categories = set(self.manager.get_categories())
        
        self.load_initial_data()

        self.create_widgets()
        self.refresh_queue()
        
    def create_widgets(self):
        # Main notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Study Tab
        self.study_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.study_frame, text="Study Cards")
        
        # Add Card Tab
        self.add_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.add_frame, text="Add New Card")
        
        self.create_study_tab()
        self.create_add_tab()
        
        self.category_combo['values'] = self.manager.get_categories()
        
    
    def create_study_tab(self):
        # Current card display
        self.card_frame = ttk.LabelFrame(self.study_frame, text="Current Flash Card", padding="20")
        self.card_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Front of card (question)
        self.front_label = ttk.Label(self.card_frame, text="", 
                                   font=("Arial", 16, "bold"), 
                                   wraplength=600, justify="center")
        self.front_label.pack(pady=20)
        
        # Back of card (answer) - initially hidden
        self.back_label = ttk.Label(self.card_frame, text="", 
                                  font=("Arial", 14), 
                                  wraplength=600, justify="center")
        
        # Show answer button
        self.show_button = ttk.Button(self.card_frame, text="Show Answer", 
                                    command=self.show_answer)
        self.show_button.pack(pady=10)
        
        # Difficulty buttons (hidden until answer is shown)
        self.difficulty_frame = ttk.Frame(self.card_frame)
        
        ttk.Label(self.difficulty_frame, text="How well did you know this?").pack()
        
        button_frame = ttk.Frame(self.difficulty_frame)
        button_frame.pack(pady=5)
        
        self.difficulty_buttons = []
        for i in range(1, 6):
            btn = ttk.Button(button_frame, text=str(i), 
                            command=lambda d=i: self.rate_difficulty(d))
            btn.pack(side=tk.LEFT, padx=2)
            self.difficulty_buttons.append(btn)
        
        # Category filter
        filter_frame = ttk.Frame(self.study_frame)
        filter_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(filter_frame, text="Filter by Category:").pack(side=tk.LEFT, padx=5)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(filter_frame, 
                                         textvariable=self.category_var, 
                                         values=["All"] + sorted(self.card_categories),
                                         state="readonly")
        self.category_combo.set("All")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.refresh_queue)
        self.category_combo['value'] = ["All"] + sorted(self.card_categories if hasattr(self, 'card_categories') else [])
        
        print(f"Debug - categories: {hasattr(self, 'card_categories')}")
        print(f"Debug - cards: {hasattr(self, 'cards')}")
        
        # Next card button
        ttk.Button(self.study_frame, text="Next Card", 
                  command=self.next_card).pack(pady=10)
    
    def create_add_tab(self):
        ttk.Label(self.add_frame, text="Create New Flash Card", 
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Card front (question)
        ttk.Label(self.add_frame, text="Question/Front:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.front_entry = tk.Text(self.add_frame, width=50, height=4, wrap=tk.WORD)
        self.front_entry.grid(row=1, column=1, pady=5)
        
        # Card back (answer)
        ttk.Label(self.add_frame, text="Answer/Back:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.back_entry = tk.Text(self.add_frame, width=50, height=4, wrap=tk.WORD)
        self.back_entry.grid(row=2, column=1, pady=5)
        
        # Category
        ttk.Label(self.add_frame, text="Category:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.category_entry = ttk.Entry(self.add_frame, width=50)
        self.category_entry.grid(row=3, column=1, pady=5)
        
        # Submit button
        ttk.Button(self.add_frame, text="Add Flash Card", 
                  command=self.add_new_card).grid(row=4, column=0, columnspan=2, pady=20)
    
    def refresh_queue(self, event=None):
        selected_category = self.category_var.get()
        
        if selected_category == "All":
            self.review_queue = self.cards.copy()
        else:
            self.review_queue = [card for card in self.cards if card.category == selected_category]
        
        random.shuffle(self.review_queue)
        self.next_card()
    
    def next_card(self):
        selected_category = self.category_var.get()
        card_data = self.manager.get_next_card(selected_category)
        if card_data:
            self.current_card = FlashCard(
                front=card_data['question'],
                back=card_data['answer'],
                category=card_data.get('category', 'General')
            )
        else:
            self.current_card = None
        
        if self.current_card:
            self.front_label.config(text=self.current_card.front)
            self.back_label.config(text=self.current_card.back)
            self.back_label.pack_forget()
            self.show_button.pack()
            self.difficulty_frame.pack_forget()
            root.mainloop()
        else:
            self.front_label.config(text="No cards available in this category")
            self.back_label.pack_forget()
            self.show_button.pack_forget()
            self.difficulty_frame.pack_forget()
        
        
        if not self.review_queue:
            self.front_label.config(text="No cards available in this category")
            self.back_label.pack_forget()
            self.show_button.pack_forget()
            self.difficulty_frame.pack_forget()
            return
        
        self.current_card = self.review_queue.pop(0)
        self.front_label.config(text=self.current_card.front)
        self.back_label.config(text=self.current_card.back)
        self.back_label.pack_forget()
        self.show_button.pack()
        self.difficulty_frame.pack_forget()
    
    def show_answer(self):
        self.back_label.pack(pady=20)
        self.show_button.pack_forget()
        self.difficulty_frame.pack(pady=10)
    
    def rate_difficulty(self, difficulty):
        if self.current_card:
            self.current_card.difficulty = difficulty
            self.current_card.last_reviewed = datetime.now()
            self.current_card.times_reviewed += 1
            # Record review with manager instead of local handling
            self.manager.record_review(self.current_card.card_id, difficulty)
            
            # Cards rated harder will appear again sooner
            if difficulty >= 4:
                self.review_queue.append(self.current_card)
            
            self.next_card()
    
    def add_new_card(self):
        front = self.front_entry.get("1.0", tk.END).strip()
        back = self.back_entry.get("1.0", tk.END).strip()
        category = self.category_entry.get().strip()
        
        if not all([front, back, category]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        self.manager.add_card_to_db(front, back, category)
        
        new_card = FlashCard(front, back, category)
        self.cards.append(FlashCard(front, back, category))
        self.card_categories.add(category)
        
        self.update_category_dropdown()
        
        # Clear form
        self.front_entry.delete("1.0", tk.END)
        self.back_entry.delete("1.0", tk.END)
        self.category_entry.delete(0, tk.END)
        
        messagebox.showinfo("Success", "Flash card added successfully!")
        self.refresh_queue()
        
        
    def update_category_dropdown(self):
        """Update the category dropdown with current categories"""
        self.category_combo['values'] = ["All"] + sorted(self.card_categories)
 
    def load_initial_data(self):
        try:
            db_cards = self.manager.get_all_cards()  # You'll need to implement this in FlashcardDB
            self.cards = [FlashCard(
            front=card['question'],
            back=card['answer'],
            category=card.get('category', 'General')
        ) for card in db_cards]
        
        # Initialize categories
            self.card_categories = {card.category for card in self.cards}
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load initial data: {e}")
            self.card_categories = set()
            self.cards = [ FlashCard(
                front=card['front'],
                back=card['back'],
                category=card['category']
            )for card in db_cards]
        
        
# Example usage:
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    app = FlashCardApp(root)
    root.mainloop()