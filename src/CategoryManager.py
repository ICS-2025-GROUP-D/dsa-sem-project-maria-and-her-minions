# category_manager.py

from linkedlist import Node 

class CategoryManager:
    def __init__(self):
        self.categories = {}  

    def add_to_category(self, category, node):
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(node)

    def remove_from_category(self, category, node):
        if category in self.categories and node in self.categories[category]:
            self.categories[category].remove(node)
            if not self.categories[category]:  
                del self.categories[category]

    def update_category(self, old_category, new_category, node):
        self.remove_from_category(old_category, node)
        self.add_to_category(new_category, node)

    def get_by_category(self, category):
        return self.categories.get(category, [])

    def list_categories(self):
        return list(self.categories.keys())



class CategoryManager:
    def __init__(self):
        self.categories = {}  # key: category name, value: list of flashcard nodes

    def add_to_category(self, category, node):
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(node)

    def remove_from_category(self, category, node):
        if category in self.categories and node in self.categories[category]:
            self.categories[category].remove(node)
            if not self.categories[category]:  # cleanup if empty
                del self.categories[category]

    def update_category(self, old_category, new_category, node):
        self.remove_from_category(old_category, node)
        self.add_to_category(new_category, node)

    def get_by_category(self, category):
        return self.categories.get(category, [])

    def list_categories(self):
        return list(self.categories.keys())
