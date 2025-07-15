from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from main import FlashcardDB
from guiconnection import FlashCardManager
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import random
from review_gui import ReviewHistoryGUI
from linkedlist import LinkedList

# Replace Style withStyle
class Style:
    PRIMARY = "#8B5CF6"
    PRIMARY_DARK = "#7C3AED"
    SECONDARY = "#3B82F6"
    BACKGROUND = "#2FECF0"
    SURFACE = "#FFFFFF"
    SURFACE_DARK = "#F1F5F9"
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    BORDER = "#E2E8F0"
    FONT_LARGE = ("Segoe UI", 16, "bold")
    FONT_MEDIUM = ("Segoe UI", 12)
    FONT_SMALL = ("Segoe UI", 10)
    FONT_BUTTON = ("Segoe UI", 11, "bold")

# Replace empty Button class with Button
class Button(tk.Button):
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        if style == "primary":
            bg = Style.PRIMARY
            fg = "white"
            active_bg = Style.PRIMARY_DARK
        elif style == "secondary":
            bg = Style.SECONDARY
            fg = "white"
            active_bg = "#2563EB"
        else:
            bg = Style.SURFACE
            fg = Style.TEXT_PRIMARY
            active_bg = Style.SURFACE_DARK
        super().__init__(
            parent,
            text=text,
            command=command,
            style='TButton',  # Use ttk style
            **kwargs
        )
        self.configure(style='TButton')
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.original_bg = bg
        self.hover_bg = active_bg
    
    def _on_enter(self, event):
        self.config(background=self.hover_bg)
    
    def _on_leave(self, event):
        self.config(background=self.original_bg)

class FlashCard:
    def __init__(self, front: str, back: str, category: str = "General", last_reviewed=None, difficulty=1):
        self.front = front
        self.back = back
        self.category = category
        self.last_reviewed = last_reviewed or datetime.now()
        self.difficulty = difficulty  # 1-5 scale (1=easy, 5=hard)
        self.times_reviewed = 0

