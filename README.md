This project establishes a complete data lifecycle for a Carbon Footprint Tracker, moving raw user activity data into analytical insights.
Built with a Flask API and MySQL, the system's architecture is centered on demonstrating three core Data Structures and Algorithms.
The saved data is then analyzed via the following methods:

Impact Ranking (Sorting Algorithm): The custom Bubble Sort function fetches the latest calculated breakdown and ranks the activities (Travel, Energy, Food) in descending order (highest impact first).

Historical Trend (BST + Traversal): The Binary Search Tree (BST) manages historical records, keyed by the date. Inorder Traversal is used as the search algorithm to retrieve all data in guaranteed chronological order for accurate trend visualization.

Eco-Suggestions (Trie Data Structure): The Trie (Prefix Tree) is used for instant lookup, providing personalized eco-recommendations in highly efficient O(L) time.

This structure ensures that the system accurately calculates impact, efficiently stores history, and provides necessary analytical proof points.
