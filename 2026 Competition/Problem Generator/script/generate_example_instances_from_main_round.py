#!/usr/bin/env python3
"""Generate a cleaned example set using the same maps as the current main round."""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path
from typing import Dict, Sequence

from generate_main_round_from_sheet import (
    InstanceSpec,
    generate_agents,
    generate_generic_tasks,
    generate_warehouse_tasks,
    load_map,
    repo_root,
    source_map_for,
    write_agents,
    write_problem_json,
    write_tasks,
)


EXAMPLE_SPECS: Sequence[InstanceSpec] = (
    InstanceSpec("maze-example_40", "maze.domain", "maze-32-32-2.map", 40, 55, 2, 2, 2.0, "random", 3, 5, 12, 0.0003, 2500, 1.0, 500, 4.00, 250.0, 1.5),
    InstanceSpec("room-example_250", "room.domain", "room-64-64-16.map", 250, 66, 2, 2, 2.0, "random", 3, 10, 30, 0.0002, 3500, 1.0, 600, 5.50, 350.0, 1.5),
    InstanceSpec("random-example_400", "random.domain", "random-64-64-10.map", 400, 43, 2, 4, 3.0, "random", 3, 1, 4, 0.003, 6000, 1.0, 500, 8.00, 600.0, 1.5),
    InstanceSpec("fulfill-example_2500", "warehouse.domain", "warehouse_long_corridor_large.map", 2500, 148, 2, 3, 2.5, "distance", 3, 2, 8, 0.003, 12000, 1.0, 1000, 9.00, 1200.0, 1.5),
    InstanceSpec("iron-example_10000", "iron_harvest.domain", "scene_mp_2p_01.map", 10000, 2000, 2, 2, 2.0, "random", 3, 15, 40, 0.001, 30000, 1.0, 1000, 2.50, 3000.0, 1.0),
    InstanceSpec("bos-example_600", "city.domain", "Boston_0_256.map", 600, 195, 2, 2, 2.0, "random", 3, 10, 25, 0.0005, 6000, 1.0, 1000, 6.00, 600.0, 1.5),
    InstanceSpec("orz-example_1800", "game.domain", "orz900d.map", 1800, 1146, 2, 2, 2.0, "random", 3, 5, 20, 0.001, 22000, 1.0, 1000, 4.00, 2200.0, 1.5),
)

EXAMPLE_DELAY_MODELS: Dict[str, tuple[str, str]] = {
    "maze-example_40": ("bernoulli", "gaussian"),
    "room-example_250": ("poisson", "uniform"),
    "random-example_400": ("bernoulli", "uniform"),
    "fulfill-example_2500": ("poisson", "gaussian"),
    "iron-example_10000": ("bernoulli", "uniform"),
    "bos-example_600": ("poisson", "gaussian"),
    "orz-example_1800": ("bernoulli", "gaussian"),
}


def ensure_map_present(domain_dir: Path, map_name: str, source_map: Path) -> None:
    target = domain_dir / "maps" / map_name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.resolve() == source_map.resolve():
        return
    if not target.exists():
        shutil.copy2(source_map, target)


def generate_example_instance(repo: Path, spec: InstanceSpec) -> Dict[str, float]:
    domain_dir = repo / "Example Instances" / spec.domain
    maps_dir = domain_dir / "maps"
    tasks_dir = domain_dir / "tasks"
    agents_dir = domain_dir / "agents"
    maps_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)

    source_map = source_map_for(repo, spec)
    ensure_map_present(domain_dir, spec.map_name, source_map)
    height, width, _grid, traversable, e_cells, s_cells = load_map(source_map)
    if height <= 0 or width <= 0:
        raise ValueError(f"Invalid map dimensions for {spec.instance_id}")

    task_rng = random.Random(f"{spec.instance_id}:tasks:2026")
    agent_rng = random.Random(f"{spec.instance_id}:agents:2026")
    event_model, duration_model = EXAMPLE_DELAY_MODELS[spec.instance_id]

    if spec.domain == "warehouse.domain":
        tasks, realized = generate_warehouse_tasks(spec, width, e_cells, s_cells, task_rng)
    else:
        tasks, realized = generate_generic_tasks(spec, width, traversable, task_rng)

    agents = generate_agents(width, traversable, spec.agents, agent_rng)
    write_tasks(tasks_dir / f"{spec.instance_id}.tasks", tasks)
    write_agents(agents_dir / f"{spec.instance_id}.agents", agents)
    write_problem_json(domain_dir / f"{spec.instance_id}.json", spec, event_model, duration_model)

    realized["task_dist"] = spec.task_dist
    realized["event_model"] = event_model
    realized["duration_model"] = duration_model
    return realized


def cleanup_example_tree(repo: Path) -> None:
    root = repo / "Example Instances"
    keep: set[str] = {"example_from_main_round_manifest.json"}

    for spec in EXAMPLE_SPECS:
        keep.add(f"{spec.domain}/{spec.instance_id}.json")
        keep.add(f"{spec.domain}/agents/{spec.instance_id}.agents")
        keep.add(f"{spec.domain}/tasks/{spec.instance_id}.tasks")
        keep.add(f"{spec.domain}/maps/{spec.map_name}")

    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            rel = str(path.relative_to(root))
            if rel not in keep:
                path.unlink()

    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir() and path != root:
            try:
                path.rmdir()
            except OSError:
                pass


def main() -> None:
    repo = repo_root()
    manifest: Dict[str, Dict[str, float]] = {}

    for spec in EXAMPLE_SPECS:
        manifest[spec.instance_id] = generate_example_instance(repo, spec)

    manifest_path = repo / "Example Instances" / "example_from_main_round_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fout:
        json.dump(manifest, fout, indent=4)
        fout.write("\n")

    cleanup_example_tree(repo)

    print(f"Generated {len(EXAMPLE_SPECS)} example instances")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
