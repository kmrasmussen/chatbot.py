from uuid import uuid4
import time
import pickle

class Node:
    def __init__(self, parent_id, content, role):
        self.parent_id = parent_id
        self.content = content
        self.role = role
        self.id = str(uuid4())
        self.timestamp = time.time()

    # get string
    def __str__(self):
        return f'Node {self.id} <{self.role}>: {self.content}'

class Nodes:
    def __init__(self):
        self.nodes = {}
        self.latest_node_id = None

    def add_node(self, parent_id, content, role):
        node = Node(parent_id, content, role)
        self.nodes[node.id] = node
        self.latest_node_id = node.id
        return node

    def save_as_pickle(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    def traverse_back_from(self, node_id):
        traverse_list = []
        node = self.nodes[node_id]
        while node:
            traverse_list.append(node)
            node = self.nodes.get(node.parent_id)
        # reverse
        traverse_list.reverse()
        return traverse_list

    def traverse_back_from_latest(self):
        if self.latest_node_id is None:
            return []
        return self.traverse_back_from(self.latest_node_id)

    def traversal_list_to_dict_list(traverse_list):
        return [{'role': node.role, 'content': node.content} for node in traverse_list]

    def get_messages(self):
        return Nodes.traversal_list_to_dict_list(
            self.traverse_back_from_latest())

    def prefix2id(self, prefix):
        matches = []
        for node_id, node in self.nodes.items():
            if node_id.startswith(prefix):
                matches.append(node)
                if len(matches) > 1:
                    return None
        return matches[0] if len(matches) == 1 else None

class CodeBlocks:
    def __init__(self):
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)

    def save_as_pickle(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

