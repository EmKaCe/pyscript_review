"""Smoke test: Pydantic in local (non-Pyodide) environment.

Validates that Pydantic v2 works correctly for serialization/deserialization,
validation, and integration with PyYAML. This is the critical gating test
for the architecture decision of Pydantic vs pure dataclasses.

If Pydantic v2's compiled Rust extension (pydantic-core) fails to import,
we document the fallback to pure dataclasses with manual validation.
"""

import pydantic
import pytest
import yaml
from pydantic import BaseModel, Field, ValidationError


class SampleModel(BaseModel):
    """A minimal Pydantic model for smoke testing."""

    name: str = Field(description="The name of the entity")
    value: int = Field(description="A numeric value", ge=0, le=100)
    tags: list[str] = Field(description="Tag list", default_factory=list)
    active: bool = Field(description="Whether this is active", default=True)


class ConfigModel(BaseModel):
    """Pydantic model for YAML integration testing."""

    version: str = Field(description="Config version string")
    max_items: int = Field(description="Maximum number of items", gt=0)
    enabled_features: list[str] = Field(default_factory=list)


def test_pydantic_import():
    """Import pydantic, verify the pydantic-core backend is present."""
    assert pydantic.__version__
    # Verify pydantic-core is importable (may fail in Pyodide due to Rust extension)
    try:
        import pydantic_core

        assert pydantic_core.__version__
    except ImportError:
        # In Pyodide, this is expected to fail
        pytest.fail(
            "pydantic-core failed to import — Pydantic v2 cannot work. "
            "Fall back to pure dataclasses with manual validation."
        )


def test_pydantic_basic_model():
    """Define a BaseModel with Field(description=...), instantiate, serialize, deserialize."""
    obj = SampleModel(name="test-item", value=42, tags=["a", "b"])
    assert obj.name == "test-item"
    assert obj.value == 42
    assert obj.tags == ["a", "b"]
    assert obj.active is True

    # Serialize
    data = obj.model_dump()
    assert data == {"name": "test-item", "value": 42, "tags": ["a", "b"], "active": True}

    # Serialize as JSON
    json_str = obj.model_dump_json()
    assert '"name"' in json_str
    assert '"value"' in json_str

    # Deserialize
    obj2 = SampleModel.model_validate(data)
    assert obj2 == obj


def test_pydantic_defaults():
    """Test that default values work correctly."""
    obj = SampleModel(name="minimal", value=50)
    assert obj.tags == []
    assert obj.active is True


def test_pydantic_validation():
    """Create a model with required fields, test that missing fields raise ValidationError."""
    with pytest.raises(ValidationError):
        SampleModel.model_validate({})  # missing name and value

    with pytest.raises(ValidationError):
        SampleModel.model_validate({"name": "bad-value"})  # missing value

    # Test field constraints
    with pytest.raises(ValidationError):
        SampleModel(name="bad-range", value=999)  # value > 100


def test_pydantic_yaml_integration():
    """Create a Pydantic model, load YAML string, validate with model_validate."""
    yaml_str = """
version: "1.0"
max_items: 50
enabled_features:
  - dark_mode
  - undo_redo
  - export
"""

    raw = yaml.safe_load(yaml_str)
    assert raw["version"] == "1.0"
    assert raw["max_items"] == 50

    config = ConfigModel.model_validate(raw)
    assert config.version == "1.0"
    assert config.max_items == 50
    assert config.enabled_features == ["dark_mode", "undo_redo", "export"]


def test_pydantic_json_schema():
    """Verify that Pydantic can generate JSON schema."""
    schema = SampleModel.model_json_schema()
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "value" in schema["properties"]
    # Field descriptions must be present per AGENTS.md convention
    assert schema["properties"]["name"]["description"] == "The name of the entity"
    assert schema["properties"]["value"]["description"] == "A numeric value"


def test_pydantic_version_info():
    """Print Pydantic version details for documentation."""
    print(f"\nPydantic version: {pydantic.__version__}")
    try:
        import pydantic_core

        print(f"pydantic-core version: {pydantic_core.__version__}")
    except ImportError:
        print("pydantic-core: NOT AVAILABLE (expected in Pyodide)")
