"""Functions for making a simple enterprise network."""

import random


def create_network(node_count=50, connection_probability=0.1, seed=None):
    """Make a network using lists and dictionaries."""
    if node_count < 1:
        raise ValueError("node_count must be at least 1")
    if connection_probability < 0 or connection_probability > 1:
        raise ValueError("connection_probability must be between 0 and 1")

    random_generator = random.Random(seed)
    nodes = []
    adjacency = {}

    # make the nodes first
    for i in range(node_count):
        node = {
            "id": i,
            "vulnerability": random_generator.randint(1, 10),
            "cost": random_generator.randint(5, 20),
            "degree": 0,
        }
        nodes.append(node)
        adjacency[i] = []

    edges = []

    # check every possible pair of nodes
    for i in range(node_count):
        for j in range(i + 1, node_count):
            if random_generator.random() < connection_probability:
                edges.append((i, j))
                adjacency[i].append(j)
                adjacency[j].append(i)

    # save the number of connections for every node
    for node in nodes:
        node_id = node["id"]
        node["degree"] = len(adjacency[node_id])

    network = {
        "nodes": nodes,
        "edges": edges,
        "adjacency": adjacency,
        "node_count": node_count,
    }
    return network


def create_custom_network(node_values, edge_values):
    """Make a network from node dictionaries and edge pairs."""
    nodes = []
    adjacency = {}
    node_count = len(node_values)

    for i in range(node_count):
        old_node = node_values[i]
        node = {
            "id": i,
            "vulnerability": int(old_node["vulnerability"]),
            "cost": int(old_node["cost"]),
            "degree": 0,
        }
        nodes.append(node)
        adjacency[i] = []

    edges = []
    for edge in edge_values:
        left = int(edge[0])
        right = int(edge[1])
        if left == right:
            raise ValueError("a node cannot connect to itself")
        if left < 0 or right < 0 or left >= node_count or right >= node_count:
            raise ValueError("edge has a node number outside the network")

        edge_pair = (left, right)
        reverse_pair = (right, left)
        if edge_pair in edges or reverse_pair in edges:
            raise ValueError("duplicate edges are not allowed")

        edges.append(edge_pair)
        adjacency[left].append(right)
        adjacency[right].append(left)

    for node in nodes:
        node["degree"] = len(adjacency[node["id"]])

    return {
        "nodes": nodes,
        "edges": edges,
        "adjacency": adjacency,
        "node_count": node_count,
    }
