# -*- coding: UTF-8 -*-
"""Amend problem instances with delayConfig or generate a delay-parameter mesh."""

import argparse
import copy
import json
import os
import random
from typing import Dict, List, Tuple


AGENT_SIZE_CHOICES: List[float] = [round(0.1 * i, 1) for i in range(1, 11)]
REQUIRED_INSTANCE_KEYS = {"mapFile", "agentFile", "teamSize", "taskFile", "numTasksReveal", "version"}
DIFFICULTY_RANGES = {
    "super_easy": (1, 1),
    "super_easy1": (10, 10),
    "easy": (5, 10),
    "medium": (10, 20),
    "hard": (1, 40),
    "super_hard": (1, 100),
}
DELAY_PROBABILITIES = [0.02, 0.05, 0.1, 0.2, 0.3, 0.5]
DURATION_MODELS = ["uniform", "gaussian"]
EVENT_MODELS = ["bernoulli", "poisson"]
CURATED_PROFILES: List[Dict[str, object]] = [
    {"name": "super_easy1_p0p02_bernoulli_uniform", "difficulty": "super_easy1", "probability": 0.02, "event_model": "bernoulli", "duration_model": "uniform"},
    {"name": "super_easy1_p0p1_bernoulli_gaussian", "difficulty": "super_easy1", "probability": 0.1, "event_model": "bernoulli", "duration_model": "gaussian"},
    {"name": "super_easy1_p0p3_poisson_uniform", "difficulty": "super_easy1", "probability": 0.3, "event_model": "poisson", "duration_model": "uniform"},
    {"name": "super_easy1_p0p5_poisson_gaussian", "difficulty": "super_easy1", "probability": 0.5, "event_model": "poisson", "duration_model": "gaussian"},
    {"name": "easy_p0p02_bernoulli_uniform", "difficulty": "easy", "probability": 0.02, "event_model": "bernoulli", "duration_model": "uniform"},
    {"name": "easy_p0p1_bernoulli_gaussian", "difficulty": "easy", "probability": 0.1, "event_model": "bernoulli", "duration_model": "gaussian"},
    {"name": "easy_p0p3_poisson_uniform", "difficulty": "easy", "probability": 0.3, "event_model": "poisson", "duration_model": "uniform"},
    {"name": "easy_p0p5_poisson_gaussian", "difficulty": "easy", "probability": 0.5, "event_model": "poisson", "duration_model": "gaussian"},
    {"name": "medium_p0p02_bernoulli_uniform", "difficulty": "medium", "probability": 0.02, "event_model": "bernoulli", "duration_model": "uniform"},
    {"name": "medium_p0p1_bernoulli_gaussian", "difficulty": "medium", "probability": 0.1, "event_model": "bernoulli", "duration_model": "gaussian"},
    {"name": "medium_p0p3_poisson_uniform", "difficulty": "medium", "probability": 0.3, "event_model": "poisson", "duration_model": "uniform"},
    {"name": "medium_p0p5_poisson_gaussian", "difficulty": "medium", "probability": 0.5, "event_model": "poisson", "duration_model": "gaussian"},
    {"name": "hard_p0p02_bernoulli_uniform", "difficulty": "hard", "probability": 0.02, "event_model": "bernoulli", "duration_model": "uniform"},
    {"name": "hard_p0p1_bernoulli_gaussian", "difficulty": "hard", "probability": 0.1, "event_model": "bernoulli", "duration_model": "gaussian"},
    {"name": "hard_p0p3_poisson_uniform", "difficulty": "hard", "probability": 0.3, "event_model": "poisson", "duration_model": "uniform"},
    {"name": "hard_p0p5_poisson_gaussian", "difficulty": "hard", "probability": 0.5, "event_model": "poisson", "duration_model": "gaussian"},
]


def _random_communication_time(seed_value: str) -> int:
    return random.Random(seed_value).choice((1000, 3000, 5000))


def _gaussian_params_for_difficulty(diff_name: str) -> Dict[str, float]:
    """Return Gaussian parameters with harder difficulties having larger std."""
    if diff_name == "super_easy":
        return {"gaussMeanRatio": 0.5, "gaussStdRatio": 0.05}
    if diff_name == "super_easy1":
        return {"gaussMeanRatio": 0.5, "gaussStdRatio": 0.05}
    if diff_name == "easy":
        return {"gaussMeanRatio": 0.5, "gaussStdRatio": 0.12}
    if diff_name == "medium":
        return {"gaussMeanRatio": 0.5, "gaussStdRatio": 0.22}
    if diff_name == "hard":
        return {"gaussMeanRatio": 0.5, "gaussStdRatio": 0.35}
    return {"gaussMeanRatio": 0.5, "gaussStdRatio": 0.45}


