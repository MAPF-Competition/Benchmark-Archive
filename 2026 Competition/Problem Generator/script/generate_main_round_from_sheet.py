#!/usr/bin/env python3
"""Generate main-round instances from the spreadsheet specification."""

from __future__ import annotations

import json
import math
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from collections import deque
from typing import Dict, List, Sequence, Tuple


Loc = Tuple[int, int]


@dataclass(frozen=True)
class InstanceSpec:
    instance_id: str
    domain: str
    map_name: str
    agents: int
    distance_per_errand: int
    task_len_min: int
    task_len_max: int
    average_task_len: float
    task_dist: str
    agent_counter: int
    delay_min: int
    delay_max: int
    delay_prob: float
    simulation_ticks: int
    slow_plan_factor: float
    min_comm_ms: int
    tasks_per_agent: float
    time_seconds: float
    num_tasks_reveal: float


SUPPORTED_EVENT_MODELS: Sequence[str] = ("bernoulli", "poisson")
SUPPORTED_DURATION_MODELS: Sequence[str] = ("uniform", "gaussian")


SPECS: Sequence[InstanceSpec] = (
    InstanceSpec("maze-A", "maze.domain", "maze-32-32-2.map", 100, 55, 2, 2, 2.0, "random", 10, 50, 100, 0.001, 5000, 3.0, 3000, 4.55, 500.0, 1.5),
    InstanceSpec("maze-B", "maze.domain", "maze-32-32-2.map", 50, 54, 2, 2, 2.0, "random", 5, 10, 30, 0.02, 4000, 1.0, 500, 7.41, 400.0, 1.5),
    InstanceSpec("room-A", "room.domain", "room-64-64-16.map", 1000, 66, 2, 2, 2.0, "random", 3, 100, 150, 0.0005, 3000, 2.0, 600, 7.58, 300.0, 1.5),
    InstanceSpec("room-B", "room.domain", "room-64-64-16.map", 500, 66, 2, 2, 2.0, "random", 10, 1, 20, 0.01, 10000, 3.0, 3000, 7.58, 1000.0, 1.5),
    InstanceSpec("rand-A", "random.domain", "random-64-64-10.map", 1500, 43, 2, 5, 3.5, "random", 5, 1, 5, 0.015, 10000, 0.5, 250, 13.29, 1000.0, 1.5),
    InstanceSpec("rand-B", "random.domain", "random-64-64-10.map", 3000, 43, 2, 5, 3.5, "random", 3, 20, 60, 0.005, 8000, 3.0, 900, 17.72, 800.0, 1.5),
    InstanceSpec("fulfill-A", "warehouse.domain", "warehouse_long_corridor_large.map", 10000, 148, 2, 3, 2.5, "distance", 5, 1, 40, 0.02, 30000, 10.0, 5000, 16.22, 3000.0, 1.5),
    InstanceSpec("fulfill-B", "warehouse.domain", "warehouse_long_corridor_large.map", 5000, 148, 2, 3, 2.5, "distance", 3, 1, 10, 0.01, 20000, 3.0, 900, 18.02, 2000.0, 1.5),
    InstanceSpec("fulfill-C", "warehouse.domain", "warehouse_long_corridor_large.map", 10000, 148, 2, 2, 2.0, "random", 10, 20, 80, 0.005, 25000, 3.0, 3000, 8.45, 2500.0, 1.5),
    InstanceSpec("iron", "iron_harvest.domain", "scene_mp_2p_01.map", 10000, 2000, 2, 2, 2.0, "random", 3, 50, 200, 0.005, 60000, 10.0, 3000, 5.00, 6000.0, 1.0),
    InstanceSpec("bos", "city.domain", "Boston_0_256.map", 2000, 195, 2, 2, 2.0, "random", 3, 50, 100, 0.002, 10000, 5.0, 1500, 8.55, 1000.0, 1.5),
    InstanceSpec("orz", "game.domain", "orz900d.map", 6000, 1146, 2, 2, 2.0, "random", 3, 10, 80, 0.005, 40000, 10.0, 3000, 5.82, 4000.0, 1.5),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def largest_component_cells(grid: Sequence[str]) -> set[Loc]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    free_chars = {".", "S", "E"}
    seen: set[Loc] = set()
    best: set[Loc] = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] not in free_chars or (row, col) in seen:
                continue
            component: set[Loc] = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                curr = queue.popleft()
                component.add(curr)
                r, c = curr
                for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    nr, nc = nxt
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if nxt in seen or grid[nr][nc] not in free_chars:
                        continue
                    seen.add(nxt)
                    queue.append(nxt)
            if len(component) > len(best):
                best = component
    return best


