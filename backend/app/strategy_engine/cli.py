import argparse
import json

from .evaluator import evaluate_strategy
from .fixtures import FIXTURES


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Proposal Strategy Engine evaluator")
    parser.add_argument("--fixture", choices=sorted(FIXTURES.keys()), required=True)
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()
    brief = evaluate_strategy(FIXTURES[args.fixture])
    print(json.dumps(brief.dict(), ensure_ascii=False, indent=args.indent, sort_keys=True))


if __name__ == "__main__":
    main()
