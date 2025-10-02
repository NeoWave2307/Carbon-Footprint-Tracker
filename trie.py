class TrieNode:
    """Represents a single node in the Trie data structure."""
    def __init__(self):
        self.children = {} 
        # suggestion is a list to hold multiple strings.
        self.suggestions = [] 

class Trie:
    """The main Trie class to manage the structure."""
    def __init__(self):
        self.root = TrieNode()

    #  suggestion parameter is now expected to be a LIST of strings
    def insert(self, item, suggestions: list):
        """Inserts an item (key) and its list of recommendations (value)."""
        node = self.root
        for char in item:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        # Store the list of suggestions
        node.suggestions = suggestions

    # The search method returns the list of suggestions or an empty list
    def search(self, prefix):
        """Searches for a prefix and returns the list of stored suggestions."""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return [] # Return empty list if prefix path is not found
            node = node.children[char]
            
        # Return the list of suggestions found at the end of the path
        return node.suggestions