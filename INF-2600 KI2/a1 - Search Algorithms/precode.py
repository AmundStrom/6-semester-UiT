import matplotlib.pyplot as plt
import random
import numpy as np
import tracemalloc
from time import time

class Node:
    def __init__(self, config, depth, parent=None):
        self.config = config
        self.depth = depth
        self.parent = parent
        self.heuristic = 0
        self.children = []

    def add_child(self, config, depth):
        node = Node(config, depth, parent=self)
        self.children.append(node)

class CubeTower:
    def __init__(self, configuration, parent=None):
        """
        Initializes the cube tower with a given configuration.
        :param configuration: A list of the front-facing colors of the cubes in the tower, starting from the bottom.
        :param parent: The parent node of the current node. (can be used for tracing back the path)
        """
        self.order = ['red', 'blue', 'green','yellow']
        self.height = len(configuration)

        self.root = Node(configuration, 0, parent)

        self.curr_node = self.root

        self.configuration = configuration
        self.parent = parent

    def visualize(self):
        """
        Visualizes the current state of the cube tower showing only the front-facing side.
        """
        fig, ax = plt.subplots()
        cube_size = 1  # Size of the cube

        for i, cube in enumerate(self.root.config):
            # Draw only the front-facing side of the cube
            color = cube
            rect = plt.Rectangle((0.5 - cube_size / 2, i), cube_size, cube_size, color=color)
            ax.add_patch(rect)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, self.height)
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        plt.show()

    def visualize_path(self):
        """
        Visualizes the path taken to reach this state from the initial state.
        """
        path = self.get_path()
        fig, ax = plt.subplots()
        cube_size = 1

        for i, configuration in enumerate(path):
            for j, cube in enumerate(configuration):
                color = cube
                rect = plt.Rectangle((i + 0.5 - cube_size / 2, j), cube_size, cube_size, color=color)
                ax.add_patch(rect)

        ax.set_xlim(0, len(path))
        ax.set_ylim(0, self.height)
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        plt.show()

    def get_path(self):
        """
        Retrieves the path taken to reach this state from the initial state.
        """
        node = self.curr_node

        path = []
        current = self
        while current.curr_node.parent is not None:
            path.append(current.curr_node.config)
            current.curr_node = current.curr_node.parent
        path.append(self.root.config)
        path.reverse()

        self.curr_node = node

        return path
    
    def check_cube(self):
        """
        Check if the cube tower is solved, i.e. all cubes are of the same color.
        """
        return len(set(self.curr_node.config)) == 1

    def rotate_cube(self, index, hold_index=None):
        """
        Rotates a cube and all cubes above it, or up to a held cube.
        :param index: The index of the cube to rotate.
        :param hold_index: The index of the cube to hold, if any.
        """
        # Create copy of current config
        config = self.curr_node.config.copy()

        # "Rotate" the cube(s) by giving them new colors
        for i in range(index, hold_index):
            color = config[i]
            color_index = self.order.index(color)
            config[i] = self.order[(color_index + 1) % 4]

        # return new config
        return config
    
    def rotate_all(self):
        """
        Rotates the current Tower in every possible way.
        Each rotation result is added as a child for the Tower.
        """
        index, index_hold = 0, 1

        while index < self.height:
            
            # Skip redundent rotation
            if not (index == 0 and index_hold == self.height):
                # Add new child
                self.curr_node.add_child(self.rotate_cube(index, index_hold), self.curr_node.depth + 1)

            
            # Increment hold index
            if index_hold < self.height:
                index_hold += 1
            # Increment index
            else:
                index += 1
                index_hold = index + 1


def bfs_queue(node_list : list, node : Node, _):
    return node_list.append(node)


def dfs_stack(node_list : list, node : Node, insert_index : int):
    return node_list.insert(insert_index, node)


# General Search used by DFS and BFS
def _search(tower : CubeTower, func : callable):
    
    # Dictionary used for keeping track of which configurations have already been seen
    # key: 'configuration', value: 'instance of node'
    key = ''.join(tower.curr_node.config)
    config_dict = {key : tower.curr_node}

    # List used for visiting next node
    node_list = [tower.curr_node]

    index_counter = 0

    count = 0

    while len(node_list) != 0:
        count += 1

        # Check if current node is the solution
        if tower.check_cube() == 1:
            break

        # Do every rotation possible for current node
        tower.rotate_all()

        # Populate the dictionary, and populate the list only if the node has never been seen
        for node in tower.curr_node.children:
            assert isinstance(node, Node)

            # Use config as key
            key = ''.join(node.config)

            # Check if key already exists
            if key in config_dict:
                # If key already exists, check which node instance has the lowest depth
                if config_dict[key].depth > node.depth:
                    config_dict[key] = node
            else:
                # Populate the dictionary
                config_dict[key] = node

                # Populate the list
                func(node_list, node, index_counter)
                index_counter += 1

        index_counter = 0

        # Move to next node in the list
        tower.curr_node = node_list[0]
        node_list.pop(0)

    print("Node visited: ", count)


# Depth-First Search
def dfs_search(tower : CubeTower):

    _search(tower, dfs_stack)


# Breadth-First Search
def bfs_search(tower : CubeTower):

    _search(tower, bfs_queue)


def a_star_evaluation(tower : CubeTower, node : Node):
    return node.depth + check_heuristic(node.config, tower.order)


