from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from app.prompts.services import (
    build_prompt_experiment_analytics,
    create_experiment_from_learning,
    get_prompt_studio_dashboard,
)
from app.prompts.version_manager import PromptVersionManager

_legacy_prompt_path = Path(__file__).resolve().parent.parent / "proposal_prompts.py"
_legacy_spec = spec_from_file_location("_legacy_proposal_prompts", _legacy_prompt_path)
if _legacy_spec and _legacy_spec.loader:
    _legacy_module = module_from_spec(_legacy_spec)
    _legacy_spec.loader.exec_module(_legacy_module)
    BASIC_PROPOSAL_STRUCTURE = _legacy_module.BASIC_PROPOSAL_STRUCTURE
    SYSTEM_PROMPT = _legacy_module.SYSTEM_PROMPT
    build_user_prompt = _legacy_module.build_user_prompt
else:
    BASIC_PROPOSAL_STRUCTURE = []
    SYSTEM_PROMPT = ""

    def build_user_prompt(payload):  # type: ignore[no-untyped-def]
        return str(payload)

__all__ = [
    "BASIC_PROPOSAL_STRUCTURE",
    "PromptVersionManager",
    "SYSTEM_PROMPT",
    "build_prompt_experiment_analytics",
    "build_user_prompt",
    "create_experiment_from_learning",
    "get_prompt_studio_dashboard",
]
