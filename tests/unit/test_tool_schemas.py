from __future__ import annotations

import pytest

from zeta_cli.api.models import ToolCall
from zeta_cli.tools.schemas import ToolSchema, ToolSchemaRegistry


def test_tool_schema_defines_name_description_and_arguments():
    schema = ToolSchema(
        name="read_file",
        description="Read a UTF-8 text file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    )

    assert schema.name == "read_file"
    assert schema.description == "Read a UTF-8 text file."
    assert schema.parameters["type"] == "object"
    assert schema.parameters["required"] == ["path"]


def test_tool_schema_rejects_empty_name():
    with pytest.raises(ValueError, match="tool name"):
        ToolSchema(
            name="",
            description="Read a file.",
            parameters={"type": "object"},
        )


def test_tool_schema_rejects_non_object_parameters():
    with pytest.raises(ValueError, match="parameters"):
        ToolSchema(
            name="read_file",
            description="Read a file.",
            parameters={"type": "string"},
        )


def test_tool_schema_converts_to_tool_definition():
    schema = ToolSchema(
        name="read_file",
        description="Read a UTF-8 text file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    )

    assert schema.to_definition() == {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    }


def test_schema_registry_registers_and_returns_schemas():
    registry = ToolSchemaRegistry()

    schema = ToolSchema(
        name="read_file",
        description="Read a file.",
        parameters={"type": "object"},
    )

    registry.register(schema)

    assert registry.get("read_file") is schema
    assert registry.names() == ("read_file",)


def test_schema_registry_rejects_duplicate_names():
    registry = ToolSchemaRegistry()

    schema = ToolSchema(
        name="read_file",
        description="Read a file.",
        parameters={"type": "object"},
    )

    registry.register(schema)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(schema)


def test_schema_registry_returns_none_for_unknown_schema():
    registry = ToolSchemaRegistry()

    assert registry.get("missing") is None


def test_schema_registry_builds_definitions():
    registry = ToolSchemaRegistry()

    registry.register(
        ToolSchema(
            name="read_file",
            description="Read a file.",
            parameters={"type": "object"},
        )
    )
    registry.register(
        ToolSchema(
            name="write_file",
            description="Write a file.",
            parameters={"type": "object"},
        )
    )

    assert registry.definitions() == [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file.",
                "parameters": {"type": "object"},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write a file.",
                "parameters": {"type": "object"},
            },
        },
    ]