def load_map(path: Path) -> Tuple[int, int, List[str], List[Loc], List[Loc], List[Loc]]:
    with path.open("r", encoding="utf-8") as fin:
        lines = [line.rstrip("\n") for line in fin]

    height = int(lines[1].split()[-1])
    width = int(lines[2].split()[-1])
    grid = lines[4:]

    traversable: List[Loc] = []
    e_cells: List[Loc] = []
    s_cells: List[Loc] = []
    free_chars = {".", "S", "E"}
    largest_component = largest_component_cells(grid)
    for row, line in enumerate(grid):
        for col, ch in enumerate(line):
            if (row, col) not in largest_component:
                continue
            if ch in free_chars:
                traversable.append((row, col))
            if ch == "E":
                e_cells.append((row, col))
            elif ch == "S":
                s_cells.append((row, col))
    return height, width, grid, traversable, e_cells, s_cells


def encode_loc(width: int, loc: Loc) -> int:
    return loc[0] * width + loc[1]


def manhattan(a: Loc, b: Loc) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def sample_task_length(spec: InstanceSpec, rng: random.Random) -> int:
    if spec.task_len_min == spec.task_len_max:
        return spec.task_len_min
    # The sheet values align with uniform integer sampling for the listed ranges.
    return rng.randint(spec.task_len_min, spec.task_len_max)


def choose_delay_models(spec: InstanceSpec) -> Tuple[str, str]:
    rng = random.Random(f"{spec.instance_id}:delay_models:2026")
    return (
        rng.choice(list(SUPPORTED_EVENT_MODELS)),
        rng.choice(list(SUPPORTED_DURATION_MODELS)),
    )


def choose_by_target_distance(
    current: Loc,
    candidates: Sequence[Loc],
    target_distance: int,
    rng: random.Random,
    forbidden: set[Loc],
    attempts: int = 24,
) -> Loc:
    best = None
    best_score = None
    tol = max(3, int(target_distance * 0.12))
    for _ in range(attempts):
        loc = candidates[rng.randrange(len(candidates))]
        if loc in forbidden:
            continue
        score = abs(manhattan(current, loc) - target_distance)
        if score <= tol:
            return loc
        if best_score is None or score < best_score:
            best = loc
            best_score = score

    if best is not None:
        return best

    while True:
        loc = candidates[rng.randrange(len(candidates))]
        if loc not in forbidden:
            return loc


def generate_generic_tasks(
    spec: InstanceSpec,
    width: int,
    traversable: Sequence[Loc],
    rng: random.Random,
) -> Tuple[List[List[int]], Dict[str, float]]:
    task_count = round_half_up(spec.agents * spec.tasks_per_agent)
    tasks: List[List[int]] = []
    total_stops = 0
    total_errands = 0
    total_distance = 0

    for _ in range(task_count):
        task_len = sample_task_length(spec, rng)
        used: set[Loc] = set()
        first = traversable[rng.randrange(len(traversable))]
        used.add(first)
        task_locs = [first]
        prev = first
        for _ in range(task_len - 1):
            if spec.task_dist == "distance":
                nxt = choose_by_target_distance(
                    prev,
                    traversable,
                    spec.distance_per_errand,
                    rng,
                    used,
                )
            else:
                while True:
                    nxt = traversable[rng.randrange(len(traversable))]
                    if nxt not in used:
                        break
            task_locs.append(nxt)
            used.add(nxt)
            total_distance += manhattan(prev, nxt)
            total_errands += 1
            prev = nxt
        total_stops += len(task_locs)
        tasks.append([encode_loc(width, loc) for loc in task_locs])

    realized = {
        "task_count": task_count,
        "average_task_len": total_stops / task_count if task_count else 0.0,
        "average_distance_per_errand": total_distance / total_errands if total_errands else 0.0,
    }
    return tasks, realized