def _discover_instance_json_files(proposal_dir: str) -> List[str]:
    json_files: List[str] = []
    for root, _, files in os.walk(proposal_dir):
        for name in files:
            if not name.endswith(".json"):
                continue
            if name == "cli.json":
                continue
            json_files.append(os.path.join(root, name))
    json_files.sort()
    return json_files


def _is_problem_instance(payload: Dict) -> bool:
    return REQUIRED_INSTANCE_KEYS.issubset(set(payload.keys()))


def _json_dump(path: str, payload: Dict) -> None:
    with open(path, mode="w", encoding="utf-8") as fout:
        json.dump(payload, fout, indent=4)
        fout.write("\n")


def _probability_tag(probability: float) -> str:
    rendered = f"{probability:.2f}" if probability < 0.1 else f"{probability:.1f}"
    return rendered.replace(".", "p")


def _variant_stem(base_stem: str, difficulty: str, probability: float) -> str:
    return f"{base_stem}__{difficulty}__p{_probability_tag(probability)}"


def _base_stem_from_name(stem: str) -> str:
    return stem.split("__")[0]


def _load_cli_config(cli_path: str) -> Dict[str, Dict[str, int]]:
    with open(cli_path, mode="r", encoding="utf-8") as fin:
        payload = json.load(fin)

    normalized: Dict[str, Dict[str, int]] = {}
    for stem, config in payload.items():
        if isinstance(config, int):
            normalized[stem] = {
                "simulation_time": config,
                "communication_time": _random_communication_time(stem),
            }
            continue
        normalized[stem] = {
            "simulation_time": int(config["simulation_time"]),
            "communication_time": int(config.get("communication_time", _random_communication_time(stem))),
        }
    return normalized


def _write_cli_config(cli_path: str, cli_config: Dict[str, Dict[str, int]]) -> None:
    with open(cli_path, mode="w", encoding="utf-8") as fout:
        json.dump(cli_config, fout, indent=4)
        fout.write("\n")


def _build_delay_config(
    seed: int,
    difficulty: str,
    probability: float,
    event_model: str,
    poisson_lambda: float,
    duration_model: str,
) -> Dict[str, float]:
    min_delay, max_delay = DIFFICULTY_RANGES[difficulty]
    gauss_params = _gaussian_params_for_difficulty(difficulty)
    return {
        "seed": seed,
        "minDelay": min_delay,
        "maxDelay": max_delay,
        "eventModel": event_model,
        "pDelay": probability,
        "durationModel": duration_model,
        "gaussMeanRatio": gauss_params["gaussMeanRatio"],
        "gaussStdRatio": gauss_params["gaussStdRatio"],
    }


def generate_delay_mesh(
    proposal_dir: str,
    seed: int,
    agent_counter: int,
    agent_size: float,
    poisson_lambda: float,
    overwrite: bool,
    clean_existing_variants: bool,
) -> Dict[str, int]:
    cli_path = os.path.join(proposal_dir, "cli.json")
    if not os.path.isfile(cli_path):
        raise SystemExit(f"Missing cli.json: {cli_path}")

    base_cli_config = _load_cli_config(cli_path)
    source_json_files = []
    existing_variant_files = []

    for json_file in _discover_instance_json_files(proposal_dir):
        stem = os.path.splitext(os.path.basename(json_file))[0]
        if "__" in stem:
            existing_variant_files.append(json_file)
            continue
        source_json_files.append(json_file)

    stats = {
        "processed": 0,
        "generated": 0,
        "removed_variants": 0,
    }

    if clean_existing_variants:
        for json_file in existing_variant_files:
            os.remove(json_file)
            stats["removed_variants"] += 1

    mesh_cli_config: Dict[str, Dict[str, int]] = dict(base_cli_config)

    for json_file in source_json_files:
        stats["processed"] += 1
        with open(json_file, mode="r", encoding="utf-8") as fin:
            payload = json.load(fin)

        if not _is_problem_instance(payload):
            continue

        base_stem = os.path.splitext(os.path.basename(json_file))[0]
        if base_stem not in base_cli_config:
            raise SystemExit(f"Missing CLI entry for {base_stem}")

        for difficulty, (min_delay, max_delay) in DIFFICULTY_RANGES.items():
            gauss_params = _gaussian_params_for_difficulty(difficulty)
            for probability in DELAY_PROBABILITIES:
                variant_stem = _variant_stem(base_stem, difficulty, probability)
                variant_path = os.path.join(os.path.dirname(json_file), f"{variant_stem}.json")

                if os.path.exists(variant_path) and not overwrite:
                    raise SystemExit(f"Variant already exists (use --overwrite): {variant_path}")

                variant_payload = copy.deepcopy(payload)
                variant_payload["delayConfig"] = {
                    "seed": seed,
                    "minDelay": min_delay,
                    "maxDelay": max_delay,
                    "eventModel": "bernoulli",
                    "pDelay": probability,
                    "durationModel": "uniform",
                    "gaussMeanRatio": gauss_params["gaussMeanRatio"],
                    "gaussStdRatio": gauss_params["gaussStdRatio"],
                }
                variant_payload["agentCounter"] = agent_counter
                variant_payload["agentSize"] = agent_size

                _json_dump(variant_path, variant_payload)
                mesh_cli_config[variant_stem] = dict(base_cli_config[base_stem])
                stats["generated"] += 1

    _write_cli_config(cli_path, mesh_cli_config)
    return stats


