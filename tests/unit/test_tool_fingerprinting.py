from zeta_cli.tools.fingerprinting import tool_fingerprint


def test_tool_fingerprint_is_stable_for_same_call():
    first = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )
    second = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )

    assert first == second


def test_tool_fingerprint_changes_when_tool_name_changes():
    first = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )
    second = tool_fingerprint(
        "write_file",
        {"path": "README.md"},
    )

    assert first != second


def test_tool_fingerprint_changes_when_arguments_change():
    first = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )
    second = tool_fingerprint(
        "read_file",
        {"path": "ROADMAP.md"},
    )

    assert first != second


def test_tool_fingerprint_is_independent_of_mapping_order():
    first = tool_fingerprint(
        "read_file",
        {
            "path": "README.md",
            "encoding": "utf-8",
        },
    )
    second = tool_fingerprint(
        "read_file",
        {
            "encoding": "utf-8",
            "path": "README.md",
        },
    )

    assert first == second


def test_tool_fingerprint_returns_hex_digest():
    fingerprint = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )

    assert len(fingerprint) == 64
    int(fingerprint, 16)
