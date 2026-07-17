import argparse
import json
import sys

from .evaluator import evaluate_strategy
from .fixtures import FIXTURES
from .quality import evaluate_proposal_quality, quality_report_json, render_quality_report_markdown
from .quality_fixtures import build_quality_evaluation_input, quality_fixture_choices
from .review import render_strategy_brief_markdown


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Offline Proposal Strategy Engine evaluator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixture", choices=sorted(FIXTURES.keys()))
    group.add_argument("--review", choices=sorted(FIXTURES.keys()))
    group.add_argument("--evaluate", choices=quality_fixture_choices())
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()
    if args.evaluate:
        quality_input = build_quality_evaluation_input(args.evaluate)
        report = evaluate_proposal_quality(
            quality_input.strategy_brief,
            quality_input.human_review_report,
            quality_input.presentation_context,
        )
        if args.format == "json":
            print(quality_report_json(report, indent=args.indent))
        else:
            print(render_quality_report_markdown(report))
        return

    fixture_name = args.fixture or args.review
    brief = evaluate_strategy(FIXTURES[fixture_name])
    if args.review:
        print(render_strategy_brief_markdown(brief))
    else:
        print(json.dumps(brief.dict(), ensure_ascii=False, indent=args.indent, sort_keys=True))


if __name__ == "__main__":
    main()
