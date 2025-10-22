"""Tests for Dilemma models."""

import sys
from pathlib import Path

# Add src to path for tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from dilemmas.models.dilemma import Dilemma, DilemmaChoice, ToolSchema


class TestToolSchema:
    """Tests for ToolSchema model."""

    def test_basic_creation(self):
        """Test basic ToolSchema creation."""
        tool = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters["type"] == "object"

    def test_empty_parameters(self):
        """Test ToolSchema with empty parameters."""
        tool = ToolSchema(name="simple_tool", description="Simple")
        assert tool.parameters == {}


class TestDilemmaChoice:
    """Tests for DilemmaChoice model."""

    def test_basic_creation(self):
        """Test basic DilemmaChoice creation."""
        choice = DilemmaChoice(
            id="test",
            label="Test Choice",
            description="A test choice",
        )
        assert choice.id == "test"
        assert choice.label == "Test Choice"
        assert choice.tool_name is None

    def test_with_tool(self):
        """Test DilemmaChoice with tool mapping."""
        choice = DilemmaChoice(
            id="action",
            label="Take Action",
            description="Do something",
            tool_name="do_something",
        )
        assert choice.tool_name == "do_something"


class TestDilemma:
    """Tests for Dilemma model."""

    @pytest.fixture
    def simple_dilemma(self):
        """Create a simple test dilemma."""
        return Dilemma(
            title="Test Dilemma",
            situation_template="A {SUBJECT} did {ACTION}.",
            question="What should happen?",
            choices=[
                DilemmaChoice(id="a", label="Option A", description="First option"),
                DilemmaChoice(id="b", label="Option B", description="Second option"),
            ],
            variables={
                "{SUBJECT}": ["person", "robot"],
                "{ACTION}": ["something good", "something bad"],
            },
            tags=["test"],
            action_context="You are a test AI.",
            difficulty_intended=5,
            created_by="human",
        )

    def test_basic_creation(self, simple_dilemma):
        """Test basic Dilemma creation."""
        assert simple_dilemma.id  # UUID auto-generated
        assert len(simple_dilemma.id) == 36  # UUID4 format
        assert simple_dilemma.title == "Test Dilemma"
        assert simple_dilemma.version == 1
        assert simple_dilemma.difficulty_intended == 5
        assert len(simple_dilemma.choices) == 2

    def test_requires_at_least_two_choices(self):
        """Test that at least 2 choices are required."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Dilemma(
                title="Bad",
                situation_template="Test",
                question="What?",
                choices=[DilemmaChoice(id="a", label="Only one", description="Oops")],
                action_context="Test",
                difficulty_intended=5,
                created_by="human",
            )

    def test_difficulty_bounds(self):
        """Test difficulty must be 1-10."""
        # Valid difficulties
        for diff in [1, 5, 10]:
            d = Dilemma(
                title="Test",
                situation_template="Test",
                question="What?",
                choices=[
                    DilemmaChoice(id="a", label="A", description="A"),
                    DilemmaChoice(id="b", label="B", description="B"),
                ],
                action_context="Test",
                difficulty_intended=diff,
                created_by="human",
            )
            assert d.difficulty_intended == diff

        # Invalid difficulties
        with pytest.raises(Exception):
            Dilemma(
                title="Bad",
                situation_template="Test",
                question="What?",
                choices=[
                    DilemmaChoice(id="a", label="A", description="A"),
                    DilemmaChoice(id="b", label="B", description="B"),
                ],
                action_context="Test",
                difficulty_intended=0,
                created_by="human",
            )

        with pytest.raises(Exception):
            Dilemma(
                title="Bad",
                situation_template="Test",
                question="What?",
                choices=[
                    DilemmaChoice(id="a", label="A", description="A"),
                    DilemmaChoice(id="b", label="B", description="B"),
                ],
                action_context="Test",
                difficulty_intended=11,
                created_by="human",
            )

    def test_render_default(self, simple_dilemma):
        """Test rendering with default values (first from each variable list)."""
        rendered = simple_dilemma.render()
        assert "person" in rendered
        assert "something good" in rendered
        assert rendered == "A person did something good."

    def test_render_with_substitutions(self, simple_dilemma):
        """Test rendering with specific variable values."""
        rendered = simple_dilemma.render(
            variable_values={"{SUBJECT}": "robot", "{ACTION}": "something bad"}
        )
        assert rendered == "A robot did something bad."

    def test_render_with_modifiers(self):
        """Test rendering with modifiers."""
        dilemma = Dilemma(
            title="Test",
            situation_template="Base situation.",
            question="What?",
            choices=[
                DilemmaChoice(id="a", label="A", description="A"),
                DilemmaChoice(id="b", label="B", description="B"),
            ],
            modifiers=["Modifier 1.", "Modifier 2.", "Modifier 3."],
            action_context="Test",
            difficulty_intended=5,
            created_by="human",
        )

        # No modifiers
        assert dilemma.render() == "Base situation."

        # One modifier
        rendered = dilemma.render(include_modifiers=[0])
        assert rendered == "Base situation. Modifier 1."

        # Multiple modifiers
        rendered = dilemma.render(include_modifiers=[0, 2])
        assert rendered == "Base situation. Modifier 1. Modifier 3."

    def test_render_with_both(self, simple_dilemma):
        """Test rendering with both substitutions and modifiers."""
        simple_dilemma.modifiers = ["Time is running out."]

        rendered = simple_dilemma.render(
            variable_values={"{SUBJECT}": "robot", "{ACTION}": "something bad"},
            include_modifiers=[0],
        )
        assert rendered == "A robot did something bad. Time is running out."

    def test_get_all_variations(self, simple_dilemma):
        """Test generating all variable combinations."""
        variations = simple_dilemma.get_all_variations()

        # Should have 2 subjects × 2 actions = 4 combinations
        assert len(variations) == 4

        # Check all combinations exist
        expected = [
            {"{SUBJECT}": "person", "{ACTION}": "something good"},
            {"{SUBJECT}": "person", "{ACTION}": "something bad"},
            {"{SUBJECT}": "robot", "{ACTION}": "something good"},
            {"{SUBJECT}": "robot", "{ACTION}": "something bad"},
        ]

        for expected_combo in expected:
            assert expected_combo in variations

    def test_get_all_variations_no_variables(self):
        """Test variations with no variables returns single empty dict."""
        dilemma = Dilemma(
            title="No vars",
            situation_template="Fixed text.",
            question="What?",
            choices=[
                DilemmaChoice(id="a", label="A", description="A"),
                DilemmaChoice(id="b", label="B", description="B"),
            ],
            action_context="Test",
            difficulty_intended=5,
            created_by="human",
        )

        variations = dilemma.get_all_variations()
        assert variations == [{}]

    def test_versioning_and_parent(self):
        """Test version and parent_id tracking."""
        parent = Dilemma(
            title="Original",
            situation_template="Original situation",
            question="What?",
            choices=[
                DilemmaChoice(id="a", label="A", description="A"),
                DilemmaChoice(id="b", label="B", description="B"),
            ],
            action_context="Test",
            difficulty_intended=5,
            created_by="human",
        )

        child = Dilemma(
            version=2,
            parent_id=parent.id,  # Reference parent's UUID
            variation_note="Added time pressure",
            title="Original with pressure",
            situation_template="Original situation",
            question="What?",
            choices=[
                DilemmaChoice(id="a", label="A", description="A"),
                DilemmaChoice(id="b", label="B", description="B"),
            ],
            modifiers=["You have 1 minute."],
            action_context="Test",
            difficulty_intended=7,
            created_by="human",
        )

        assert child.parent_id == parent.id
        assert child.version == 2
        assert child.variation_note == "Added time pressure"

    def test_with_tools(self):
        """Test dilemma with available tools."""
        dilemma = Dilemma(
            title="Tool Test",
            situation_template="Situation requiring tools",
            question="What action?",
            choices=[
                DilemmaChoice(
                    id="notify", label="Notify", description="Send notification", tool_name="send_alert"
                ),
                DilemmaChoice(id="wait", label="Wait", description="Do nothing"),
            ],
            available_tools=[
                ToolSchema(
                    name="send_alert",
                    description="Send an alert",
                    parameters={
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    },
                )
            ],
            action_context="You are an AI with alerting capability.",
            difficulty_intended=3,
            created_by="human",
        )

        assert len(dilemma.available_tools) == 1
        assert dilemma.available_tools[0].name == "send_alert"
        assert dilemma.choices[0].tool_name == "send_alert"

    def test_tags_and_metadata(self, simple_dilemma):
        """Test tags and metadata fields."""
        simple_dilemma.tags = ["ai_autonomy", "test", "simple"]
        simple_dilemma.source = "manual"
        simple_dilemma.notes = "This is a test dilemma"

        assert "ai_autonomy" in simple_dilemma.tags
        assert simple_dilemma.source == "manual"
        assert simple_dilemma.notes == "This is a test dilemma"
        assert simple_dilemma.created_by == "human"
        assert simple_dilemma.created_at is not None