def choose_warehouse_stop(
    current: Loc,
    targets: Sequence[Loc],
    spec: InstanceSpec,
    rng: random.Random,
    forbidden: set[Loc],
) -> Loc:
    if spec.task_dist == "distance":
        return choose_by_target_distance(
            current,
            targets,
            spec.distance_per_errand,
            rng,
            forbidden,
            attempts=40,
        )

    while True:
        loc = targets[rng.randrange(len(targets))]
        if loc not in forbidden:
            return loc


def generate_warehouse_tasks(
    spec: InstanceSpec,
    width: int,
    e_cells: Sequence[Loc],
    s_cells: Sequence[Loc],
    rng: random.Random,
) -> Tuple[List[List[int]], Dict[str, float]]:
    if not e_cells or not s_cells:
        raise ValueError(f"{spec.instance_id} uses warehouse generation but map lacks E/S cells")

    task_count = round_half_up(spec.agents * spec.tasks_per_agent)
    tasks: List[List[int]] = []
    total_stops = 0
    total_errands = 0
    total_distance = 0

    for _ in range(task_count):
        task_len = sample_task_length(spec, rng)
        task_locs: List[Loc] = []
        used: set[Loc] = set()

        current = e_cells[rng.randrange(len(e_cells))]
        task_locs.append(current)
        used.add(current)

        for stop_idx in range(1, task_len):
            targets = s_cells if stop_idx % 2 == 1 else e_cells
            nxt = choose_warehouse_stop(current, targets, spec, rng, used)
            task_locs.append(nxt)
            used.add(nxt)
            total_distance += manhattan(current, nxt)
            total_errands += 1
            current = nxt

        total_stops += len(task_locs)
        tasks.append([encode_loc(width, loc) for loc in task_locs])

    realized = {
        "task_count": task_count,
        "average_task_len": total_stops / task_count if task_count else 0.0,
        "average_distance_per_errand": total_distance / total_errands if total_errands else 0.0,
    }
    return tasks, realized


def generate_agents(width: int, traversable: Sequence[Loc], count: int, rng: random.Random) -> List[int]:
    if count > len(traversable):
        raise ValueError(f"Requested {count} agents but only {len(traversable)} traversable cells exist")
    starts = rng.sample(list(traversable), count)
    return [encode_loc(width, loc) for loc in starts]


def write_agents(path: Path, encoded_agents: Sequence[int]) -> None:
    with path.open("w", encoding="utf-8") as fout:
        fout.write("# version for LoRR 2026\n")
        fout.write(f"{len(encoded_agents)}\n")
        for loc in encoded_agents:
            fout.write(f"{loc}\n")


def write_tasks(path: Path, tasks: Sequence[Sequence[int]]) -> None:
    with path.open("w", encoding="utf-8") as fout:
        fout.write("# version for LoRR 2026\n")
        fout.write(f"{len(tasks)}\n")
        for task in tasks:
            fout.write(",".join(str(loc) for loc in task))
            fout.write("\n")


def write_problem_json(path: Path, spec: InstanceSpec, event_model: str, duration_model: str) -> None:
    payload = {
        "mapFile": f"maps/{spec.map_name}",
        "agentFile": f"agents/{spec.instance_id}.agents",
        "teamSize": spec.agents,
        "taskFile": f"tasks/{spec.instance_id}.tasks",
        "numTasksReveal": spec.num_tasks_reveal,
        "version": "2026 LoRR",
        "agentCounter": spec.agent_counter,
        "agentSize": 1.0,
        "delayConfig": {
            "seed": 0,
            "minDelay": spec.delay_min,
            "maxDelay": spec.delay_max,
            "eventModel": event_model,
            "pDelay": spec.delay_prob,
            "durationModel": duration_model,
            "gaussMeanRatio": 0.5,
            "gaussStdRatio": 0.22,
        },
    }
    with path.open("w", encoding="utf-8") as fout:
        json.dump(payload, fout, indent=4)
        fout.write("\n")


