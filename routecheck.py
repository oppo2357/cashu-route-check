"""Check a wallet's required payment routes against saved Cashu mint metadata."""
import argparse
import json
from pathlib import Path
import sys


def unique_fields(pairs):
    obj = {}
    for name, value in pairs:
        if name in obj:
            raise ValueError(f"duplicate JSON field {name!r}")
        obj[name] = value
    return obj


def integer(value):
    return type(value) is int and value >= 0


def verdict(info, route):
    operation = {"mint": "4", "melt": "5"}[route["operation"]]
    method, unit, amount = (route[key] for key in ("method", "unit", "amount"))
    if not all(isinstance(s, str) and s for s in (method, unit)) or not integer(amount) or amount == 0:
        raise ValueError("A route needs a method, unit and positive integer amount")
    nuts = info.get("nuts")
    section = nuts.get(operation) if isinstance(nuts, dict) else None
    if not isinstance(section, dict) or type(section.get("disabled")) is not bool:
        return "unknown", "missing operation metadata or disabled flag"
    if section["disabled"]:
        return "blocked", "operation disabled"
    methods = section.get("methods")
    if not isinstance(methods, list):
        return "unknown", "missing methods list"
    for item in methods:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k] for k in ("method","unit")):
            return "unknown", "malformed method declaration"
    rows = [r for r in methods if (r["method"], r["unit"]) == (method, unit)]
    if not rows:
        return "blocked", "method/unit pair absent"
    if len(rows) != 1:
        return "unknown", "multiple declarations for one pair"
    low, high = rows[0].get("min_amount"), rows[0].get("max_amount")
    if any(v is not None and not integer(v) for v in (low, high)):
        return "unknown", "invalid amount limit"
    if low is not None and high is not None and low > high:
        return "unknown", "inverted limits"
    if low is not None and amount < low:
        return "blocked", f"below minimum {low}"
    if high is not None and amount > high:
        return "blocked", f"above maximum {high}"
    return "advertised", "within published limits"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routes", type=Path)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--before", type=Path, help="Earlier /v1/info JSON for comparison")
    args = parser.parse_args()
    def load(path):
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_fields)
    try:
        routes, current = load(args.routes), load(args.snapshot)
        before = load(args.before) if args.before else None
        if not isinstance(routes, list) or not routes or not isinstance(current, dict) or (args.before and not isinstance(before, dict)):
            raise ValueError("Expected a nonempty route array and snapshot objects")
        results = []
        for route in routes:
            state, reason = verdict(current, route)
            row = {k: route[k] for k in ("operation", "method", "unit", "amount")}
            row.update(status=state, reason=reason)
            if before is not None:
                row["previous"] = verdict(before, route)[0]
            results.append(row)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Invalid input: {error}\n")
    print(json.dumps(results, indent=2))
    return int(any(r["status"] != "advertised" for r in results))


if __name__ == "__main__":
    sys.exit(main())
