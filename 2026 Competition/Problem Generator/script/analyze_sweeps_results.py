#!/usr/bin/env python3
"""Analyze sweep evaluation results by map type and delay configuration."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

DELAY_ORDER = ["super_easy", "super_easy1", "easy", "medium", "hard", "super_hard"]
DELAY_RANK = {label: index for index, label in enumerate(DELAY_ORDER)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read a SweepsResults.json file and summarize performance by map type "
            "and delay configuration."
        )
    )
    parser.add_argument(
        "results",
        nargs="?",
        default="Main Round Evaluation Instances/SweepsResults.json",
        help="Path to SweepsResults.json",
    )
    parser.add_argument(
        "--instances-root",
        default=None,
        help=(
            "Directory containing the instance JSON files referenced by the sweep. "
            "Defaults to the parent directory of the results file."
        ),
    )
    parser.add_argument(
        "--metric",
        choices=["numTaskFinished", "throughput"],
        default="numTaskFinished",
        help="Primary metric used in the per-map pivot tables.",
    )
    return parser.parse_args()


def parse_task_name(task_name: str) -> tuple[str, str | None, str | None]:
    parts = task_name.split("__")
    base = parts[0]
    delay_label = parts[1] if len(parts) > 1 else None
    delay_slug = parts[2] if len(parts) > 2 else None
    return base, delay_label, delay_slug


def format_float(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def format_delay_probability(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:g}"


def delay_sort_key(label: str) -> tuple[int, str]:
    return (DELAY_RANK.get(label, len(DELAY_ORDER)), label)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def resolve_results_path(raw_path: str) -> Path:
    candidates = [Path(raw_path)]

    if raw_path == "Main Round Evaluation Instances/SweepsResults.json":
        candidates.append(Path("MainRoundEvaluationInstances/SweepsResults.json"))
    elif raw_path == "MainRoundEvaluationInstances/SweepsResults.json":
        candidates.append(Path("Main Round Evaluation Instances/SweepsResults.json"))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def build_instance_index(instances_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in instances_root.glob("*/*.json"):
        index[path.stem] = path
    return index


def infer_map_type(instance_path: Path, instance_data: dict) -> str:
    domain = instance_path.parent.name
    if domain.endswith(".domain"):
        return domain[:-7]

    map_file = instance_data.get("mapFile", "")
    map_name = Path(map_file).name.lower()
    if "warehouse" in map_name or "sortation" in map_name:
        return "warehouse"
    if "random" in map_name:
        return "random"
    if "paris" in map_name or "boston" in map_name or "city" in map_name:
        return "city"
    return Path(map_file).stem or "unknown"


def summarize_rows(rows: list[dict], base_task_bests: dict[str, dict[str, float]]) -> dict[str, float]:
    return {
        "count": len(rows),
        "avg_finished": mean(row["numTaskFinished"] for row in rows),
        "avg_throughput": mean(row["throughput"] for row in rows),
        "avg_norm_finished": mean(
            (
                row["numTaskFinished"] / base_task_bests[row["base_task"]]["numTaskFinished"]
                if base_task_bests[row["base_task"]]["numTaskFinished"]
                else 0.0
            )
            for row in rows
        ),
        "avg_norm_throughput": mean(
            (
                row["throughput"] / base_task_bests[row["base_task"]]["throughput"]
                if base_task_bests[row["base_task"]]["throughput"]
                else 0.0
            )
            for row in rows
        ),
        "avg_timeouts": mean(row["numEntryTimeouts"] for row in rows),
        "avg_schedule_errors": mean(row["numScheduleErrors"] for row in rows),
        "avg_planner_errors": mean(row["numPlannerErrors"] for row in rows),
    }


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    print("  ".join(header.ljust(widths[i]) for i, header in enumerate(headers)))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def main() -> None:
    args = parse_args()
    results_path = resolve_results_path(args.results)
    instances_root = Path(args.instances_root) if args.instances_root else results_path.parent

    results_data = load_json(results_path)
    evaluation_rows = results_data.get("evaluation_data", [])
    instance_index = build_instance_index(instances_root)

    enriched_rows: list[dict] = []
    missing_tasks: list[str] = []

    for row in evaluation_rows:
        task_name = row["task"]
        instance_path = instance_index.get(task_name)
        if instance_path is None:
            missing_tasks.append(task_name)
            continue

        instance_data = load_json(instance_path)
        delay_config = instance_data.get("delayConfig", {})
        base_task, delay_label, delay_slug = parse_task_name(task_name)
        makespan = row.get("makespan", 0) or 0
        num_task_finished = row.get("numTaskFinished", 0)

        enriched_rows.append(
            {
                **row,
                "base_task": base_task,
                "delay_label": delay_label or "-",
                "delay_slug": delay_slug or "-",
                "map_type": infer_map_type(instance_path, instance_data),
                "map_name": Path(instance_data.get("mapFile", "")).stem or base_task,
                "instance_path": str(instance_path),
                "minDelay": delay_config.get("minDelay"),
                "maxDelay": delay_config.get("maxDelay"),
                "pDelay": delay_config.get("pDelay"),
                "eventModel": delay_config.get("eventModel"),
                "durationModel": delay_config.get("durationModel"),
                "gaussStdRatio": delay_config.get("gaussStdRatio"),
                "throughput": (num_task_finished / makespan) if makespan else 0.0,
            }
        )

    if missing_tasks:
        raise SystemExit(
            "Missing instance JSON files for tasks: " + ", ".join(sorted(missing_tasks))
        )

    if not enriched_rows:
        raise SystemExit("No evaluation rows found.")

    print(f"Results file: {results_path}")
    print(f"Instances root: {instances_root}")
    print(f"Rows analyzed: {len(enriched_rows)}")
    print()

    by_map_type: dict[str, list[dict]] = defaultdict(list)
    by_base_task: dict[str, list[dict]] = defaultdict(list)
    for row in enriched_rows:
        by_map_type[row["map_type"]].append(row)
        by_base_task[row["base_task"]].append(row)

    base_task_bests = {
        base_task: {
            "numTaskFinished": max(row["numTaskFinished"] for row in rows),
            "throughput": max(row["throughput"] for row in rows),
        }
        for base_task, rows in by_base_task.items()
    }

    aggregate_rows: list[list[str]] = []
    for map_type in sorted(by_map_type):
        grouped: dict[tuple, list[dict]] = defaultdict(list)
        for row in by_map_type[map_type]:
            key = (
                row["delay_label"],
                row["pDelay"],
                row["minDelay"],
                row["maxDelay"],
                row["gaussStdRatio"],
            )
            grouped[key].append(row)

        for key in sorted(
            grouped,
            key=lambda item: (
                DELAY_RANK.get(str(item[0]), len(DELAY_ORDER)),
                str(item[0]),
                float(item[1]) if item[1] is not None else -1.0,
                item[2] if item[2] is not None else -1,
                item[3] if item[3] is not None else -1,
            ),
        ):
            rows = grouped[key]
            summary = summarize_rows(rows, base_task_bests)
            aggregate_rows.append(
                [
                    map_type,
                    key[0] or "-",
                    format_delay_probability(key[1]),
                    f"{key[2]}-{key[3]}",
                    format_float(key[4]),
                    str(int(summary["count"])),
                    format_float(summary["avg_finished"]),
                    format_float(summary["avg_norm_finished"] * 100.0),
                    format_float(summary["avg_throughput"], 4),
                    format_float(summary["avg_timeouts"]),
                    format_float(summary["avg_schedule_errors"]),
                    format_float(summary["avg_planner_errors"]),
                ]
            )

    print("Aggregate Summary By Map Type And Delay Config")
    print_table(
        [
            "map_type",
            "delay",
            "pDelay",
            "range",
            "stdRatio",
            "n",
            "avgFinished",
            "avgFinished%Best",
            "avgThroughput",
            "avgTimeouts",
            "avgSchedErr",
            "avgPlanErr",
        ],
        aggregate_rows,
    )

    metric_label = "finished" if args.metric == "numTaskFinished" else "throughput"
    print()
    print(f"Per-Map Pivot By Delay Config ({metric_label})")

    for base_task in sorted(by_base_task):
        rows = by_base_task[base_task]
        map_type = rows[0]["map_type"]
        map_name = rows[0]["map_name"]
        best_finished = max(row["numTaskFinished"] for row in rows)
        best_throughput = max(row["throughput"] for row in rows)

        pivot: dict[str, dict[str, str]] = defaultdict(dict)
        delay_ranges: dict[str, str] = {}
        p_delay_values = sorted({row["pDelay"] for row in rows if row["pDelay"] is not None})

        for row in rows:
            delay_ranges[row["delay_label"]] = f"{row['minDelay']}-{row['maxDelay']}"
            if args.metric == "numTaskFinished":
                value = str(row["numTaskFinished"])
                normalized = (
                    (row["numTaskFinished"] / best_finished) * 100.0 if best_finished else 0.0
                )
            else:
                value = format_float(row["throughput"], 4)
                normalized = (
                    (row["throughput"] / best_throughput) * 100.0 if best_throughput else 0.0
                )

            pivot[row["delay_label"]][format_delay_probability(row["pDelay"])] = (
                f"{value} ({normalized:.1f}%)"
            )

        print()
        print(
            f"{base_task}  map_type={map_type}  map={map_name}  "
            f"best_finished={best_finished}  best_throughput={best_throughput:.4f}"
        )
        headers = ["delay", "range"] + [format_delay_probability(value) for value in p_delay_values]
        table_rows: list[list[str]] = []
        for delay_label in sorted(pivot, key=delay_sort_key):
            table_rows.append(
                [delay_label, delay_ranges.get(delay_label, "-")]
                + [pivot[delay_label].get(format_delay_probability(value), "-") for value in p_delay_values]
            )
        print_table(headers, table_rows)


if __name__ == "__main__":
    main()
