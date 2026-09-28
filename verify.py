#!/usr/bin/env python3
"""Run the published finite verification from a source-only checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(command, label):
    print(label, flush=True)
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {command}")
    print(f"  passed ({time.monotonic() - started:.2f}s)", flush=True)
    return result.stdout


def load(relative):
    return json.loads((ROOT / relative).read_text())


def check_published_counts():
    from published_reference import PUBLISHED_120_SHA256

    build = load("reports/build.json")
    cert = load("reports/certificate_checks.json")
    math = load("reports/math_checks.json")
    dispatch = load("machines/RH_121.dispatch.json")
    digest = hashlib.sha256((ROOT / "machines/RH_120.tm").read_bytes()).hexdigest()
    require(digest == PUBLISHED_120_SHA256, "Generated table differs from Appendix I")
    require(build["raw_counts"] == {"framework": 59, "decision_DAG": 63, "total": 122},
            "Unexpected named-state counts")
    require((build["predecessor_states"], build["final_states"], build["transitions"]) == (121, 120, 240),
            "Unexpected machine sizes")
    require(build["G_bits"] == 2140, "Unexpected transition-integer bit length")
    control = build["control_bisimulation"]
    require((control["operation_boundary_pairs"], control["outcome_edges"], control["halting_pairs"]) == (84, 125, 1)
            and control["all_decrement_outcomes_checked"], "Unexpected control certificate")
    require((cert["state_window_pairs"], cert["closure_obligations"], cert["projected_reachable_reads"]) == (1621, 3218, 240),
            "Unexpected window certificate")
    require(cert["excluded_reads"] == [[37, 0], [97, 0]], "Unexpected excluded state/read pairs")
    require(len(build["negative_controls_rejected"]) == 2 and len(cert["negative_controls_rejected"]) == 5,
            "Negative-control checks did not all run")
    require((dispatch["terminal_paths"], dispatch["maximum_word_length"], dispatch["maximum_consecutive_zeros"], dispatch["scanner_states"]) == (121, 18, 3, 4),
            "Unexpected dispatcher certificate")
    counts = math["counts"]
    expected = {"fold_unit_cases": 343, "transform_unit_cases": 343,
                "split_divider_and_reconstruction_cases": 1960,
                "offset_digit_witnesses": 4944, "scaling_clock_cases": 100000,
                "unit_conserving_scaling_cases": 10000,
                "small_range_rational_inequalities": 6, "self_sieve_identities": 4095,
                "complete_host_integer_stages": 255, "intermediate_product_invariants": 32640}
    require(counts == expected, "Host-integer checks did not cover the expected cases")
    require([row["n"] for row in math["stages"]] == list(range(2, 257)), "Incomplete stage coverage")
    print("Published table fingerprint, certificate sizes, and arithmetic coverage verified.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-only", action="store_true", help="skip C++ compilation and literal tape replays")
    parser.add_argument("--cxx", default=os.environ.get("CXX", "c++"), help="C++ compiler executable (default: CXX or c++)")
    args = parser.parse_args()
    require(sys.version_info >= (3, 10), "Python 3.10 or newer is required")
    require(__debug__ and not sys.flags.optimize, "Run without -O, -OO, or PYTHONOPTIMIZE; the published checks use assertions")
    compiler = None
    if not args.python_only:
        compiler = shutil.which(args.cxx)
        require(compiler is not None, "C++ compiler not found. Install g++/clang++, pass --cxx, or use --python-only")

    started = time.monotonic()
    run([sys.executable, "-B", "reproduce.py", "--test"], "Rebuilding machines and running arithmetic/control checks...")
    run([sys.executable, "-B", "verify_certificate.py"], "Running the standalone certificate checker...")
    check_published_counts()

    if args.python_only:
        print(f"Python verification passed ({time.monotonic() - started:.2f}s). Literal tape replays were skipped.")
        return

    (ROOT / "build").mkdir(exist_ok=True)
    outputs = {}
    for name in ("bootstrap_check", "stage_check"):
        binary = ROOT / "build" / (name + (".exe" if os.name == "nt" else ""))
        run([compiler, "-O3", "-std=c++17", str(ROOT / (name + ".cpp")), "-o", str(binary)],
            f"Compiling {name}.cpp...")
        outputs[name] = run([str(binary), "machines/RH_121_raw_named.tm"], f"Running {name} literal tape replay...")

    require(outputs["bootstrap_check"].strip() == "bootstrap certificate verified", "Unexpected bootstrap result")
    stages = json.loads(outputs["stage_check"])
    expected_stages = [
        {"completed_endpoint": 0, "steps": 89775610, "m": 0},
        {"completed_endpoint": 2, "steps": 92233600, "m": 1},
        {"completed_endpoint": 3, "steps": 113387256, "m": 2},
        {"completed_endpoint": 4, "steps": 208951810, "m": 3},
    ]
    require(stages == expected_stages, "Literal replay step counts differ from the paper")
    print("Bootstrap and completed endpoints 2, 3, 4 match the published step counts.")
    print(f"All included finite verification checks passed ({time.monotonic() - started:.2f}s).")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
