"""Simple timing and memory checks for the patching algorithms."""

import time
import tracemalloc

from optimization_algorithms import divide_and_conquer_patch
from optimization_algorithms import dynamic_programming_patch
from optimization_algorithms import greedy_patch
from optimization_algorithms import selection_summary


def benchmark_algorithm(name, algorithm, network, budget):
    """Run one algorithm and save a few result values."""
    if budget < 0:
        raise ValueError("budget must be non-negative")

    tracemalloc.start()
    start_time = time.perf_counter()
    selected = algorithm(network, budget)
    end_time = time.perf_counter()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    budget_used, risk = selection_summary(network, selected)
    result = {
        "name": name,
        "execution_time_ms": (end_time - start_time) * 1000,
        "peak_memory_kb": peak_memory / 1024,
        "selected_count": len(selected),
        "budget_used": budget_used,
        "budget": budget,
        "risk_reduction": risk,
    }
    return result


def get_budget_percent(result):
    """Return the percentage of budget used."""
    if result["budget"] == 0:
        return 0
    return 100 * result["budget_used"] / result["budget"]


def run_benchmarks(network, budget=120):
    """Run all three algorithms."""
    results = []
    results.append(
        benchmark_algorithm(
            "Divide & Conquer", divide_and_conquer_patch, network, budget
        )
    )
    results.append(
        benchmark_algorithm("Greedy", greedy_patch, network, budget)
    )
    results.append(
        benchmark_algorithm(
            "Dynamic Programming", dynamic_programming_patch, network, budget
        )
    )
    return results


def format_comparison_table(results):
    """Make a simple text table for the terminal."""
    headers = [
        "Algorithm",
        "Time (ms)",
        "Memory (KB)",
        "Budget Used",
        "Utilization",
        "Risk Reduction",
    ]
    rows = []

    for result in results:
        row = []
        row.append(result["name"])
        row.append("{:.3f}".format(result["execution_time_ms"]))
        row.append("{:.2f}".format(result["peak_memory_kb"]))
        row.append(
            "{} / {}".format(result["budget_used"], result["budget"])
        )
        row.append("{:.1f}%".format(get_budget_percent(result)))
        row.append(str(result["risk_reduction"]))
        rows.append(row)

    widths = []
    for i in range(len(headers)):
        biggest = len(headers[i])
        for row in rows:
            if len(row[i]) > biggest:
                biggest = len(row[i])
        widths.append(biggest)

    line = ""
    for i in range(len(widths)):
        if i > 0:
            line += "-+-"
        line += "-" * widths[i]

    table = ""
    for i in range(len(headers)):
        if i > 0:
            table += " | "
        table += headers[i].ljust(widths[i])
    table += "\n" + line

    for row in rows:
        table += "\n"
        for i in range(len(row)):
            if i > 0:
                table += " | "
            table += row[i].ljust(widths[i])

    return table