def amend_instances(
    proposal_dir: str,
    seed: int,
    agent_counter: int,
    event_model: str,
    p_delay: float,
    poisson_lambda: float,
    overwrite: bool,
) -> Dict[str, int]:
    rng = random.Random(seed)
    stats = {
        "processed": 0,
        "amended": 0,
        "skipped": 0,
    }

    for json_file in _discover_instance_json_files(proposal_dir):
        stats["processed"] += 1

        with open(json_file, mode="r", encoding="utf-8") as fin:
            payload = json.load(fin)

        if not _is_problem_instance(payload):
            stats["skipped"] += 1
            continue

        if "delayConfig" in payload and not overwrite:
            stats["skipped"] += 1
            continue

        agent_size = rng.choice(AGENT_SIZE_CHOICES)
        chosen_difficulty = rng.choice(list(DIFFICULTY_RANGES.keys()))
        min_delay, max_delay = DIFFICULTY_RANGES[chosen_difficulty]
        chosen_duration_model = rng.choice(DURATION_MODELS)
        chosen_event_model = rng.choice(EVENT_MODELS) if event_model == "random" else event_model
        gauss_params = _gaussian_params_for_difficulty(chosen_difficulty)

        payload["delayConfig"] = {
            "seed": seed,
            "minDelay": min_delay,
            "maxDelay": max_delay,
            "eventModel": chosen_event_model,
            "pDelay": p_delay,
            "durationModel": chosen_duration_model,
            "gaussMeanRatio": gauss_params["gaussMeanRatio"],
            "gaussStdRatio": gauss_params["gaussStdRatio"],
        }
        payload["agentCounter"] = agent_counter
        payload["agentSize"] = agent_size

        with open(json_file, mode="w", encoding="utf-8") as fout:
            json.dump(payload, fout, indent=4)
            fout.write("\n")

        stats["amended"] += 1

    return stats


