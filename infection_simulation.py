"""Simple functions for simulating worm infection."""

import random


def start_simulation(network, beta=0.85, patient_zero=0, seed=None):
    """Create the starting state for a simulation."""
    if beta < 0 or beta > 1:
        raise ValueError("beta must be between 0 and 1")
    if patient_zero not in network["adjacency"]:
        raise ValueError("patient_zero must identify a node in the network")

    infected = set()
    infected.add(patient_zero)

    simulation = {
        "network": network,
        "beta": beta,
        "patient_zero": patient_zero,
        "random": random.Random(seed),
        "infected": infected,
        "time": 0,
        "infection_curve": [],
    }
    simulation["infection_curve"].append(get_compromised_percentage(simulation))
    return simulation


def get_compromised_percentage(simulation):
    """Return the percentage of infected nodes."""
    infected_count = len(simulation["infected"])
    node_count = simulation["network"]["node_count"]
    return 100 * infected_count / node_count


def infection_step(simulation):
    """Run one infection step and return the new infected node ids."""
    network = simulation["network"]
    infected = simulation["infected"]
    new_infected = set()

    # loop through infected nodes and their neighbors
    for infected_node in infected:
        neighbors = network["adjacency"][infected_node]
        for neighbor in neighbors:
            if neighbor in infected or neighbor in new_infected:
                continue

            node = network["nodes"][neighbor]
            chance = simulation["beta"] * node["vulnerability"] / 10
            if simulation["random"].random() < chance:
                new_infected.add(neighbor)

    for node_id in new_infected:
        infected.add(node_id)

    simulation["time"] += 1
    simulation["infection_curve"].append(
        get_compromised_percentage(simulation)
    )
    return new_infected


def run_simulation(simulation, steps):
    """Run the simulation for the requested number of steps."""
    if steps < 0:
        raise ValueError("steps must be non-negative")

    while steps > 0:
        infection_step(simulation)
        steps -= 1
    return simulation["infection_curve"][:]
