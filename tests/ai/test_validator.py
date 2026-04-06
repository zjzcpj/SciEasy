"""Tests for validator stages 4-5 and validate_generated_type."""

from __future__ import annotations

from scieasy.ai.generation.validator import (
    dry_run_generated_code,
    validate_generated_type,
    validate_port_contracts,
)

# ---------------------------------------------------------------------------
# Stage 4: dry_run_generated_code
# ---------------------------------------------------------------------------


class TestDryRunGeneratedCode:
    """Tests for Stage 4 dry-run validation."""

    def test_valid_code_passes(self) -> None:
        """Valid class definition passes dry run."""
        code = "class MyType:\n    value = 42\n"
        result = dry_run_generated_code(code)
        assert result["passed"] is True
        assert len(result["errors"]) == 0

    def test_syntax_error_caught(self) -> None:
        """Code with syntax error fails dry run."""
        code = "def broken(:\n    pass\n"
        result = dry_run_generated_code(code)
        assert result["passed"] is False
        assert any("syntax" in e.lower() for e in result["errors"])

    def test_import_error_caught(self) -> None:
        """Code with unresolvable import fails dry run."""
        code = "from nonexistent_package_xyz import SomeClass\nclass Foo(SomeClass):\n    pass\n"
        result = dry_run_generated_code(code)
        assert result["passed"] is False
        assert any("import" in e.lower() for e in result["errors"])

    def test_runtime_error_caught(self) -> None:
        """Code that raises at execution time fails dry run."""
        code = "raise ValueError('intentional failure')\nclass MyType:\n    pass\n"
        result = dry_run_generated_code(code)
        assert result["passed"] is False
        assert any("Dry run failed" in e for e in result["errors"])

    def test_no_class_defined_fails(self) -> None:
        """Code that executes but defines no class fails."""
        code = "x = 1\ny = 2\n"
        result = dry_run_generated_code(code)
        assert result["passed"] is False
        assert any("no class" in e.lower() for e in result["errors"])

    def test_result_structure(self) -> None:
        """Dry run result always has passed, errors, warnings."""
        result = dry_run_generated_code("class Foo:\n    pass\n")
        assert "passed" in result
        assert "errors" in result
        assert "warnings" in result
        assert isinstance(result["passed"], bool)
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)


# ---------------------------------------------------------------------------
# Stage 5: validate_port_contracts
# ---------------------------------------------------------------------------


