class Node:
    """A single node in the Binary Search Tree."""
    def __init__(self, date, value):
        self.date = date
        self.value = value
        self.left = None
        self.right = None

class BST:
    """Manages the Binary Search Tree structure."""
    def __init__(self):
        self.root = None #initially is none before the first insertion 

    def insert(self, date, value):
        """Inserts a new record (date and value) into the BST."""
        new_node = Node(date, value)
        if self.root is None:
            self.root = new_node
        else:
            self._insert_recursive(self.root, new_node)

    def _insert_recursive(self, current_node, new_node):
        """A helper method for the recursive insertion process."""
        # We compare based on date (the key)
        if new_node.date < current_node.date:
            if current_node.left is None:
                current_node.left = new_node
            else:
                self._insert_recursive(current_node.left, new_node)
        elif new_node.date > current_node.date:
            if current_node.right is None:
                current_node.right = new_node
            else:
                self._insert_recursive(current_node.right, new_node)
        # Note: We skip the case where dates are equal for simplicity

    def get_inorder_traversal(self):
        """
        Performs an inorder traversal to get a sorted list of all records.
        This is a search algorithm.
        """
        results = []
        self._inorder_recursive(self.root, results)
        return results

    def _inorder_recursive(self, node, results):
        """A helper method for the recursive traversal."""
        if node:
            self._inorder_recursive(node.left, results)
            # Collect the data when the node is visited
            results.append({"date": node.date, "total_em": node.value})
            self._inorder_recursive(node.right, results)