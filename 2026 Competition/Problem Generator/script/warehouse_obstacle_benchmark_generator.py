# -*- coding: UTF-8 -*-
"""Generate a warehouse benchmark instance with extra mid-map obstacle bands."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Dict, List

from warehouse_map_generator import WarehouseMapGenerator
from warehouse_task_generator import WarehouseTaskGenerator


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _warehouse_storage_bounds(generator: WarehouseMapGenerator) -> tuple[int, int, int, int]:
    start_row = (
        generator.config["stationW"] + generator.config["operWidth"]
        if generator.has_station["N"]
        else generator.config["pillarWidth"]
    )
    start_col = (
        generator.config["stationW"] + generator.config["operWidth"]
        if generator.has_station["W"]
        else generator.config["pillarWidth"]
    )
    end_row = (
        generator.config["mapHeight"] - generator.config["stationW"] - generator.config["operWidth"]
        if generator.has_station["S"]
        else generator.config["mapHeight"] - generator.config["pillarWidth"]
    )
    end_col = (
        generator.config["mapWidth"] - generator.config["stationW"] - generator.config["operWidth"]
        if generator.has_station["E"]
        else generator.config["mapWidth"] - generator.config["pillarWidth"]
    )
    return start_row, start_col, end_row, end_col


def _detect_aisle_spans(generator: WarehouseMapGenerator) -> List[tuple[int, int]]:
    start_row, start_col, end_row, end_col = _warehouse_storage_bounds(generator)

    for row in range(start_row, end_row):
        line = generator.warehouse[row][start_col:end_col]
        spans: List[tuple[int, int]] = []
        seg_start = None
        for idx, cell in enumerate(line):
            if cell != "." and seg_start is None:
                seg_start = idx
            elif cell == "." and seg_start is not None:
                spans.append((start_col + seg_start, start_col + idx))
                seg_start = None
        if seg_start is not None:
            spans.append((start_col + seg_start, start_col + len(line)))

        if len(spans) > 1:
            return spans

    return [(start_col, end_col)]


def _apply_middle_obstacle_bands(
    generator: WarehouseMapGenerator,
    rng: random.Random,
    band_count: int,
    band_height_min: int,
    band_height_max: int,
    margin_cols: int,
) -> Dict[str, List[tuple[int, int]]]:
    start_row, start_col, end_row, end_col = _warehouse_storage_bounds(generator)
    aisle_spans = _detect_aisle_spans(generator)
    row_min = start_row + 1
    row_max = end_row - 2

    if row_max < row_min:
        return {}

    chosen_bands: Dict[str, List[tuple[int, int]]] = {}

    for aisle_idx, (span_start, span_end) in enumerate(aisle_spans):
        col_min = span_start + margin_cols
        col_max = span_end - margin_cols
        if col_max <= col_min:
            continue

        occupied_rows = set()
        aisle_key = f"aisle_{aisle_idx}:{span_start}-{span_end}"
        chosen_bands[aisle_key] = []

        for _ in range(band_count):
            height = rng.randint(band_height_min, band_height_max)
            placed = False
            for _attempt in range(200):
                band_start = rng.randint(row_min, max(row_min, row_max - height + 1))
                band_rows = range(band_start, band_start + height)
                if any(row in occupied_rows for row in band_rows):
                    continue
                for row in band_rows:
                    for col in range(col_min, col_max):
                        generator.warehouse[row][col] = "@"
                    occupied_rows.add(row)
                chosen_bands[aisle_key].append((band_start, height))
                placed = True
                break
            if not placed:
                break

    return chosen_bands


def _save_map(generator: WarehouseMapGenerator, output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as fout:
        fout.write("type octile\n")
        fout.write(f"height {generator.config['mapHeight']}\n")
        fout.write(f"width {generator.config['mapWidth']}\n")
        fout.write("map\n")
        for row in generator.warehouse:
            fout.write("".join(row) + "\n")


def _write_problem_json(
    output_path: Path,
    map_name: str,
    task_name: str,
    agent_name: str,
    team_size: int,
    reveal_num: float,
    delay_config: Dict[str, float],
    agent_counter: int,
    agent_size: float,
) -> None:
    payload = {
        "mapFile": f"maps/{map_name}",
        "agentFile": f"agents/{agent_name}",
        "teamSize": team_size,
        "taskFile": f"tasks/{task_name}",
        "numTasksReveal": reveal_num,
        "version": "2026 LoRR",
        "agentCounter": agent_counter,
        "agentSize": agent_size,
        "delayConfig": delay_config,
    }
    with output_path.open("w", encoding="utf-8") as fout:
        json.dump(payload, fout, indent=4)
        fout.write("\n")


def _load_cli_config(cli_path: Path) -> Dict[str, Dict[str, int]]:
    payload: Dict[str, object] = {}
    if cli_path.exists():
        with cli_path.open("r", encoding="utf-8") as fin:
            payload = json.load(fin)

    normalized: Dict[str, Dict[str, int]] = {}
    for problem_stem, config in payload.items():
        if isinstance(config, int):
            normalized[problem_stem] = {
                "simulation_time": config,
                "communication_time": _random_communication_time(random.Random(problem_stem)),
            }
            continue
        normalized[problem_stem] = {
            "simulation_time": int(config["simulation_time"]),
            "communication_time": int(
                config.get("communication_time", _random_communication_time(random.Random(problem_stem)))
            ),
        }
    return normalized


def _random_communication_time(rng: random.Random) -> int:
    return rng.choice((1000, 3000, 5000))


def _update_cli_config(cli_path: Path, problem_stem: str, simulation_time: int, rng: random.Random) -> None:
    payload = _load_cli_config(cli_path)
    existing = payload.get(problem_stem, {})
    payload[problem_stem] = {
        "simulation_time": simulation_time,
        "communication_time": int(existing.get("communication_time", _random_communication_time(rng))),
    }
    with cli_path.open("w", encoding="utf-8") as fout:
        json.dump(payload, fout, indent=4)
        fout.write("\n")


def parse_args() -> argparse.Namespace:
    repo_root = _repo_root()
    parser = argparse.ArgumentParser(
        description="Generate a warehouse benchmark instance and add random mid-map obstacle bands."
    )

    parser.add_argument("--config", type=str, required=True, help="Warehouse map config YAML relative to this script.")
    parser.add_argument("--benchmarkFolder", type=str, required=True, help="Output benchmark folder.")
    parser.add_argument("--problemName", type=str, required=True, help="Base name used for map/tasks/problem files.")
    parser.add_argument("--teamSize", type=int, default=10000, help="Number of agents.")
    parser.add_argument("--taskNum", type=int, default=100000, help="Number of tasks.")
    parser.add_argument("--taskBuckets", type=int, default=5, help="Warehouse task distance buckets.")
    parser.add_argument("--minEPT", type=int, default=2, help="Minimum errands per task.")
    parser.add_argument("--maxEPT", type=int, default=2, help="Maximum errands per task.")
    parser.add_argument("--numTasksReveal", type=float, default=1.5, help="Number of tasks revealed.")
    parser.add_argument("--warehouseTaskMode", type=int, choices=[2023, 2024], default=2023,
                        help="Warehouse task generator mode. Default uses 2023 to avoid plotting.")

    parser.add_argument("--seed", type=int, default=0, help="Random seed for obstacle placement.")
    parser.add_argument("--obstacleBands", type=int, default=2, help="Number of obstacle bands to place.")
    parser.add_argument("--obstacleBandHeightMin", type=int, default=2, help="Minimum obstacle-band height.")
    parser.add_argument("--obstacleBandHeightMax", type=int, default=4, help="Maximum obstacle-band height.")
    parser.add_argument("--obstacleMarginCols", type=int, default=0, help="Columns to leave open on each side.")

    parser.add_argument("--simulationTime", type=int, default=50000, help="Simulation time entry to write.")
    parser.add_argument(
        "--cliFile",
        type=str,
        default=str(repo_root / "MainRoundEvaluationInstances" / "cli.json"),
        help="Path to cli.json to update.",
    )

    parser.add_argument("--delaySeed", type=int, default=0)
    parser.add_argument("--minDelay", type=int, default=1)
    parser.add_argument("--maxDelay", type=int, default=3)
    parser.add_argument("--eventModel", choices=["bernoulli", "poisson"], default="bernoulli")
    parser.add_argument("--pDelay", type=float, default=0.02)
    parser.add_argument("--durationModel", choices=["uniform", "gaussian"], default="gaussian")
    parser.add_argument("--gaussMeanRatio", type=float, default=0.5)
    parser.add_argument("--gaussStdRatio", type=float, default=0.22)
    parser.add_argument("--agentCounter", type=int, default=10)
    parser.add_argument("--agentSize", type=float, default=1.0)

    args = parser.parse_args()
    if args.maxEPT < args.minEPT:
        parser.error("--maxEPT must be >= --minEPT")
    if args.obstacleBandHeightMax < args.obstacleBandHeightMin:
        parser.error("--obstacleBandHeightMax must be >= --obstacleBandHeightMin")
    return args


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    benchmark_folder = Path(args.benchmarkFolder)
    maps_dir = benchmark_folder / "maps"
    tasks_dir = benchmark_folder / "tasks"
    agents_dir = benchmark_folder / "agents"
    _ensure_dir(maps_dir)
    _ensure_dir(tasks_dir)
    _ensure_dir(agents_dir)

    map_filename = f"{args.problemName}.map"
    task_filename = f"{args.problemName}.tasks"
    agent_filename = f"{args.problemName}_{args.teamSize}.agents"
    problem_filename = f"{args.problemName}_{args.teamSize}.json"

    generator_args = argparse.Namespace(
        config=args.config,
        mapWidth=None,
        mapHeight=None,
        output=map_filename,
        stationNumber=None,
        pillarWidth=None,
        operWidth=None,
        stationConfig=None,
        storageSize=None,
        stationDistance=None,
        corridorWidth=None,
    )
    map_generator = WarehouseMapGenerator(generator_args)
    map_generator.load_stations()
    map_generator.load_storages()
    chosen_bands = _apply_middle_obstacle_bands(
        map_generator,
        rng=rng,
        band_count=args.obstacleBands,
        band_height_min=args.obstacleBandHeightMin,
        band_height_max=args.obstacleBandHeightMax,
        margin_cols=args.obstacleMarginCols,
    )

    map_path = maps_dir / map_filename
    _save_map(map_generator, map_path)

    task_generator = WarehouseTaskGenerator()
    if args.taskBuckets == -1:
        tasks = task_generator.random_generate(
            args.taskNum,
            str(map_path),
            minEPT=args.minEPT,
            maxEPT=args.maxEPT,
        )
    elif args.warehouseTaskMode == 2024:
        tasks = task_generator.generate_amazon_warehouse_tasks(
            taskNum=args.taskNum,
            map_name=str(map_path),
            m_buckets=args.taskBuckets,
            minEPT=args.minEPT,
            maxEPT=args.maxEPT,
        )
    else:
        tasks = task_generator.distribute_generate(
            args.taskNum,
            str(map_path),
            args.taskBuckets,
            args.minEPT,
            args.maxEPT,
        )
    task_generator.generate_txt(tasks, str(tasks_dir / task_filename))
    task_generator.generate_agents(args.teamSize, str(map_path), str(agents_dir / agent_filename))

    delay_config = {
        "seed": args.delaySeed,
        "minDelay": args.minDelay,
        "maxDelay": args.maxDelay,
        "eventModel": args.eventModel,
        "pDelay": args.pDelay,
        "durationModel": args.durationModel,
        "gaussMeanRatio": args.gaussMeanRatio,
        "gaussStdRatio": args.gaussStdRatio,
    }
    _write_problem_json(
        benchmark_folder / problem_filename,
        map_name=map_filename,
        task_name=task_filename,
        agent_name=agent_filename,
        team_size=args.teamSize,
        reveal_num=args.numTasksReveal,
        delay_config=delay_config,
        agent_counter=args.agentCounter,
        agent_size=args.agentSize,
    )

    _update_cli_config(Path(args.cliFile), f"{args.problemName}_{args.teamSize}", args.simulationTime, rng)
    print(f"Generated benchmark at: {benchmark_folder}")
    print(f"Obstacle bands: {chosen_bands}")


if __name__ == "__main__":
    main()
