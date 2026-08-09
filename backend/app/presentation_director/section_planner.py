"""Section planning rules."""

from __future__ import annotations

from .models import DecisionStage, SectionPlanItem


def plan_sections(stage: DecisionStage) -> tuple[SectionPlanItem, ...]:
    if stage == "poc_proposal":
        return (
            SectionPlanItem("sec-01", "Opening", "30分で合意したい論点を最初に揃える", ("slide-01", "slide-02")),
            SectionPlanItem("sec-02", "Problem Agreement", "判断ばらつきの原因と影響に合意する", ("slide-03", "slide-04")),
            SectionPlanItem("sec-03", "PoC Design", "PoCで何を検証するかを具体化する", ("slide-05", "slide-06", "slide-07", "slide-08")),
            SectionPlanItem("sec-04", "Decision Material", "効果・期間・リスク・体制を意思決定材料に変える", ("slide-09", "slide-10", "slide-11", "slide-12", "slide-13")),
            SectionPlanItem("sec-05", "Appendix", "本編を邪魔しない詳細根拠を保持する", ("slide-14", "slide-15"), include_section_divider=False),
        )
    return (
        SectionPlanItem("sec-01", "Opening", "提案の目的と結論を示す", ("slide-01", "slide-02")),
        SectionPlanItem("sec-02", "Current Issue", "課題と原因を整理する", ("slide-03", "slide-04")),
        SectionPlanItem("sec-03", "Recommendation", "提案内容と実行方法を説明する", ("slide-05", "slide-06", "slide-07", "slide-08")),
        SectionPlanItem("sec-04", "Decision", "効果・リスク・次アクションを合意する", ("slide-09", "slide-10", "slide-11", "slide-12")),
    )