class TestValidatePortContracts:
    """Tests for Stage 5 port contract validation."""

    def test_valid_block_passes(self) -> None:
        """Block with ports and run() method passes."""
        code = (
            "class MyBlock:\n"
            "    input_ports = []\n"
            "    output_ports = []\n"
            "    def run(self, inputs, config):\n"
            "        return {}\n"
        )
        result = validate_port_contracts(code)
        assert result["passed"] is True
        assert len(result["errors"]) == 0

    def test_missing_ports_warns(self) -> None:
        """Block without input_ports/output_ports produces a warning."""
        code = "class MyBlock:\n    def run(self, inputs):\n        return {}\n"
        result = validate_port_contracts(code)
        assert any("input_ports" in w or "output_ports" in w for w in result["warnings"])

    def test_missing_run_fails(self) -> None:
        """Block without run() method fails."""
        code = "class MyBlock:\n    input_ports = []\n    output_ports = []\n    def process(self): pass\n"
        result = validate_port_contracts(code)
        assert result["passed"] is False
        assert any("run()" in e for e in result["errors"])

    def test_run_too_few_params_warns(self) -> None:
        """run() with only self parameter produces a warning."""
        code = "class MyBlock:\n    input_ports = []\n    output_ports = []\n    def run(self):\n        return {}\n"
        result = validate_port_contracts(code)
        assert any("parameter" in w for w in result["warnings"])

    def test_run_no_return_warns(self) -> None:
        """run() without return statement produces a warning."""
        code = "class MyBlock:\n    input_ports = []\n    output_ports = []\n    def run(self, inputs):\n        pass\n"
        result = validate_port_contracts(code)
        assert any("return" in w for w in result["warnings"])

    def test_annotated_ports_detected(self) -> None:
        """Annotated port declarations (ClassVar) are properly detected."""
        code = (
            "from typing import ClassVar\n"
            "class MyBlock:\n"
            "    input_ports: ClassVar[list] = []\n"
            "    output_ports: ClassVar[list] = []\n"
            "    def run(self, inputs, config):\n"
            "        return {}\n"
        )
        result = validate_port_contracts(code)
        assert result["passed"] is True
        # No warnings about missing ports.
        port_warnings = [w for w in result["warnings"] if "input_ports" in w or "output_ports" in w]
        assert len(port_warnings) == 0

    def test_syntax_error_fails(self) -> None:
        """Code with syntax error fails port validation."""
        result = validate_port_contracts("def broken(:\n  pass")
        assert result["passed"] is False
        assert any("Syntax error" in e for e in result["errors"])

    def test_no_class_fails(self) -> None:
        """Code without class definition fails."""
        result = validate_port_contracts("x = 1\n")
        assert result["passed"] is False
        assert any("No class" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# validate_generated_type
# ---------------------------------------------------------------------------


class TestValidateGeneratedType:
    """Tests for type-specific validation pipeline."""

    def test_valid_array_with_axes_passes(self) -> None:
        """Array subclass with axes ClassVar passes all stages."""
        code = (
            "from typing import ClassVar\n"
            "\n"
            "class DataObject:\n"
            "    pass\n"
            "\n"
            "class Array(DataObject):\n"
            "    axes: ClassVar[list[str] | None] = None\n"
            "\n"
            "class RamanImage(Array):\n"
            "    axes: ClassVar[list[str]] = ['y', 'x', 'wavenumber']\n"
        )
        result = validate_generated_type(code)
        assert result["passed"] is True
        assert len(result["errors"]) == 0

    def test_array_missing_axes_warns(self) -> None:
        """Array subclass without axes ClassVar produces a warning."""
        code = (
            "from typing import ClassVar\n"
            "\n"
            "class DataObject:\n"
            "    pass\n"
            "\n"
            "class Array(DataObject):\n"
            "    axes: ClassVar[list[str] | None] = None\n"
            "\n"
            "class BadImage(Array):\n"
            "    pass\n"
        )
        result = validate_generated_type(code)
        # Should still pass (axes is a warning, not an error), but warn.
        assert any("axes" in w.lower() for w in result["warnings"])

    def test_non_dataobject_subclass_rejected(self) -> None:
        """Class not inheriting from a known DataObject base fails."""
        code = "class NotADataObject(list):\n    pass\n"
        result = validate_generated_type(code)
        assert result["passed"] is False
        assert any("DataObject" in e for e in result["errors"])

    def test_valid_series_passes(self) -> None:
        """Series subclass passes validation."""
        code = "class DataObject:\n    pass\nclass Series(DataObject):\n    pass\nclass IRSpectrum(Series):\n    pass\n"
        result = validate_generated_type(code)
        assert result["passed"] is True

    def test_valid_dataframe_passes(self) -> None:
        """DataFrame subclass passes validation."""
        code = (
            "class DataObject:\n"
            "    pass\n"
            "class DataFrame(DataObject):\n"
            "    pass\n"
            "class PeakAnnotations(DataFrame):\n"
            "    pass\n"
        )
        result = validate_generated_type(code)
        assert result["passed"] is True

    def test_syntax_error_fails(self) -> None:
        """Code with syntax error fails validation."""
        result = validate_generated_type("def broken(:\n  pass")
        assert result["passed"] is False
        assert any("Syntax error" in e for e in result["errors"])

    def test_no_class_fails(self) -> None:
        """Code without class definition fails."""
        result = validate_generated_type("x = 1\ny = 2\n")
        assert result["passed"] is False
        assert any("No class" in e for e in result["errors"])

    def test_result_structure(self) -> None:
        """Validation report always has passed, errors, warnings keys."""
        result = validate_generated_type("x = 1\n")
        assert "passed" in result
        assert "errors" in result
        assert "warnings" in result

    def test_image_subclass_needs_axes(self) -> None:
        """Image (Array-family) subclass without axes generates warning."""
        code = (
            "class DataObject:\n"
            "    pass\n"
            "class Array(DataObject):\n"
            "    pass\n"
            "class Image(Array):\n"
            "    pass\n"
            "class MyImage(Image):\n"
            "    pass\n"
        )
        result = validate_generated_type(code)
        # MyImage inherits from Image (Array-family), should warn about axes.
        assert any("axes" in w.lower() for w in result["warnings"])

    def test_direct_dataobject_inheritance_passes(self) -> None:
        """Direct DataObject subclass passes inheritance check."""
        code = "class DataObject:\n    pass\nclass CustomType(DataObject):\n    pass\n"
        result = validate_generated_type(code)
        assert result["passed"] is True
