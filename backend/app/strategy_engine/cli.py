import argparse
import json
import sys

from .benchmark import evaluation_report_csv, evaluation_report_json, render_evaluation_report_markdown, run_benchmark
from .benchmark_dataset import benchmark_category_choices
from .comparison import comparison_fixture_choices, comparison_report_json, compare_fixture, render_comparison_report_markdown
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
    group.add_argument("--benchmark", action="store_true")
    group.add_argument("--compare", choices=comparison_fixture_choices())
    parser.add_argument("--category", choices=benchmark_category_choices())
    parser.add_argument("--format", choices=["json", "markdown", "csv"], default="markdown")
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()
    if args.category and not args.benchmark:
        parser.error("--category can only be used with --benchmark")
    if args.compare:
        if args.format == "csv":
            parser.error("--compare supports json or markdown output")
        report = compare_fixture(args.compare)
        if args.format == "json":
            print(comparison_report_json(report, indent=args.indent))
        else:
            print(render_comparison_report_markdown(report))
        return
    if args.benchmark:
        report = run_benchmark(args.category)
        if args.format == "json":
            print(evaluation_report_json(report, indent=args.indent))
        elif args.format == "csv":
            print(evaluation_report_csv(report), end="")
        else:
            print(render_evaluation_report_markdown(report))
        return
    if args.evaluate:
        if args.format == "csv":
            parser.error("--evaluate supports json or markdown output")
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
    if args.format == "csv":
        parser.error("--fixture and --review support json or markdown output")
    brief = evaluate_strategy(FIXTURES[fixture_name])
    if args.review:
        print(render_strategy_brief_markdown(brief))
    else:
        print(json.dumps(brief.dict(), ensure_ascii=False, indent=args.indent, sort_keys=True))


if __name__ == "__main__":
    main()
