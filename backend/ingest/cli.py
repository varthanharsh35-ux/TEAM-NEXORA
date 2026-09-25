"""Command-line interface for the data ingestion and crawling pipeline."""

import importlib
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LOG_PATH = DATA_DIR / "ingest_log.json"


def status() -> list[dict]:
    """Read ingest log and print dataset freshness status table."""
    records = []
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data if isinstance(data, list) else data.get("datasets", [])
        except Exception:
            records = []

    print(f"{'Dataset':<25} | {'Last_fetched':<15} | {'Next_check':<15} | {'Status':<10}")
    print("-" * 72)
    for r in records:
        name = r.get("dataset", "unknown")
        last_f = r.get("last_fetched", "never")
        next_c = r.get("next_check", "pending")
        st = r.get("status", "unknown")
        print(f"{name:<25} | {last_f:<15} | {next_c:<15} | {st:<10}")

    return records


def run_parser(parser_name: str) -> dict:
    """Dynamically import and run a specific dataset parser."""
    module_name = f"backend.ingest.parsers.{parser_name}"
    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError:
        # Fallback to local import if called from backend directory
        try:
            mod = importlib.import_module(f"ingest.parsers.{parser_name}")
        except ModuleNotFoundError:
            raise ValueError(f"unknown_parser: {parser_name}")

    if hasattr(mod, "run"):
        return mod.run()

    # Find Parser class inside module if run() is not at top level
    for attr in dir(mod):
        if attr.lower().endswith("parser") and attr.lower() != "parser":
            cls = getattr(mod, attr)
            if hasattr(cls, "run"):
                return cls().run()

    raise ValueError(f"no_run_method_found: {parser_name}")


def main(argv=None):
    args = argv or sys.argv[1:]
    if not args:
        print("Usage: python -m backend.ingest status | run <parser>")
        return 1

    cmd = args[0].lower()
    if cmd == "status":
        status()
        return 0
    elif cmd == "run":
        if len(args) < 2:
            print("Error: parser name required: python -m backend.ingest run <name>")
            return 1
        parser = args[1].lower()
        res = run_parser(parser)
        print(f"Parser '{parser}' finished: {res}")
        return 0
    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(main())

    # Self-tests
    # 1. status() returns list even if log missing
    res_st = status()
    assert isinstance(res_st, list)

    # 2. Unknown parser raises ValueError
    try:
        run_parser("non_existent_parser")
        assert False, "Should raise ValueError for missing parser"
    except ValueError as e:
        assert "unknown_parser" in str(e)

    # 3. Main with no args prints usage and returns 1
    assert main([]) == 1

    # 4. Main with status returns 0
    assert main(["status"]) == 0

    # 5. Main with unknown command returns 1
    assert main(["invalid_command"]) == 1

    print("All 5+ ingest CLI tests passed successfully!")