def update_cli(cli_path: Path, specs: Sequence[InstanceSpec]) -> None:
    payload: Dict[str, Dict[str, int]] = {}
    if cli_path.exists():
        with cli_path.open("r", encoding="utf-8") as fin:
            payload = json.load(fin)

    for spec in specs:
        payload[spec.instance_id] = {
            "simulation_time": spec.simulation_ticks,
            "communication_time": spec.min_comm_ms,
        }

    with cli_path.open("w", encoding="utf-8") as fout:
        json.dump(payload, fout, indent=4)
        fout.write("\n")


def ensure_map_present(domain_dir: Path, map_name: str, source_map: Path) -> None:
    target = domain_dir / "maps" / map_name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.resolve() == source_map.resolve():
        return
    if not target.exists():
        shutil.copy2(source_map, target)


def source_map_for(repo: Path, spec: InstanceSpec) -> Path:
    existing = repo / "MainRoundEvaluationInstances" / spec.domain / "maps" / spec.map_name
    if existing.exists():
        return existing
    example_long_corridor = (
        repo / "Example Instances" / "warehouse_long_corridor.domain" / "maps" / spec.map_name
    )
    if example_long_corridor.exists():
        return example_long_corridor
    fallback = repo / "Problem Generator" / "maps" / spec.map_name
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Could not locate map {spec.map_name} for {spec.instance_id}")


def generate_instance(repo: Path, spec: InstanceSpec) -> Dict[str, float]:
    domain_dir = repo / "MainRoundEvaluationInstances" / spec.domain
    maps_dir = domain_dir / "maps"
    tasks_dir = domain_dir / "tasks"
    agents_dir = domain_dir / "agents"
    maps_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)

    source_map = source_map_for(repo, spec)
    ensure_map_present(domain_dir, spec.map_name, source_map)
    width_height = load_map(source_map)
    height, width, _grid, traversable, e_cells, s_cells = width_height
    if height <= 0 or width <= 0:
        raise ValueError(f"Invalid map dimensions for {spec.instance_id}")

    task_seed = f"{spec.instance_id}:tasks:2026"
    agent_seed = f"{spec.instance_id}:agents:2026"
    task_rng = random.Random(task_seed)
    agent_rng = random.Random(agent_seed)
    chosen_event_model, chosen_duration_model = choose_delay_models(spec)

    if spec.domain == "warehouse.domain":
        tasks, realized = generate_warehouse_tasks(spec, width, e_cells, s_cells, task_rng)
    else:
        tasks, realized = generate_generic_tasks(spec, width, traversable, task_rng)

    agents = generate_agents(width, traversable, spec.agents, agent_rng)
    write_tasks(tasks_dir / f"{spec.instance_id}.tasks", tasks)
    write_agents(agents_dir / f"{spec.instance_id}.agents", agents)
    write_problem_json(
        domain_dir / f"{spec.instance_id}.json",
        spec,
        chosen_event_model,
        chosen_duration_model,
    )

    realized["agent_count"] = spec.agents
    realized["target_task_count"] = round_half_up(spec.agents * spec.tasks_per_agent)
    realized["target_average_task_len"] = spec.average_task_len
    realized["target_average_distance_per_errand"] = spec.distance_per_errand
    realized["target_tasks_per_agent"] = spec.tasks_per_agent
    realized["realized_tasks_per_agent"] = realized["task_count"] / spec.agents
    realized["task_dist"] = spec.task_dist
    realized["chosen_event_model"] = chosen_event_model
    realized["chosen_duration_model"] = chosen_duration_model
    realized["poisson_lambda"] = spec.agents * spec.delay_prob
    return realized


def main() -> None:
    repo = repo_root()
    manifest: Dict[str, Dict[str, float]] = {}

    for spec in SPECS:
        manifest[spec.instance_id] = generate_instance(repo, spec)

    update_cli(repo / "MainRoundEvaluationInstances" / "cli.json", SPECS)

    manifest_path = repo / "MainRoundEvaluationInstances" / "sheet_main_round_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fout:
        json.dump(manifest, fout, indent=4)
        fout.write("\n")

    print(f"Generated {len(SPECS)} instances")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
