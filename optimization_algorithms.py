"""Updated for some bugs in divide and conq"""


def risk_reduction(node):
    return node["vulnerability"] * node["degree"]


def priority_ratio(node):
    if node["cost"] == 0:
        # free node with positive value → infinite priority, not zero
        return float("inf") if risk_reduction(node) > 0 else 0
    return risk_reduction(node) / node["cost"]


def sort_nodes(nodes):
    sorted_nodes = []
    for node in nodes:
        position = 0
        while position < len(sorted_nodes):
            old_node = sorted_nodes[position]
            if priority_ratio(node) > priority_ratio(old_node):
                break
            if (priority_ratio(node) == priority_ratio(old_node)
                    and risk_reduction(node) > risk_reduction(old_node)):
                break
            position += 1
        sorted_nodes.insert(position, node)
    return sorted_nodes


def choose_small_group(nodes, budget):
    selected = []
    left = budget
    for node in sort_nodes(nodes):
        if node["cost"] <= left:
            selected.append(node["id"])
            left -= node["cost"]
    return selected


def divide_and_conquer_patch(network, budget=120):
    if budget < 0:
        raise ValueError("budget must be non-negative")

    def solve(node_list, group_budget):
        if not node_list or group_budget == 0:
            return []
        if len(node_list) <= 4:
            return choose_small_group(node_list, group_budget)

        middle = len(node_list) // 2
        left_nodes = node_list[:middle]
        right_nodes = node_list[middle:]

        left_cost = sum(n["cost"] for n in left_nodes)
        left_budget = min(group_budget, left_cost)
        right_budget = group_budget - left_budget

        selected = solve(left_nodes, left_budget)
        selected.extend(solve(right_nodes, right_budget))
        return selected          # budgets already guarantee total ≤ group_budget

    return solve(network["nodes"], budget)


def greedy_patch(network, budget=120):
    if budget < 0:
        raise ValueError("budget must be non-negative")
    selected = []
    left = budget
    for node in sort_nodes(network["nodes"]):
        if node["cost"] <= left:
            selected.append(node["id"])
            left -= node["cost"]
    return selected


def dynamic_programming_patch(network, budget=120):
    if budget < 0:
        raise ValueError("budget must be non-negative")

    node_list = network["nodes"]
    n = len(node_list)
    table = [[0] * (budget + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        node = node_list[i - 1]
        for j in range(budget + 1):
            table[i][j] = table[i - 1][j]
            if node["cost"] <= j:
                candidate = table[i - 1][j - node["cost"]] + risk_reduction(node)
                if candidate > table[i][j]:
                    table[i][j] = candidate

    selected = []
    left = budget
    i = n
    while i > 0:
        if table[i][left] != table[i - 1][left]:
            node = node_list[i - 1]
            selected.append(node["id"])
            left -= node["cost"]
        i -= 1
    selected.reverse()
    return selected


def selection_summary(network, selected_ids):
    by_id = {node["id"]: node for node in network["nodes"]}
    total_cost = 0
    total_risk = 0
    for node_id in selected_ids:
        node = by_id.get(node_id)
        if node is None:
            continue
        total_cost += node["cost"]
        total_risk += risk_reduction(node)
    return total_cost, total_risk
