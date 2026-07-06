"""Tests for the Jetendard CLI helpers."""

from __future__ import annotations

import pytest

from jetendard.cli import family_file_stem, validate_weights, write_css


def test_family_file_stem_removes_spaces() -> None:
    assert family_file_stem("Jetendard Mono") == "JetendardMono"


def test_validate_weights_accepts_supported_weights() -> None:
    assert validate_weights(["Regular", "Light", "Bold"]) == ["Regular", "Light", "Bold"]


def test_validate_weights_rejects_unknown_weight() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        validate_weights(["Regular", "Book"])


def test_write_css_generates_font_face_rules(tmp_path) -> None:
    css_path = write_css(tmp_path, "Jetendard", ["Regular", "Bold"])
    content = css_path.read_text(encoding="utf-8")

    assert css_path.name == "jetendard.css"
    assert "font-family: 'Jetendard';" in content
    assert "Jetendard-Regular.woff2" in content
    assert "font-weight: 400;" in content
    assert "Jetendard-Bold.woff2" in content
    assert "font-weight: 700;" in content
