#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import argparse
import json
from collections import Counter, deque
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from util import decode_loc, load_map


Loc = Tuple[int, int]


def _label_components(env_map: List[List[bool]]) -> Tuple[List[List[int]], Dict[int, int]]:
    height = len(env_map)
    width = len(env_map[0]) if height else 0
    labels = [[-1 for _ in range(width)] for _ in range(height)]
    sizes: Dict[int, int] = {}
    component_id = 0

    for row in range(height):
        for col in range(width):
            if not env_map[row][col] or labels[row][col] != -1:
                continue

            queue = deque([(row, col)])
            labels[row][col] = component_id
            sizes[component_id] = 0

            while queue:
                curr_row, curr_col = queue.popleft()
                sizes[component_id] += 1
                for next_row, next_col in (
                    (curr_row - 1, curr_col),
                    (curr_row + 1, curr_col),
                    (curr_row, curr_col - 1),
                    (curr_row, curr_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if not env_map[next_row][next_col] or labels[next_row][next_col] != -1:
                        continue
                    labels[next_row][next_col] = component_id
                    queue.append((next_row, next_col))

            component_id += 1

    return labels, sizes


def _read_encoded_lines(path: Path) -> List[List[int]]:
    with path.open("r", encoding="utf-8") as fin:
        lines = [line.strip() for line in fin if line.strip()]

    if len(lines) < 2:
        raise ValueError(f"Malformed file: {path}")

    data_lines = lines[2:]
    encoded: List[List[int]] = []
    for line in data_lines:
        encoded.append([int(value) for value in line.split(",") if value])
    return encoded


def _iter_named_points(
    width: int,
    agents: List[List[int]],
    tasks: List[List[int]],
) -> Iterable[Tuple[str, int, int, Loc]]:
    for idx, agent_line in enumerate(agents):
        if len(agent_line) != 1:
            raise ValueError(f"Agent line {idx} should contain exactly one location")
        encoded = agent_line[0]
        yield ("agent", idx, encoded, decode_loc(width, encoded))

    for task_idx, task in enumerate(tasks):
        for stop_idx, encoded in enumerate(task):
            yield ("task", task_idx, encoded, decode_loc(width, encoded))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check whether all agent and task locations in an instance belong to the same connected component."
    )
    parser.add_argument("--instance", required=True, help="Path to the problem JSON.")
    parser.add_argument(
        "--show-limit",
        type=int,
        default=10,
        help="Maximum number of offending points to print per category.",
    )
    args = parser.parse_args()

    instance_path = Path(args.instance).resolve()
    instance_dir = instance_path.parent

    with instance_path.open("r", encoding="utf-8") as fin:
        payload = json.load(fin)

    map_path = (instance_dir / payload["mapFile"]).resolve()
    agent_path = (instance_dir / payload["agentFile"]).resolve()
    task_path = (instance_dir / payload["taskFile"]).resolve()

    height, width, env_map, _ = load_map(str(map_path))
    labels, sizes = _label_components(env_map)
    largest_component = max(sizes, key=sizes.get)

    agents = _read_encoded_lines(agent_path)
    tasks = _read_encoded_lines(task_path)

    invalid_points = []
    component_counter: Counter[int] = Counter()
    non_largest_points = []

    for kind, idx, encoded, (row, col) in _iter_named_points(width, agents, tasks):
        if not (0 <= row < height and 0 <= col < width):
            invalid_points.append((kind, idx, encoded, row, col, "out_of_bounds"))
            continue
        if not env_map[row][col]:
            invalid_points.append((kind, idx, encoded, row, col, "blocked"))
            continue

        component_id = labels[row][col]
        component_counter[component_id] += 1
        if component_id != largest_component:
            non_largest_points.append((kind, idx, encoded, row, col, component_id))

    print(f"instance: {instance_path}")
    print(f"map: {map_path}")
    print(f"agents: {agent_path}")
    print(f"tasks: {task_path}")
    print(f"components: {len(sizes)}")
    print(f"largest_component: {largest_component} size={sizes[largest_component]}")
    print(f"agent_count: {len(agents)}")
    print(f"task_count: {len(tasks)}")
    print(f"invalid_points: {len(invalid_points)}")
    print(f"components_used: {dict(component_counter)}")

    if invalid_points:
        print("status: FAIL")
        print("reason: some encoded locations are blocked or out of bounds")
        for point in invalid_points[: args.show_limit]:
            kind, idx, encoded, row, col, reason = point
            print(f"invalid {kind}[{idx}] encoded={encoded} loc=({row},{col}) reason={reason}")
        return

    if len(component_counter) == 1 and largest_component in component_counter:
        print("status: PASS")
        print("reason: all agent starts and task locations are in the largest connected component")
        return

    print("status: FAIL")
    print("reason: locations span multiple connected components")
    for point in non_largest_points[: args.show_limit]:
        kind, idx, encoded, row, col, component_id = point
        print(
            f"off_component {kind}[{idx}] encoded={encoded} loc=({row},{col}) component={component_id}"
        )


if __name__ == "__main__":
    main()