def gbfs_evaluation(tower : CubeTower, node : Node):
    return check_heuristic(node.config, tower.order)


# Calculate the heuristic value of a node
def check_heuristic(config, order):

    # Find the node that has the highest index in the color order
    val = 0
    for i in range(len(config)):
        if order.index(config[i]) > val:
            val = order.index(config[i])

    # Calculate the difference between the highest index and the rest of the indexes
    sum = 0
    for i in range(len(config)):
        sum += val - order.index(config[i])

    return sum


# General search heuristic search used by A* and GBFS
def _heuristic_search(tower : CubeTower, func : callable):
    
    # Dictionary used for keeping track of which configurations have already been seen
    # key: 'configuration', value: 'instance of node'
    key = ''.join(tower.curr_node.config)
    config_dict = {key : tower.curr_node}

    # Priority queue used for visiting next node, the lowest value is prioritized
    prio_queue = [tower.curr_node]

    count = 0

    while len(prio_queue) != 0:

        count += 1

        # Check if current node is the solution
        if tower.check_cube() == 1:
            break

        # Do every rotation possible for current node
        tower.rotate_all()

        # Populate the dictionary, and populate the stack only if the node has never been seen
        for node in tower.curr_node.children:
            assert isinstance(node, Node)

            # Use config as key
            key = ''.join(node.config)

            # Calculate heuristic for node
            node.heuristic = func(tower, node)

            # Check if key already exists
            if key in config_dict:
                # If key already exists, check which node instance has the lowest heuristic
                if config_dict[key].heuristic > node.heuristic:
                    config_dict[key] = node
            else:
                # Populate the dictionary
                config_dict[key] = node

                # Populate the queue
                prio_queue.append(node)

        # Sort priority queue
        prio_queue = sorted(prio_queue, key=lambda node: node.heuristic)
        
        # Move to next node in the stack
        tower.curr_node = prio_queue[0]
        prio_queue.pop(0)

    print("Node visited: ", count)


# A* Search
def a_star_search(tower : CubeTower):

    _heuristic_search(tower, a_star_evaluation)


# Greedy Best-First Search
def gbfs_search(tower : CubeTower):

    _heuristic_search(tower, gbfs_evaluation)


def test_algorithm(algorithm : list, configs : list):

    # Check if 'configs' is a list containing lists
    if not (isinstance(configs, list) and all(isinstance(item, list) for item in configs)):
        configs = [configs]

    # Labels for plot
    search_labels = []
    figure_labels = []
    for i in range(len(configs)):
        figure_labels.append("Tower " + str(i + 1))

    # Data for plot
    memory_data = []
    time_data = []
    moves_data = []
    
    for search in algorithm:

        search_labels.append(search.__name__)

        print("==========", search.__name__, "==========")

        memory_used, time_used, moves_used = [], [], []

        for config in configs:

            tower = CubeTower(config)

            # Start memory tracer and time
            tracemalloc.start()
            start_time = time()

            # Execute search algorithm
            search(tower)

            # End memory tracer and time
            end_time = time()
            mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            memory_used.append(mem[1] - mem[0])
            time_used.append(end_time - start_time)
            moves_used.append(len(tower.get_path()) - 1)

            print("Moves to solution: ", len(tower.get_path()) - 1)

            # tower.visualize_path()

        print("Average Memory in Bytes: ", sum(memory_used)/len(configs))
        print("Average Time in seconds: ", sum(time_used)/len(configs), "\n")

        memory_data.append(memory_used)
        time_data.append(time_used)
        moves_data.append(moves_used)


    plot_data(xlabel='Search Algorithms', ylabel='Memory used in bytes', title='Memory used to solve Cube Tower(s)',
              group_labels=search_labels, bar_labels=figure_labels, data=memory_data)
    
    plot_data(xlabel='Search Algorithms', ylabel='Time in ms', title='Time used to solve Cube Tower(s)',
              group_labels=search_labels, bar_labels=figure_labels, data=time_data)
    
    plot_data(xlabel='Search Algorithms', ylabel='Moves used', title='Moves used to solve Cube Tower(s)',
              group_labels=search_labels, bar_labels=figure_labels, data=moves_data)

    
def plot_data(xlabel : str, ylabel : str, title : str, group_labels : list, bar_labels : list, data : list):
    
    # Set up positions for bars on x-axis
    bar_positions = np.arange(len(group_labels))

    # Plot the bar chart
    fig, ax = plt.subplots()

    np_data = np.array(data)

    for i, group_label in enumerate(bar_labels):
        ax.bar(bar_positions + i * 0.2, np_data[:, i], width=0.2, label=group_label)

    # Add labels and title
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(bar_positions + 0.3)
    ax.set_xticklabels(group_labels)
    ax.legend()

    # Show the plot
    plt.show()

# Test your implementation here
if __name__ == '__main__':

    # Random problem instances
    # num = 5
    # colors = ['red', 'blue', 'green','yellow']
    # configs = []
    # for _ in range(num):  
    #     c = [random.choice(colors) for _ in range(4)]
    #     configs.append(c)

    configs = [['red', 'blue', 'red', 'blue'],
               ['yellow', 'green', 'blue', 'red'],
               ['green', 'blue', 'green', 'red'],
               ['red', 'green', 'yellow', 'red'],
               ['blue', 'green', 'yellow', 'red']]

    test_algorithm([bfs_search, dfs_search, a_star_search, gbfs_search], configs)