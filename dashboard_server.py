"""Small web server for showing the network simulation."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from benchmarking import run_benchmarks
from infection_simulation import infection_step
from infection_simulation import start_simulation
from network_graph import create_custom_network
from network_graph import create_network
from optimization_algorithms import divide_and_conquer_patch
from optimization_algorithms import dynamic_programming_patch
from optimization_algorithms import greedy_patch


ROOT = Path(__file__).parent
BUDGET = 120


def make_state():
    """Make the starting dashboard data."""
    network = create_network(50, 0.1, 42)
    simulation = start_simulation(network, 0.85, 0, 42)
    state_data = {
        "network": network,
        "simulation": simulation,
        "patched": set(),
        "mode": "random",
        "algorithm": {},
    }
    return state_data


state = make_state()


def reset_state():
    """Reset progress while keeping a custom network or falling back to random."""
    global state
    if state.get("mode") == "custom" and "custom_config" in state:
        config = state["custom_config"]
        state = make_custom_state(config["nodes"], config["edges"])
        state["custom_config"] = config
    else:
        state = make_state()


def make_custom_state(node_values, edge_values):
    """Make a dashboard state from values entered by the user and store config for reset."""
    network = create_custom_network(node_values, edge_values)
    simulation = start_simulation(network, 0.85, 0, 42)
    return {
        "network": network,
        "simulation": simulation,
        "patched": set(),
        "mode": "custom",
        "algorithm": {},
        "custom_config": {"nodes": node_values, "edges": edge_values}
    }


def configure_custom_network(data):
    """Check custom values and replace the current network."""
    node_count = int(data.get("node_count", 0))
    edge_count = int(data.get("edge_count", 0))
    node_values = data.get("nodes", [])
    edge_values = data.get("edges", [])

    if node_count < 1:
        raise ValueError("number of nodes must be at least 1")
    if edge_count < 0:
        raise ValueError("number of edges cannot be negative")
    if len(node_values) != node_count:
        raise ValueError("node data does not match the node count")
    if len(edge_values) > edge_count:
        raise ValueError("too many edges were supplied")

    for node in node_values:
        vulnerability = int(node["vulnerability"])
        cost = int(node["cost"])
        if vulnerability < 1 or vulnerability > 10:
            raise ValueError("vulnerability must be from 1 to 10")
        if cost < 1:
            raise ValueError("patch cost must be positive")

    new_state = make_custom_state(node_values, edge_values)
    global state
    state = new_state


def make_algorithm_steps(algorithm_name):
    """Make simple text steps for the selected algorithm."""
    if algorithm_name == "dc":
        algorithm = divide_and_conquer_patch
        title = "Divide and Conquer"
    elif algorithm_name == "greedy":
        algorithm = greedy_patch
        title = "Greedy Algorithm"
    elif algorithm_name == "dp":
        algorithm = dynamic_programming_patch
        title = "Dynamic Programming"
    else:
        raise ValueError("unknown algorithm")

    network = state["network"]
    selected = algorithm(network, BUDGET)
    steps = []
    steps.append(
        {
            "text": "Starting {} with a budget of {}.".format(
                title, BUDGET
            ),
            "node_id": None,
            "selected": [],
            "remaining_budget": BUDGET,
        }
    )

    selected_so_far = []
    spent = 0
    for node in network["nodes"]:
        node_id = node["id"]
        if node_id in selected:
            selected_so_far.append(node_id)
            spent += node["cost"]
            text = "Node {} was selected. Its patch cost is {}.".format(
                node_id, node["cost"]
            )
        else:
            text = "Node {} was checked and was not selected.".format(node_id)

        steps.append(
            {
                "text": text,
                "node_id": node_id,
                "selected": selected_so_far[:],
                "remaining_budget": BUDGET - spent,
            }
        )

    total_cost = 0
    for node_id in selected:
        for node in network["nodes"]:
            if node["id"] == node_id:
                total_cost += node["cost"]
                break

    steps.append(
        {
            "text": "Finished. The selected nodes are ready to be patched.",
            "node_id": None,
            "selected": selected[:],
            "remaining_budget": BUDGET - total_cost,
        }
    )
    return title, steps, selected


def start_algorithm(algorithm_name):
    """Start a step-by-step algorithm page."""
    title, steps, selected = make_algorithm_steps(algorithm_name)
    state["algorithm"] = {
        "name": algorithm_name,
        "title": title,
        "steps": steps,
        "current": 0,
        "selected": selected,
    }
    return get_algorithm_data()


def next_algorithm_step():
    """Move the current algorithm page forward by one step and advance infection simulation."""
    algorithm_data = state["algorithm"]
    if not algorithm_data:
        raise ValueError("an algorithm has not been started")

    if algorithm_data["current"] < len(algorithm_data["steps"]) - 1:
        algorithm_data["current"] += 1

    current = algorithm_data["current"]
    last_step = len(algorithm_data["steps"]) - 1
    if current == last_step:
        state["patched"] = set(algorithm_data["selected"])
    
    # Advance the worm infection simulation step-by-step with the algorithm explanation
    infection_step(state["simulation"])

    return get_algorithm_data()


def get_algorithm_data():
    """Return the current step for the explanation page."""
    algorithm_data = state["algorithm"]
    if not algorithm_data:
        return {
            "started": False,
            "step": None,
            "current": 0,
            "total": 0,
        }

    current = algorithm_data["current"]
    return {
        "started": True,
        "title": algorithm_data["title"],
        "step": algorithm_data["steps"][current],
        "current": current + 1,
        "total": len(algorithm_data["steps"]),
        "finished": current == len(algorithm_data["steps"]) - 1,
    }


def get_state_data():
    """Create the data sent to the dashboard."""
    network = state["network"]
    simulation = state["simulation"]
    benchmarks = run_benchmarks(network, BUDGET)
    node_data = []

    for node in network["nodes"]:
        if node["id"] in state["patched"]:
            node_state = "patched"
        elif node["id"] in simulation["infected"]:
            node_state = "infected"
        else:
            node_state = "healthy"

        node_data.append(
            {
                "id": node["id"],
                "vulnerability": node["vulnerability"],
                "degree": node["degree"],
                "state": node_state,
            }
        )

    benchmark_data = []
    for result in benchmarks:
        benchmark_data.append(
            {
                "name": result["name"],
                "time": result["execution_time_ms"],
                "memory": result["peak_memory_kb"],
                "budget": result["budget_used"],
                "utilization": get_budget_percent_for_dashboard(result),
                "risk": result["risk_reduction"],
            }
        )

    data = {
        "nodes": node_data,
        "edges": network["edges"],
        "time": simulation["time"],
        "infected": len(simulation["infected"]),
        "curve": simulation["infection_curve"],
        "benchmarks": benchmark_data,
        "mode": state["mode"],
    }
    return data


def read_json(handler):
    """Read a JSON request body."""
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length)
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def get_budget_percent_for_dashboard(result):
    """Return budget percentage without using a result class."""
    if result["budget"] == 0:
        return 0
    return 100 * result["budget_used"] / result["budget"]


def simulate_once():
    """Run one infection step."""
    infection_step(state["simulation"])


def patch_network(algorithm_name):
    """Patch the network with the selected algorithm."""
    if algorithm_name == "dc":
        selected = divide_and_conquer_patch(state["network"], BUDGET)
    elif algorithm_name == "greedy":
        selected = greedy_patch(state["network"], BUDGET)
    elif algorithm_name == "dp":
        selected = dynamic_programming_patch(state["network"], BUDGET)
    else:
        raise ValueError("unknown algorithm")

    state["patched"] = set(selected)


class DashboardHandler(BaseHTTPRequestHandler):
    """Handle the few HTTP requests used by the dashboard."""

    def send_json(self, data):
        """Send a dictionary as JSON."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """Handle page and state requests."""
        path = urlparse(self.path).path
        if path == "/":
            body = (ROOT / "dashboard.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/state":
            self.send_json(get_state_data())
        elif path == "/api/algorithm/state":
            self.send_json(get_algorithm_data())
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle reset, simulation, and patch requests."""
        path = urlparse(self.path).path
        try:
            if path == "/api/reset":
                reset_state()
                self.send_json(get_state_data())
            elif path == "/api/simulate":
                simulate_once()
                self.send_json(get_state_data())
            elif path == "/api/configure":
                configure_custom_network(read_json(self))
                self.send_json(get_state_data())
            elif path.startswith("/api/patch/"):
                algorithm_name = path.rsplit("/", 1)[-1]
                patch_network(algorithm_name)
                self.send_json(get_state_data())
            elif path.startswith("/api/algorithm/") and path.endswith("/start"):
                algorithm_name = path.split("/")[3]
                self.send_json(start_algorithm(algorithm_name))
            elif path == "/api/algorithm/next":
                self.send_json(next_algorithm_step())
            else:
                self.send_error(404)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            self.send_error(400, str(error))

    def log_message(self, format_string, *args):
        del format_string, args

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Dashboard running on port {port}")
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardHandler)
    server.serve_forever()