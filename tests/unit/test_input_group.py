"""Unit tests for SciProInputGroup — prefix input group component."""

from __future__ import annotations

from types import SimpleNamespace

from src.components.atomic.input_group import (
    _INPUT_CLASSES,
    _PREFIX_SPAN,
    SciProInputGroup,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    """_PREFIX_SPAN and _INPUT_CLASSES contain expected Tailwind classes."""

    def test_prefix_span_is_list(self) -> None:
        """_PREFIX_SPAN is a list of class strings."""
        assert isinstance(_PREFIX_SPAN, list)
        assert len(_PREFIX_SPAN) > 0

    def test_prefix_span_contains_key_classes(self) -> None:
        """_PREFIX_SPAN contains structural and visual Tailwind classes."""
        assert "inline-flex" in _PREFIX_SPAN
        assert "items-center" in _PREFIX_SPAN
        assert "rounded-l-md" in _PREFIX_SPAN
        assert "border" in _PREFIX_SPAN
        assert "bg-muted" in _PREFIX_SPAN
        assert "px-3" in _PREFIX_SPAN
        assert "tabular-nums" in _PREFIX_SPAN

    def test_input_classes_is_list(self) -> None:
        """_INPUT_CLASSES is a list of class strings."""
        assert isinstance(_INPUT_CLASSES, list)
        assert len(_INPUT_CLASSES) > 0

    def test_input_classes_contains_key_classes(self) -> None:
        """_INPUT_CLASSES contains structural and visual Tailwind classes."""
        assert "flex" in _INPUT_CLASSES
        assert "h-10" in _INPUT_CLASSES
        assert "w-full" in _INPUT_CLASSES
        assert "rounded-r-md" in _INPUT_CLASSES
        assert "rounded-l-none" in _INPUT_CLASSES
        assert "border" in _INPUT_CLASSES
        assert "bg-background" in _INPUT_CLASSES
        assert "focus-visible:outline-none" in _INPUT_CLASSES


# ---------------------------------------------------------------------------
# Component class attributes
# ---------------------------------------------------------------------------


class TestComponentRegistration:
    """SciProInputGroup registers correctly with PuePy."""

    def test_component_name(self) -> None:
        """component_name is 'sci-pro-input-group' so t.sci_pro_input_group() works."""
        assert SciProInputGroup.component_name == "sci-pro-input-group"

    def test_enclosing_tag(self) -> None:
        """enclosing_tag is 'div'."""
        assert SciProInputGroup.enclosing_tag == "div"


class TestComponentProps:
    """Props are defined with correct names and default values."""

    def test_props_defined(self) -> None:
        """Props list includes label, prefix, placeholder, error, helper_text."""
        prop_names = {p.name for p in SciProInputGroup.props}
        expected = {"label", "prefix", "placeholder", "error", "helper_text"}
        assert prop_names == expected

    def test_prefix_default_is_empty_string(self) -> None:
        """prefix prop defaults to empty string."""
        prop = next(p for p in SciProInputGroup.props if p.name == "prefix")
        assert prop.default_value == ""

    def test_placeholder_default_is_empty_string(self) -> None:
        """placeholder prop defaults to empty string."""
        prop = next(p for p in SciProInputGroup.props if p.name == "placeholder")
        assert prop.default_value == ""

    def test_error_default_is_empty_string(self) -> None:
        """error prop defaults to empty string."""
        prop = next(p for p in SciProInputGroup.props if p.name == "error")
        assert prop.default_value == ""

    def test_helper_text_default_is_empty_string(self) -> None:
        """helper_text prop defaults to empty string."""
        prop = next(p for p in SciProInputGroup.props if p.name == "helper_text")
        assert prop.default_value == ""

    def test_label_default_is_empty_string(self) -> None:
        """label prop defaults to empty string."""
        prop = next(p for p in SciProInputGroup.props if p.name == "label")
        assert prop.default_value == ""

    def test_prefix_prop_is_string_type(self) -> None:
        """prefix prop is typed as str."""
        prop = next(p for p in SciProInputGroup.props if p.name == "prefix")
        assert prop.type is str

    def test_prop_count(self) -> None:
        """There are exactly 5 props defined (bind is a pseudo-prop)."""
        assert len(SciProInputGroup.props) == 5


# ---------------------------------------------------------------------------
# _handle_bind — bind kwarg interception
# ---------------------------------------------------------------------------


class TestHandleBind:
    """_handle_bind removes 'bind' from kwargs and clears self.bind."""

    def test_removes_bind_from_kwargs(self) -> None:
        """The 'bind' key is removed from the kwargs dict."""
        instance = SciProInputGroup.__new__(SciProInputGroup)
        instance.bind = "student_id"
        kwargs = {"bind": "student_id", "class_name": "test"}
        instance._handle_bind(kwargs)
        assert "bind" not in kwargs

    def test_sets_self_bind_to_none(self) -> None:
        """self.bind is set to None after _handle_bind."""
        instance = SciProInputGroup.__new__(SciProInputGroup)
        instance.bind = "student_id"
        kwargs = {"bind": "student_id"}
        instance._handle_bind(kwargs)
        assert instance.bind is None

    def test_preserves_other_kwargs(self) -> None:
        """Non-bind kwargs are preserved."""
        instance = SciProInputGroup.__new__(SciProInputGroup)
        instance.bind = "student_id"
        kwargs = {"bind": "student_id", "placeholder": "Enter ID", "class_name": "x"}
        instance._handle_bind(kwargs)
        assert kwargs == {"placeholder": "Enter ID", "class_name": "x"}

    def test_handles_missing_bind_key(self) -> None:
        """No error when 'bind' is not in kwargs."""
        instance = SciProInputGroup.__new__(SciProInputGroup)
        instance.bind = ""
        kwargs = {"placeholder": "test"}
        instance._handle_bind(kwargs)
        assert instance.bind is None


# ---------------------------------------------------------------------------
# _on_input — value sync with prefix stripping
# ---------------------------------------------------------------------------


class FakeEvent:
    """Minimal event stub with a target.value attribute."""

    def __init__(self, value: str) -> None:
        self.target = SimpleNamespace(value=value)


class TestOnInput:
    """_on_input stores values in application state with prefix stripping."""

    @staticmethod
    def _make_instance(bind_key: str, prefix: str) -> SciProInputGroup:
        """Build a SciProInputGroup with minimal mocked dependencies.

        The ``application`` property on ``Tag`` requires ``_page._application``,
        so we wire up a stubbed page object instead of setting the property
        directly.
        """
        instance = SciProInputGroup.__new__(SciProInputGroup)
        instance._bind_key = bind_key
        instance.props_values = {"prefix": prefix}
        mock_app = SimpleNamespace(state={})
        instance._page = SimpleNamespace(_application=mock_app)
        return instance

    def test_stores_value_when_no_prefix(self) -> None:
        """Value is stored as-is when there is no prefix."""
        instance = self._make_instance(bind_key="student_id", prefix="")
        instance._on_input(FakeEvent("12345"))
        assert instance.application.state["student_id"] == "12345"

    def test_strips_prefix_when_present(self) -> None:
        """Prefix is stripped from the value before storage."""
        instance = self._make_instance(bind_key="student_id", prefix="2026SS_")
        instance._on_input(FakeEvent("2026SS_12345"))
        assert instance.application.state["student_id"] == "12345"

    def test_stores_plain_value_when_no_prefix_match(self) -> None:
        """Value is stored as-is when prefix does not match."""
        instance = self._make_instance(bind_key="student_id", prefix="2026SS_")
        instance._on_input(FakeEvent("12345"))
        assert instance.application.state["student_id"] == "12345"

    def test_does_nothing_when_no_bind_key(self) -> None:
        """No state mutation occurs when _bind_key is empty."""
        instance = self._make_instance(bind_key="", prefix="2026SS_")
        instance._on_input(FakeEvent("2026SS_12345"))
        assert instance.application.state == {}

    def test_handles_empty_value_with_prefix(self) -> None:
        """Empty string is stored when value equals prefix only."""
        instance = self._make_instance(bind_key="student_id", prefix="2026SS_")
        instance._on_input(FakeEvent("2026SS_"))
        assert instance.application.state["student_id"] == ""

    def test_handles_empty_value_no_prefix(self) -> None:
        """Empty string is stored when value is empty and there is no prefix."""
        instance = self._make_instance(bind_key="student_id", prefix="")
        instance._on_input(FakeEvent(""))
        assert instance.application.state["student_id"] == ""

    def test_partial_prefix_does_not_strip(self) -> None:
        """Only exact full prefix at start is stripped, not partial match."""
        instance = self._make_instance(bind_key="student_id", prefix="2026SS_")
        instance._on_input(FakeEvent("2026_12345"))
        assert instance.application.state["student_id"] == "2026_12345"

    def test_strips_prefix_after_previous_strip(self) -> None:
        """Prefix is stripped even if value was previously stripped."""
        instance = self._make_instance(bind_key="student_id", prefix="2026SS_")
        instance._on_input(FakeEvent("2026SS_12345"))
        assert instance.application.state["student_id"] == "12345"
        instance._on_input(FakeEvent("2026SS_99999"))
        assert instance.application.state["student_id"] == "99999"