class FlashCardApp:
    def __init__(self, parent, style="primary", **kwargs):
        self.window = tk.Toplevel(parent)
        self.window.title("Flash Card System")
        self.window.geometry("1000x700")
        self.window.configure(bg=Style.BACKGROUND)
        
        MONGO_URI = "mongodb+srv://dominicwaithaka6:12345@flashcardappcluster.sqpcmki.mongodb.net/?retryWrites=true&w=majority&appName=FlashCardAppCluster"
        self.manager = FlashcardDB(MONGO_URI)
        self.cards = LinkedList()
        self.current_card = None
        self.review_queue = []
        
        self.card_categories = set(self.manager.get_categories())
        
        self.load_initial_data()
        self.setup_styles()
        self.create_widgets()
        self.refresh_queue()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', 
                      foreground='white', 
                      background=Style.PRIMARY,
                      font=Style.FONT_BUTTON,
                      padding=6)
        style.map('TButton', 
                 background=[('active', Style.PRIMARY_DARK)])
        style.configure('Treeview', font=Style.FONT_MEDIUM)
        style.configure('Treeview.Heading', 
                      font=Style.FONT_MEDIUM, 
                      foreground=Style.TEXT_PRIMARY, 
                      background=Style.SURFACE)
        
    def create_widgets(self):
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Manage cards tab
        self.create_manage_tab(self.notebook)
        
        # Study Tab
        self.study_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.study_frame, text="Cards")
        self.create_study_tab(self.study_frame)
        
        # Add Card Tab
        self.add_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.add_frame, text="Add New Card")
        self.create_add_tab(self.add_frame)
        
        self.manage_category_combo['values'] = ["All"] + sorted(self.card_categories)
        self.study_category_combo['values'] = ["All"] + sorted(self.card_categories)
        
        self.history_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.history_frame, text="Review History")
        self.create_history_tab(self.history_frame)
        
        self.status_bar = tk.Label(self.window, text="", 
                                 bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)  
       
    def create_manage_tab(self, notebook):
        # Manage Cards Tab
        manage_frame = ttk.Frame(notebook)
        notebook.add(manage_frame, text="Manage Cards")
        
        # Left panel for CRUD operations
        left_panel = ttk.LabelFrame(manage_frame, text="Card Operations", padding=10)
        left_panel.pack(side='left', fill='y', padx=5, pady=5)
        
        # Create card section
        tk.Label(left_panel, text="Question:").pack(anchor='w')
        self.front_entry = tk.Text(left_panel, height=3, width=30, wrap='word', font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
        self.front_entry.pack(pady=2)
        
        tk.Label(left_panel, text="Answer:").pack(anchor='w')
        self.back_entry = tk.Text(left_panel, height=3, width=30, wrap='word', font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
        self.back_entry.pack(pady=2)
        
        ttk.Label(left_panel, text="Category:").pack(anchor='w')
        self.category_var = tk.StringVar()
        self.manage_category_combo = ttk.Combobox(left_panel, textvariable=self.category_var, width=27)
        self.manage_category_combo.pack(pady=2)
        self.update_category_dropdown()
        
        # CRUD Buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Create Card", command=self.go_to_add_tab).pack(pady=2, fill='x')
        ttk.Button(button_frame, text="Update Card", command=self.update_card).pack(pady=2, fill='x')
        ttk.Button(button_frame, text="Delete Card", command=self.delete_card).pack(pady=2, fill='x')
        
        # Right panel for card list
        right_panel = ttk.LabelFrame(manage_frame, text="All Cards", padding=10)
        right_panel.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Search frame
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        # self.search_var.trace('w', self.filter_cards)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', padx=5)
        
        ttk.Label(search_frame, text="Filter by Category:").pack(side='left', padx=(20, 5))
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self.filter_cards)
        filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var, width=15)
        filter_combo.pack(side='left', padx=5)
        filter_combo['values'] = ['All'] + list(self.card_categories)
        filter_combo.set('All')
        
        # Treeview for displaying cards
        columns = ('Front', 'Back', 'Category', 'Difficulty', 'Last Studied')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings')
        # Configure columns
        self.tree.heading('Front', text='Front')
        self.tree.heading('Back', text='Back')
        self.tree.heading('Category', text='Category')
        self.tree.heading('Difficulty', text='Difficulty')
        self.tree.heading('Last Studied', text='Last Studied')

        self.tree.column('Front', width=150, anchor='w')
        self.tree.column('Back', width=150, anchor='w')
        self.tree.column('Category', width=100, anchor='w')
        self.tree.column('Difficulty', width=80, anchor='w')
        self.tree.column('Last Studied', width=120, anchor='w')
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(right_panel, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_card_select)

        # Now set up the traces
        self.search_var.trace('w', self.filter_cards)
        self.filter_var.trace('w', self.filter_cards)
        
    def filter_cards(self, *args):
        search_term = self.search_var.get().lower()
        category_filter = self.filter_var.get()
           # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Filter and add cards
        for card in self.cards:
            # Apply search filter   
            if search_term and search_term not in card.front.lower() and search_term not in card.back.lower():
                continue
            # Apply category filter
            if category_filter and category_filter != 'All' and card.category != category_filter:
                continue
            last_studied = getattr(card, 'last_reviewed', '')
            if last_studied:
                last_studied = str(last_studied)
            self.tree.insert('', 'end', values=(card.front, card.back, card.category, card.difficulty, last_studied))
            
    def on_card_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            self.front_entry.delete("1.0", tk.END)
            self.front_entry.insert("1.0", values[0])
            self.back_entry.delete("1.0", tk.END)
            self.back_entry.insert("1.0", values[1])
            self.category_var.set(values[2])                
    
    def create_study_tab(self, parent):
        # Current card display
        self.card_frame = ttk.LabelFrame(parent, text="Current Flash Card", padding="20")
        self.card_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Front of card (question)
        self.front_label = ttk.Label(self.card_frame, text="Click 'Start Study Session' to begin", font=Style.FONT_LARGE)
        self.front_label.pack(fill='both', expand=True, pady=20)
        
        # Back of card (answer) - initially hidden
        self.back_label = ttk.Label(self.card_frame, text="", font=Style.FONT_MEDIUM)
        
        # Show answer button
        self.show_button = ttk.Button(self.card_frame, text="Show Answer", 
                                    command=self.show_answer)
        self.show_button.pack(pady=10)
        
        # Difficulty buttons (hidden until answer is shown)
        self.difficulty_frame = ttk.Frame(self.card_frame)
        
        ttk.Label(self.difficulty_frame, text="How well did you know this?", font=Style.FONT_MEDIUM).pack()
        
        button_frame = ttk.Frame(self.difficulty_frame)
        button_frame.pack(pady=5)
        
        self.difficulty_buttons = []
        for i in range(1, 6):
            btn = ttk.Button(button_frame, text=str(i), 
                            command=lambda d=i: self.rate_difficulty(d))
            btn.pack(side=tk.LEFT, padx=2)
            self.difficulty_buttons.append(btn)
        
        # Category filter
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(filter_frame, text="Filter by Category:").pack(side=tk.LEFT, padx=5)
        
        self.category_var = tk.StringVar()
        self.study_category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, values=["All"] + sorted(self.card_categories), state="readonly")
        self.study_category_combo.set("All")
        self.study_category_combo.pack(side=tk.LEFT, padx=5)
        self.study_category_combo.bind("<<ComboboxSelected>>", self.refresh_queue)
        self.study_category_combo['value'] = ["All"] + sorted(self.card_categories if hasattr(self, 'card_categories') else [])
        
        print(f"Debug - categories: {hasattr(self, 'card_categories')}")
        print(f"Debug - cards: {hasattr(self, 'cards')}")
        
        # Next card button
        ttk.Button(parent, text="Next Card", 
                  command=self.next_card).pack(pady=10)
    
    def create_add_tab(self, notebook):
        ttk.Label(self.add_frame, text="Create New Flash Card", font=Style.FONT_LARGE).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Card front (question)
        ttk.Label(self.add_frame, text="Question/Front:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.front_entry = tk.Text(self.add_frame, width=50, height=4, wrap=tk.WORD, font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
        self.front_entry.grid(row=1, column=1, pady=5)
        
        # Card back (answer)
        ttk.Label(self.add_frame, text="Answer/Back:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.back_entry = tk.Text(self.add_frame, width=50, height=4, wrap=tk.WORD, font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
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
            
            # Cards rated harder will appear again sooner
            if hasattr(self.manager, 'review_history_manager'):
                 self.manager.review_history_manager.push(self.current_card, f"Difficulty: {difficulty}")
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
        self.cards.append(new_card)
        self.cards.append(FlashCard(front, back, category))
        self.card_categories.add(category)
        
        self.update_category_dropdown()
        if hasattr(self.manager, 'review_history_manager'):
            self.manager.review_history_manager.push(new_card, "Added( not reviewed)")
        
        # Clear form
        self.front_entry.delete("1.0", tk.END)
        self.back_entry.delete("1.0", tk.END)
        self.category_entry.delete(0, tk.END)
        
        messagebox.showinfo("Success", "Flash card added successfully!")
        self.refresh_queue()
        
    def go_to_add_tab(self):
        self.notebook.select(self.add_frame)
        
    def update_category_dropdown(self):
        """Update the category dropdown with current categories"""
        self.manage_category_combo['values'] = ["All"] + sorted(self.card_categories)
        
    def update_card(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a card to update!")
            return

        item_id = selection[0]
        item = self.tree.item(item_id)
        values = item["values"]
        # Get the original front and back to find the node
        original_front = values[0]
        original_back = values[1]

        new_front = self.front_entry.get("1.0", tk.END).strip()
        new_back = self.back_entry.get("1.0", tk.END).strip()
        new_category = self.category_var.get().strip()

        if not new_front or not new_back:
            messagebox.showerror("Error", "Both front and back are required!")
            return

        # Match card using front and back (fallback since ID isn’t stored in TreeView yet)
        matched_node = None
        for card in self.cards:
            if hasattr(card, "front") and hasattr(card, "back") and card.front == original_front and card.back == original_back:
                matched_node = card
                break

        if matched_node:
            matched_node.front = new_front
            matched_node.back = new_back
            matched_node.category = new_category or "General"

            # Sync update to MongoDB
            try:
                if hasattr(self.manager, "edit_card_in_db"):
                    # If you have a unique identifier for the card, use it here. Otherwise, update by front/back/category.
                    self.manager.edit_card_in_db(new_front, new_back, new_category)
            except Exception as e:
                print(f"Mongo update failed: {e}")

            self.refresh_history()
            self.update_category_dropdown()
            self.refresh_queue()
            messagebox.showinfo("Success", "Card updated successfully!")
        else:
            messagebox.showerror("Error", "Failed to locate the selected card in memory.")
     
        
    def create_history_tab(self, parent):
        columns = ("Front", "Back", "Category", "Difficulty")
        self.history_tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150, anchor='w')
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        ttk.Button(parent, text="Refresh History", command=self.refresh_history).pack(pady=10)
        self.refresh_history()

    def refresh_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        for card in self.cards:
            self.history_tree.insert("", tk.END, values=(card.front, card.back, card.category, card.difficulty))
      
 
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
            
       
    def delete_card(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a card to delete!")
            return

        item = self.tree.item(selection[0])
        values = item['values']
        deleted = False
        # Loop over a copy to avoid issues while removing
        for card in self.cards[:]:  # iterate over a copy
            if card.front == values[0] and card.back == values[1] and card.category == values[2]:
                self.cards.remove(card)
                deleted = True
                break

        if deleted:
            self.refresh_history()
            self.refresh_history()
            self.update_category_dropdown()
            messagebox.showinfo("Success", "Card deleted successfully!")
        else:
            messagebox.showerror("Error", "Failed to delete card!")     
        
        
# Example usage:
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    app = FlashCardApp(root)
    root.mainloop()
    
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Accent.TButton', foreground='white', background='#007acc')
    style.map('Accent.TButton', background=[('active', '#005a9e')])
    
    style.configure("Treeview", font=Style.FONT_MEDIUM)
    style.configure("Treeview.Heading", font=Style.FONT_MEDIUM, foreground=Style.TEXT_PRIMARY, background=Style.SURFACE)
    
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()