def curate_instances(
    proposal_dir: str,
    seed: int,
    agent_counter: int,
    agent_size: float,
    poisson_lambda: float,
    overwrite: bool,
) -> Dict[str, object]:
    cli_path = os.path.join(proposal_dir, "cli.json")
    if not os.path.isfile(cli_path):
        raise SystemExit(f"Missing cli.json: {cli_path}")

    existing_cli_config = _load_cli_config(cli_path)
    grouped_files: Dict[str, List[str]] = {}

    for json_file in _discover_instance_json_files(proposal_dir):
        stem = os.path.splitext(os.path.basename(json_file))[0]
        if stem in {"cli", "SweepsResults"}:
            continue
        grouped_files.setdefault(_base_stem_from_name(stem), []).append(json_file)

    stats = {
        "processed": 0,
        "written": 0,
        "removed_variants": 0,
        "assignments": [],
    }
    curated_cli_config: Dict[str, Dict[str, int]] = {}

    for idx, base_stem in enumerate(sorted(grouped_files)):
        profile = CURATED_PROFILES[idx % len(CURATED_PROFILES)]
        group_paths = sorted(grouped_files[base_stem])
        source_path = None
        payload = None

        for candidate in group_paths:
            with open(candidate, mode="r", encoding="utf-8") as fin:
                candidate_payload = json.load(fin)
            if _is_problem_instance(candidate_payload):
                source_path = candidate
                payload = candidate_payload
                break

        if payload is None or source_path is None:
            continue

        stats["processed"] += 1
        target_path = os.path.join(os.path.dirname(source_path), f"{base_stem}.json")
        if os.path.exists(target_path) and target_path not in group_paths and not overwrite:
            raise SystemExit(f"Target already exists (use --overwrite): {target_path}")

        payload["delayConfig"] = _build_delay_config(
            seed=seed,
            difficulty=profile["difficulty"],
            probability=profile["probability"],
            event_model=profile["event_model"],
            poisson_lambda=poisson_lambda,
            duration_model=profile["duration_model"],
        )
        payload["agentCounter"] = agent_counter
        payload["agentSize"] = agent_size

        _json_dump(target_path, payload)
        stats["written"] += 1
        stats["assignments"].append(f"{base_stem}:{profile['name']}")

        simulation_key = None
        if base_stem in existing_cli_config:
            simulation_key = base_stem
        else:
            for key in existing_cli_config:
                if _base_stem_from_name(key) == base_stem:
                    simulation_key = key
                    break
        if simulation_key is not None:
            curated_cli_config[base_stem] = dict(existing_cli_config[simulation_key])

        for old_path in group_paths:
            if old_path == target_path:
                continue
            os.remove(old_path)
            stats["removed_variants"] += 1

    _write_cli_config(cli_path, curated_cli_config)
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Amend problem instances with delayConfig, generate a delay-parameter mesh, or curate sweep variants."
    )

    default_proposal_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "proposal",
    )

    parser.add_argument("--proposalDir", type=str, default=default_proposal_dir)
    parser.add_argument("--mode", choices=("amend", "mesh", "curate"), default="amend")

    parser.add_argument("--seed", type=int, default=0, help="Seed for deterministic delay generation.")
    parser.add_argument("--agentCounter", type=int, default=10, help="Default agentCounter in delayConfig.")
    parser.add_argument("--agentSize", type=float, default=1.0, help="Agent size to store in problem JSONs.")

    parser.add_argument("--eventModel", type=str, default="random", help="random|bernoulli|poisson")
    parser.add_argument("--pDelay", type=float, default=0.02)
    parser.add_argument("--poissonLambda", type=float, default=2.0)
    parser.add_argument("--durationModel", type=str, default="uniform", help="uniform|gaussian")

    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing delayConfig blocks.")
    parser.add_argument(
        "--cleanExistingVariants",
        action="store_true",
        help="In mesh mode, remove existing variant JSONs whose names contain '__' before regenerating.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not os.path.isdir(args.proposalDir):
        raise SystemExit(f"Proposal directory does not exist: {args.proposalDir}")
    if args.agentCounter <= 0:
        raise SystemExit("--agentCounter must be > 0")
    if args.agentSize <= 0:
        raise SystemExit("--agentSize must be > 0")
    if args.eventModel not in {"random", *EVENT_MODELS}:
        raise SystemExit("--eventModel must be one of: random, bernoulli, poisson")
    if args.durationModel not in DURATION_MODELS:
        raise SystemExit("--durationModel must be one of: uniform, gaussian")

    if args.mode == "mesh":
        stats = generate_delay_mesh(
            proposal_dir=args.proposalDir,
            seed=args.seed,
            agent_counter=args.agentCounter,
            agent_size=args.agentSize,
            poisson_lambda=args.poissonLambda,
            overwrite=args.overwrite,
            clean_existing_variants=args.cleanExistingVariants,
        )
        print(
            "Mesh generation complete. "
            f"Processed={stats['processed']}, "
            f"Generated={stats['generated']}, "
            f"RemovedVariants={stats['removed_variants']}"
        )
        return

    if args.mode == "curate":
        stats = curate_instances(
            proposal_dir=args.proposalDir,
            seed=args.seed,
            agent_counter=args.agentCounter,
            agent_size=args.agentSize,
            poisson_lambda=args.poissonLambda,
            overwrite=args.overwrite,
        )
        print(
            "Curation complete. "
            f"Processed={stats['processed']}, "
            f"Written={stats['written']}, "
            f"RemovedVariants={stats['removed_variants']}"
        )
        print("Assignments:")
        for assignment in stats["assignments"]:
            print(f"  {assignment}")
        return

    stats = amend_instances(
        proposal_dir=args.proposalDir,
        seed=args.seed,
        agent_counter=args.agentCounter,
        event_model=args.eventModel,
        p_delay=args.pDelay,
        poisson_lambda=args.poissonLambda,
        overwrite=args.overwrite,
    )

    print(
        "Amendment complete. "
        f"Processed={stats['processed']}, "
        f"Amended={stats['amended']}, "
        f"Skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    main()
