"""Tests for AI generation templates and validator."""

from __future__ import annotations

from scieasy.ai.generation.templates import BLOCK_TEMPLATES, TYPE_TEMPLATES
from scieasy.ai.generation.validator import validate_generated_code


class TestBlockTemplates:
    """Verify BLOCK_TEMPLATES content and constraints."""

    def test_all_categories_present(self) -> None:
        """BLOCK_TEMPLATES has entries for all five block categories."""
        expected = {"process", "io", "code", "app", "ai"}
        assert set(BLOCK_TEMPLATES.keys()) == expected

    def test_templates_reference_collection(self) -> None:
        """All templates mention Collection."""
        for category, template in BLOCK_TEMPLATES.items():
            assert "Collection" in template, f"{category} template missing Collection reference"

    def test_templates_prohibit_dict_str_any(self) -> None:
        """Templates instruct not to use dict[str, Any] for port data."""
        for category, template in BLOCK_TEMPLATES.items():
            assert "dict[str, Any]" in template, f"{category} template should warn against dict[str, Any]"

    def test_templates_warn_against_transitions(self) -> None:
        """Templates instruct not to call self.transition()."""
        for category, template in BLOCK_TEMPLATES.items():
            assert "transition" in template.lower(), f"{category} template doesn't mention transition constraint"

    def test_templates_warn_against_estimated_memory(self) -> None:
        """Templates instruct not to use estimated_memory_gb."""
        for category, template in BLOCK_TEMPLATES.items():
            assert "estimated_memory_gb" in template, (
                f"{category} template doesn't mention estimated_memory_gb constraint"
            )

    def test_templates_are_nonempty_strings(self) -> None:
        """Each template is a non-empty string."""
        for category, template in BLOCK_TEMPLATES.items():
            assert isinstance(template, str)
            assert len(template) > 50, f"{category} template is suspiciously short"


class TestTypeTemplates:
    """Verify TYPE_TEMPLATES content and constraints."""

    def test_core_families_present(self) -> None:
        """TYPE_TEMPLATES has entries for core type families."""
        expected = {"array", "series", "dataframe"}
        assert set(TYPE_TEMPLATES.keys()) == expected

    def test_templates_reference_collection(self) -> None:
        """Type templates mention Collection usage."""
        for family, template in TYPE_TEMPLATES.items():
            assert "Collection" in template, f"{family} template missing Collection reference"

    def test_templates_are_nonempty_strings(self) -> None:
        """Each template is a non-empty string."""
        for family, template in TYPE_TEMPLATES.items():
            assert isinstance(template, str)
            assert len(template) > 20, f"{family} template is suspiciously short"


class TestValidator:
    """Verify validate_generated_code() validation pipeline."""

    def test_valid_process_block_passes(self) -> None:
        """A minimal valid ProcessBlock passes validation."""
        code = (
            "from scieasy.blocks.process.process_block import ProcessBlock\n"
            "from scieasy.core.types.collection import Collection\n"
            "from scieasy.blocks.base.config import BlockConfig\n"
            "\n"
            "class MyBlock(ProcessBlock):\n"
            "    def run(self, inputs: dict[str, Collection],\n"
            "            config: BlockConfig) -> dict[str, Collection]:\n"
            "        return {}\n"
        )
        result = validate_generated_code(code)
        assert result["passed"] is True
        assert len(result["errors"]) == 0

    def test_syntax_error_fails(self) -> None:
        """Code with syntax errors fails validation."""
        result = validate_generated_code("def foo(:\n  pass")
        assert result["passed"] is False
        assert any("Syntax error" in e for e in result["errors"])

    def test_no_class_fails(self) -> None:
        """Code without a class definition fails."""
        result = validate_generated_code("x = 1\ny = 2\n")
        assert result["passed"] is False
        assert any("No class" in e for e in result["errors"])

    def test_no_run_method_fails(self) -> None:
        """Code with class but no run() method fails."""
        code = "class MyBlock:\n    def process(self): pass\n"
        result = validate_generated_code(code)
        assert result["passed"] is False
        assert any("run()" in e for e in result["errors"])

    def test_estimated_memory_gb_fails(self) -> None:
        """Code referencing estimated_memory_gb is rejected."""
        code = "class MyBlock:\n    def run(self):\n        req = ResourceRequest(estimated_memory_gb=4.0)\n"
        result = validate_generated_code(code)
        assert result["passed"] is False
        assert any("estimated_memory_gb" in e for e in result["errors"])

    def test_dict_str_any_warns(self) -> None:
        """Code using dict[str, Any] generates a warning."""
        code = "class MyBlock:\n    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:\n        return {}\n"
        result = validate_generated_code(code)
        assert any("dict[str, Any]" in w for w in result["warnings"])

    def test_state_transition_warns(self) -> None:
        """Code calling self.transition() generates a warning."""
        code = "class MyBlock:\n    def run(self):\n        self.transition(BlockState.RUNNING)\n        return {}\n"
        result = validate_generated_code(code)
        assert any("transition" in w for w in result["warnings"])

    def test_paused_transition_no_warning(self) -> None:
        """AppBlock PAUSED transition does not generate a warning."""
        code = "class MyAppBlock:\n    def run(self):\n        self.transition(BlockState.PAUSED)\n        return {}\n"
        result = validate_generated_code(code)
        # PAUSED transitions should not generate warnings.
        transition_warnings = [w for w in result["warnings"] if "transition" in w]
        assert len(transition_warnings) == 0

    def test_result_structure(self) -> None:
        """Validation report always has passed, errors, warnings keys."""
        result = validate_generated_code("x = 1\n")
        assert "passed" in result
        assert "errors" in result
        assert "warnings" in result
        assert isinstance(result["passed"], bool)
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)

    def test_valid_code_no_warnings(self) -> None:
        """Clean code produces no errors and no warnings."""
        code = (
            "class CleanBlock:\n"
            "    def run(self, inputs: dict[str, 'Collection'],\n"
            "            config: 'BlockConfig') -> dict[str, 'Collection']:\n"
            "        return {}\n"
        )
        result = validate_generated_code(code)
        assert result["passed"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
