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
    def __init__(self, front: str, back: str, category: str = "General", last_reviewed=None):
        self.front = front
        self.back = back
        self.category = category
        self.last_reviewed = last_reviewed or datetime.now()
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
        self.selected_card_for_update = None  # Track which card is selected for update
        
        # NEW: History tracking for previous card functionality
        self.card_history = []  # Stack to store previously viewed cards
        self.current_card_index = -1  # Track current position in history
        
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
        
        # Update category dropdowns
        self.update_all_category_dropdowns()
        
        self.history_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.history_frame, text="Review History")
        self.create_history_tab(self.history_frame)
        
        self.status_bar = tk.Label(self.window, text="Ready", 
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
        tk.Label(left_panel, text="Question:", font=Style.FONT_MEDIUM).pack(anchor='w')
        self.manage_front_entry = tk.Text(left_panel, height=3, width=30, wrap='word', font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
        self.manage_front_entry.pack(pady=2)
        
        tk.Label(left_panel, text="Answer:", font=Style.FONT_MEDIUM).pack(anchor='w')
        self.manage_back_entry = tk.Text(left_panel, height=3, width=30, wrap='word', font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
        self.manage_back_entry.pack(pady=2)
        
        ttk.Label(left_panel, text="Category:", font=Style.FONT_MEDIUM).pack(anchor='w')
        self.manage_category_var = tk.StringVar()
        self.manage_category_combo = ttk.Combobox(left_panel, textvariable=self.manage_category_var, width=27)
        self.manage_category_combo.pack(pady=2)
        
        # Status label for showing current operation
        self.operation_status = tk.Label(left_panel, text="Select a card to edit, or create a new one", 
                                       font=Style.FONT_SMALL, fg=Style.TEXT_SECONDARY, wraplength=250)
        self.operation_status.pack(pady=5)
        
        # CRUD Buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Create New Card", command=self.create_new_card).pack(pady=2, fill='x')
        ttk.Button(button_frame, text="Update Selected Card", command=self.update_card).pack(pady=2, fill='x')
        ttk.Button(button_frame, text="Delete Selected Card", command=self.delete_card).pack(pady=2, fill='x')
        ttk.Button(button_frame, text="Clear Form", command=self.clear_form).pack(pady=2, fill='x')
        
        # Right panel for card list
        right_panel = ttk.LabelFrame(manage_frame, text="All Cards", padding=10)
        right_panel.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Search frame
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', padx=5)
        
        ttk.Label(search_frame, text="Filter by Category:").pack(side='left', padx=(20, 5))
        self.filter_var = tk.StringVar()
        self.filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var, width=15)
        self.filter_combo.pack(side='left', padx=5)
        self.filter_combo.set('All')
        
        # Treeview for displaying cards
        columns = ('Front', 'Back', 'Category', 'Last Studied')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings')
        # Configure columns
        self.tree.heading('Front', text='Front')
        self.tree.heading('Back', text='Back')
        self.tree.heading('Category', text='Category')
        self.tree.heading('Last Studied', text='Last Studied')

        self.tree.column('Front', width=200, anchor='w')
        self.tree.column('Back', width=200, anchor='w')
        self.tree.column('Category', width=120, anchor='w')
        self.tree.column('Last Studied', width=150, anchor='w')
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(right_panel, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_card_select)

        # IMPORTANT: Set up the traces AFTER the tree widget is created
        self.search_var.trace('w', self.filter_cards)
        self.filter_var.trace('w', self.filter_cards)
        
        # Initialize the tree with data
        self.filter_cards()
        
    def filter_cards(self, *args):
        # Check if tree exists before trying to use it
        if not hasattr(self, 'tree'):
            return
            
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
            self.tree.insert('', 'end', values=(card.front, card.back, card.category, last_studied))
            
    def on_card_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            # Populate the form fields with selected card data
            self.manage_front_entry.delete("1.0", tk.END)
            self.manage_front_entry.insert("1.0", values[0])
            self.manage_back_entry.delete("1.0", tk.END)
            self.manage_back_entry.insert("1.0", values[1])
            self.manage_category_var.set(values[2])
            
            # Store the selected card for update operations
            self.selected_card_for_update = {
                'original_front': values[0],
                'original_back': values[1],
                'original_category': values[2]
            }
            
            # Update status
            self.operation_status.config(text="Card selected for editing. Make changes and click 'Update Selected Card'")
            self.status_bar.config(text="Card selected for editing")
        else:
            self.clear_form()
    
    def clear_form(self):
        """Clear all form fields and reset selection"""
        self.manage_front_entry.delete("1.0", tk.END)
        self.manage_back_entry.delete("1.0", tk.END)
        self.manage_category_var.set("")
        self.selected_card_for_update = None
        self.operation_status.config(text="Select a card to edit, or create a new one")
        self.status_bar.config(text="Ready")
        
        # Clear tree selection
        for item in self.tree.selection():
            self.tree.selection_remove(item)
    
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
        
        # Category filter
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(filter_frame, text="Filter by Category:").pack(side=tk.LEFT, padx=5)
        
        self.category_var = tk.StringVar()
        self.study_category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, state="readonly")
        self.study_category_combo.set("All")
        self.study_category_combo.pack(side=tk.LEFT, padx=5)
        self.study_category_combo.bind("<<ComboboxSelected>>", self.refresh_queue)
        
        # NEW: Navigation buttons frame
        nav_frame = ttk.Frame(parent)
        nav_frame.pack(pady=10)
        
        # Previous card button
        self.prev_button = ttk.Button(nav_frame, text="◀ Previous Card", 
                                    command=self.previous_card, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        # Next card button
        self.next_button = ttk.Button(nav_frame, text="Next Card ▶", 
                                    command=self.next_card)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # NEW: Progress indicator
        self.progress_label = ttk.Label(parent, text="", font=Style.FONT_SMALL)
        self.progress_label.pack(pady=5)
        
        # NEW: Start study session button
        ttk.Button(parent, text="Start Study Session", 
                  command=self.start_study_session).pack(pady=10)
    
    def create_add_tab(self, parent):
        ttk.Label(parent, text="Create New Flash Card", font=Style.FONT_LARGE).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Card front (question)
        ttk.Label(parent, text="Question/Front:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.add_front_entry = tk.Text(parent, width=50, height=4, wrap=tk.WORD, font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
        self.add_front_entry.grid(row=1, column=1, pady=5)
        
        # Card back (answer)
        ttk.Label(parent, text="Answer/Back:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.add_back_entry = tk.Text(parent, width=50, height=4, wrap=tk.WORD, font=Style.FONT_MEDIUM, fg=Style.TEXT_PRIMARY, bg=Style.SURFACE)
        self.add_back_entry.grid(row=2, column=1, pady=5)
        
        # Category
        ttk.Label(parent, text="Category:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.add_category_entry = ttk.Entry(parent, width=50)
        self.add_category_entry.grid(row=3, column=1, pady=5)
        
        # Submit button
        ttk.Button(parent, text="Add Flash Card", 
                  command=self.add_new_card).grid(row=4, column=0, columnspan=2, pady=20)
    
    def refresh_queue(self, event=None):
        """Refresh the review queue and reset navigation history"""
        selected_category = self.category_var.get()
        
        if selected_category == "All":
            self.review_queue = self.cards.copy()
        else:
            self.review_queue = [card for card in self.cards if card.category == selected_category]
        
        random.shuffle(self.review_queue)
        
        # Reset navigation history
        self.card_history.clear()
        self.current_card_index = -1
        
        self.update_navigation_buttons()
        self.update_progress_indicator()
        
        # Start with first card
        self.next_card()
    
    def start_study_session(self):
        """Start a new study session"""
        self.refresh_queue()
        self.status_bar.config(text="Study session started!")
    
    def next_card(self):
        """Move to the next card in the queue"""
        # If we're in the middle of history (user went back), remove future cards
        if self.current_card_index < len(self.card_history) - 1:
            self.card_history = self.card_history[:self.current_card_index + 1]
        
        # Get next card from database or queue
        selected_category = self.category_var.get()
        card_data = self.manager.get_next_card(selected_category)
        
        if card_data:
            self.current_card = FlashCard(
                front=card_data['question'],
                back=card_data['answer'],
                category=card_data.get('category', 'General')
            )
        elif self.review_queue:
            # Fallback to local queue if database method fails
            self.current_card = self.review_queue.pop(0)
        else:
            self.current_card = None
        
        if self.current_card:
            # Add to history
            self.card_history.append(self.current_card)
            self.current_card_index = len(self.card_history) - 1
            
            # Display card
            self.display_current_card()
            
            # Update navigation
            self.update_navigation_buttons()
            self.update_progress_indicator()
            
            self.status_bar.config(text=f"Viewing card {self.current_card_index + 1} of {len(self.card_history)}")
        else:
            self.front_label.config(text="No more cards available in this category")
            self.back_label.pack_forget()
            self.show_button.pack_forget()
            self.update_navigation_buttons()
            self.update_progress_indicator()
    
    def previous_card(self):
        """Move to the previous card in history"""
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.current_card = self.card_history[self.current_card_index]
            
            # Display card
            self.display_current_card()
            
            # Update navigation
            self.update_navigation_buttons()
            self.update_progress_indicator()
            
            self.status_bar.config(text=f"Viewing card {self.current_card_index + 1} of {len(self.card_history)}")
    
    def display_current_card(self):
        """Display the current card"""
        if self.current_card:
            self.front_label.config(text=self.current_card.front)
            self.back_label.config(text=self.current_card.back)
            self.back_label.pack_forget()
            self.show_button.pack(pady=10)
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        # Enable/disable previous button
        if self.current_card_index > 0:
            self.prev_button.config(state=tk.NORMAL)
        else:
            self.prev_button.config(state=tk.DISABLED)
        
        # Enable/disable next button
        if self.review_queue or (self.current_card_index < len(self.card_history) - 1):
            self.next_button.config(state=tk.NORMAL)
        else:
            self.next_button.config(state=tk.DISABLED)
    
    def update_progress_indicator(self):
        """Update the progress indicator text"""
        if self.card_history:
            current_pos = self.current_card_index + 1
            total_viewed = len(self.card_history)
            remaining = len(self.review_queue)
            
            if remaining > 0:
                self.progress_label.config(text=f"Card {current_pos} of {total_viewed} viewed | {remaining} remaining")
            else:
                self.progress_label.config(text=f"Card {current_pos} of {total_viewed} viewed | No more cards")
        else:
            self.progress_label.config(text="No cards in session")
    
    def show_answer(self):
        """Show the answer for the current card"""
        self.back_label.pack(pady=20)
        self.show_button.pack_forget()
        
        # Update card review count
        if self.current_card:
            self.current_card.times_reviewed += 1
            self.current_card.last_reviewed = datetime.now()
        
        # Remove the automatic next card after 3 seconds
        # User now has manual control via Previous/Next buttons
    
    def update_all_category_dropdowns(self):
        """Update all category dropdowns with current categories"""
        categories_list = sorted(self.card_categories)
        
        if hasattr(self, 'manage_category_combo'):
            self.manage_category_combo['values'] = categories_list
            
        if hasattr(self, 'study_category_combo'):
            self.study_category_combo['values'] = ["All"] + categories_list
            
        if hasattr(self, 'filter_combo'):
            self.filter_combo['values'] = ['All'] + categories_list
    
    def create_new_card(self):
        """Create a new card using the manage tab form"""
        front = self.manage_front_entry.get("1.0", tk.END).strip()
        back = self.manage_back_entry.get("1.0", tk.END).strip()
        category = self.manage_category_var.get().strip()
        
        if not all([front, back, category]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            # Add to database
            self.manager.add_card_to_db(front, back, category)
            
            # Add to local cards list
            new_card = FlashCard(front, back, category)
            self.cards.append(new_card)
            self.card_categories.add(category)
            
            # Update all category dropdowns
            self.update_all_category_dropdowns()
            
            # Add to review history if available
            if hasattr(self.manager, 'review_history_manager'):
                self.manager.review_history_manager.push(new_card, "Added (not reviewed)")
            
            # Clear form and refresh views
            self.clear_form()
            self.refresh_queue()
            self.filter_cards()
            
            messagebox.showinfo("Success", "Flash card created successfully!")
            self.status_bar.config(text="New card created successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create card: {str(e)}")
    
    def add_new_card(self):
        """Add card from the dedicated Add tab"""
        front = self.add_front_entry.get("1.0", tk.END).strip()
        back = self.add_back_entry.get("1.0", tk.END).strip()
        category = self.add_category_entry.get().strip()
        
        if not all([front, back, category]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            # Add to database
            self.manager.add_card_to_db(front, back, category)
            
            # Add to local cards list
            new_card = FlashCard(front, back, category)
            self.cards.append(new_card)
            self.card_categories.add(category)
            
            # Update all category dropdowns
            self.update_all_category_dropdowns()
            
            # Add to review history if available
            if hasattr(self.manager, 'review_history_manager'):
                self.manager.review_history_manager.push(new_card, "Added (not reviewed)")
            
            # Clear form
            self.add_front_entry.delete("1.0", tk.END)
            self.add_back_entry.delete("1.0", tk.END)
            self.add_category_entry.delete(0, tk.END)
            
            # Refresh views
            self.refresh_queue()
            self.filter_cards()
            
            messagebox.showinfo("Success", "Flash card added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add card: {str(e)}")
    
    def update_card(self):
        """Update the selected card with values from the form"""
        if not self.selected_card_for_update:
            messagebox.showerror("Error", "Please select a card to update first!")
            return

        # Get new values from form
        new_front = self.manage_front_entry.get("1.0", tk.END).strip()
        new_back = self.manage_back_entry.get("1.0", tk.END).strip()
        new_category = self.manage_category_var.get().strip()

        if not all([new_front, new_back, new_category]):
            messagebox.showerror("Error", "Please fill in all fields!")
            return

        try:
            # Find and update the card in the local list
            updated = False
            for card in self.cards:
                if (card.front == self.selected_card_for_update['original_front'] and 
                    card.back == self.selected_card_for_update['original_back'] and 
                    card.category == self.selected_card_for_update['original_category']):
                    
                    # Update the card
                    card.front = new_front
                    card.back = new_back
                    card.category = new_category
                    updated = True
                    break

            if updated:
                # Update categories set
                self.card_categories.add(new_category)
                
                # Update all category dropdowns
                self.update_all_category_dropdowns()
                self.refresh_history()
                self.filter_cards()
                
                # Clear form and selection
                self.clear_form()
                
                messagebox.showinfo("Success", "Card updated successfully!")
                self.status_bar.config(text="Card updated successfully")
            else:
                messagebox.showerror("Error", "Failed to find card to update!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update card: {str(e)}")
            
    def create_history_tab(self, parent):
        columns = ("Front", "Back", "Category", "Times Reviewed")
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
            self.history_tree.insert("", tk.END, values=(card.front, card.back, card.category, card.times_reviewed))
      
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
            self.card_categories = {"General"}  # Default category if loading fails
            
    def delete_card(self):
        """Delete the selected card"""
        if not self.selected_card_for_update:
            messagebox.showerror("Error", "Please select a card to delete first!")
            return
            
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this card?"):
            return
            
        try:
            # Find and remove the card from the local list
            card_to_remove = None
            for card in self.cards:
                if (card.front == self.selected_card_for_update['original_front'] and 
                    card.back == self.selected_card_for_update['original_back'] and 
                    card.category == self.selected_card_for_update['original_category']):
                    card_to_remove = card
                    break
                    
            if card_to_remove:
                self.cards.remove(card_to_remove)
                
                # Remove from database if needed
                # self.manager.delete_card_from_db(card_to_remove.front, card_to_remove.back)
                
                # Refresh views
                self.filter_cards()
                self.refresh_history()
                self.refresh_queue()
                
                # Clear form
                self.clear_form()
                
                messagebox.showinfo("Success", "Card deleted successfully!")
                self.status_bar.config(text="Card deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to find card to delete!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete card: {str(e)}")

# Main application entry point
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    app = FlashCardApp(root)
    root.mainloop()