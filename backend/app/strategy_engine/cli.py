import argparse
import json
import sys

from .evaluator import evaluate_strategy
from .fixtures import FIXTURES
from .review import render_strategy_brief_markdown


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Offline Proposal Strategy Engine evaluator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixture", choices=sorted(FIXTURES.keys()))
    group.add_argument("--review", choices=sorted(FIXTURES.keys()))
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()
    fixture_name = args.fixture or args.review
    brief = evaluate_strategy(FIXTURES[fixture_name])
    if args.review:
        print(render_strategy_brief_markdown(brief))
    else:
        print(json.dumps(brief.dict(), ensure_ascii=False, indent=args.indent, sort_keys=True))


if __name__ == "__main__":
    main()
