"""Unit tests for Jetendard builder logic."""

from __future__ import annotations

from pathlib import Path

import pytest
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

from jetendard.builder import (
    calculate_fitted_transform,
    calculate_korean_target_width,
    collect_cjk_codepoints,
    derive_latin_advance,
    enforce_monospace_flags,
    is_cjk,
    merge_fonts,
    update_font_names,
)


class DummyPanose:
    """Minimal Panose object for fixed-pitch flag tests."""

    bProportion = 0


def make_width_font(widths: dict[str, int]) -> TTFont:
    """Create a minimal font with cmap and hmtx tables for metric tests."""
    font = TTFont()
    cmap = newTable("cmap")
    cmap.tableVersion = 0
    subtable = CmapSubtable.newSubtable(4)
    subtable.platformID = 3
    subtable.platEncID = 1
    subtable.language = 0
    subtable.cmap = {ord(char): char for char in widths}
    cmap.tables = [subtable]
    font["cmap"] = cmap

    hmtx = newTable("hmtx")
    hmtx.metrics = {char: (width, 0) for char, width in widths.items()}
    font["hmtx"] = hmtx
    return font


def make_name_font() -> TTFont:
    """Create a minimal font with name and head tables."""
    font = TTFont()
    name = newTable("name")
    name.names = []
    font["name"] = name
    head = newTable("head")
    head.fontRevision = 1.0
    font["head"] = head
    return font


def test_is_cjk_supported_ranges() -> None:
    assert is_cjk(0xAC00) is True
    assert is_cjk(0xD7A3) is True
    assert is_cjk(0x1100) is True
    assert is_cjk(0x3131) is True
    assert is_cjk(0xA960) is True
    assert is_cjk(0xD7FF) is True
    assert is_cjk(0x4E00) is True
    assert is_cjk(0x3001) is True
    assert is_cjk(0xFF01) is True
    assert is_cjk(ord("A")) is False


def test_collect_cjk_codepoints_adds_required_jamo() -> None:
    codepoints = collect_cjk_codepoints({0xAC00: "uniAC00", ord("A"): "A"})
    assert 0xAC00 in codepoints
    assert 0x1100 in codepoints
    assert 0x1161 in codepoints
    assert 0x11A8 in codepoints
    assert ord("A") not in codepoints


def test_derive_latin_advance_from_monospaced_sample() -> None:
    font = make_width_font({char: 600 for char in " A0Hinmw"})
    assert derive_latin_advance(font) == 600


def test_derive_latin_advance_rejects_non_monospaced_sample() -> None:
    font = make_width_font({char: 600 for char in " A0Hinmw"})
    font["hmtx"].metrics["m"] = (700, 0)
    with pytest.raises(ValueError, match="not monospaced"):
        derive_latin_advance(font)


def test_calculate_korean_target_width() -> None:
    assert calculate_korean_target_width(600) == 1200


def test_calculate_korean_target_width_rejects_invalid_advance() -> None:
    with pytest.raises(ValueError, match="positive"):
        calculate_korean_target_width(0)


def test_fitted_transform_centers_uncapped_glyph() -> None:
    fitted = calculate_fitted_transform(
        (100, -100, 900, 700),
        target_width=1200,
        requested_scale=1.0,
        safe_ymin=-300,
        safe_ymax=900,
        side_bearing_guard=20,
    )

    assert fitted.capped is False
    assert fitted.transformed_bounds == pytest.approx((200, -100, 1000, 700))
    assert fitted.left_side_bearing == 200


def test_fitted_transform_caps_unsafe_scale() -> None:
    fitted = calculate_fitted_transform(
        (0, -100, 1000, 800),
        target_width=1200,
        requested_scale=1.3,
        safe_ymin=-300,
        safe_ymax=900,
        side_bearing_guard=20,
    )

    assert fitted.capped is True
    assert fitted.scale == pytest.approx(1.125)
    assert fitted.transformed_bounds is not None
    assert fitted.transformed_bounds[0] >= 20
    assert fitted.transformed_bounds[2] <= 1180
    assert fitted.transformed_bounds[3] <= 900


def test_update_font_names_sets_required_records() -> None:
    font = make_name_font()
    update_font_names(font, "Jetendard", "Regular")

    name_table = font["name"]
    assert name_table.getName(1, 3, 1, 0x409).toUnicode() == "Jetendard"
    assert name_table.getName(2, 3, 1, 0x409).toUnicode() == "Regular"
    assert name_table.getName(4, 3, 1, 0x409).toUnicode() == "Jetendard Regular"
    assert name_table.getName(6, 3, 1, 0x409).toUnicode() == "Jetendard-Regular"
    assert name_table.getName(16, 3, 1, 0x409).toUnicode() == "Jetendard"
    assert name_table.getName(17, 3, 1, 0x409).toUnicode() == "Regular"


def test_enforce_monospace_flags() -> None:
    font = TTFont()
    post = newTable("post")
    post.isFixedPitch = 0
    font["post"] = post
    os2 = newTable("OS/2")
    os2.panose = DummyPanose()
    font["OS/2"] = os2

    enforce_monospace_flags(font)

    assert font["post"].isFixedPitch == 1
    assert font["OS/2"].panose.bProportion == 9


def test_integration_merge_skips_without_upstream_fonts(tmp_path: Path) -> None:
    latin_path = Path("upstream/jetbrainsmono/JetBrainsMonoNerdFontMono-Regular.ttf")
    cjk_path = Path("upstream/pretendard/Pretendard-Regular.ttf")
    if not latin_path.exists() or not cjk_path.exists():
        pytest.skip("upstream fonts have not been downloaded")

    output_path = tmp_path / "Jetendard-Regular.ttf"
    stats = merge_fonts(
        latin_path=latin_path,
        cjk_path=cjk_path,
        output_path=output_path,
        family_name="Jetendard",
        subfamily_name="Regular",
    )

    font = TTFont(str(output_path))
    cmap = font.getBestCmap()
    features = [record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord]
    assert stats.copied_count > 10_000
    assert font["hmtx"].metrics[cmap[ord("가")]][0] == font["hmtx"].metrics[cmap[ord("A")]][0] * 2
    assert font["name"].getName(1, 3, 1, 0x409).toUnicode() == "Jetendard"
    assert font["post"].isFixedPitch == 1
    assert "calt" in features
    assert "ccmp" in features
    font.close()
