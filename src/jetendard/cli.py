"""Command-line interface for Jetendard."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from jetendard.builder import (
    DEFAULT_KOREAN_SCALE,
    DEFAULT_WEIGHTS,
    SUPPORTED_WEIGHTS,
    merge_fonts,
)

logger = logging.getLogger(__name__)

WEIGHT_TO_CSS = {
    "Thin": 100,
    "ExtraLight": 200,
    "Light": 300,
    "Regular": 400,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
    "ExtraBold": 800,
    "Black": 900,
}


def family_file_stem(family_name: str) -> str:
    """Return the output filename stem for a family name."""
    return "".join(family_name.split())


def write_css(output_web_dir: Path, family_name: str, weights: list[str]) -> Path:
    """Generate @font-face rules for compiled web fonts."""
    css_content: list[str] = []
    stem = family_file_stem(family_name)
    for weight in weights:
        font_filename = f"{stem}-{weight}.woff2"
        css_content.append(
            "\n".join(
                [
                    "@font-face {",
                    f"  font-family: '{family_name}';",
                    f"  src: url('./{font_filename}') format('woff2');",
                    f"  font-weight: {WEIGHT_TO_CSS[weight]};",
                    "  font-style: normal;",
                    "  font-display: swap;",
                    "}",
                    "",
                ]
            )
        )

    css_path = output_web_dir / f"{stem.lower()}.css"
    css_path.write_text("\n".join(css_content), encoding="utf-8")
    logger.info("Wrote web font CSS to %s", css_path)
    return css_path


def build_parser() -> argparse.ArgumentParser:
    """Build the Jetendard CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Build Jetendard from ligature-enabled JetBrainsMono Nerd Font Mono "
            "and Pretendard Korean glyphs."
        )
    )
    parser.add_argument(
        "--latin-dir",
        default="upstream/jetbrainsmono",
        help="Directory containing JetBrainsMonoNerdFontMono TTF files.",
    )
    parser.add_argument(
        "--cjk-dir",
        default="upstream/pretendard",
        help="Directory containing Pretendard TTF files.",
    )
    parser.add_argument(
        "--output-dir",
        default="fonts",
        help="Directory to save generated fonts.",
    )
    parser.add_argument(
        "--family-name",
        default="Jetendard",
        help="Generated font family name.",
    )
    parser.add_argument(
        "--korean-scale",
        "--scale",
        dest="korean_scale",
        type=float,
        default=DEFAULT_KOREAN_SCALE,
        help=(
            "Visual scale factor for Korean/CJK glyphs after UPM normalization "
            f"(default: {DEFAULT_KOREAN_SCALE})."
        ),
    )
    parser.add_argument(
        "--weights",
        nargs="+",
        default=list(DEFAULT_WEIGHTS),
        help="Weights to generate (default: Regular Light Bold).",
    )
    return parser


def validate_weights(weights: list[str]) -> list[str]:
    """Validate requested weight names."""
    unsupported = [weight for weight in weights if weight not in SUPPORTED_WEIGHTS]
    if unsupported:
        supported = ", ".join(SUPPORTED_WEIGHTS)
        msg = f"Unsupported weight(s): {', '.join(unsupported)}. Supported: {supported}"
        raise ValueError(msg)
    return weights


def main(argv: list[str] | None = None) -> int:
    """Run the Jetendard build."""
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        weights = validate_weights(list(args.weights))
    except ValueError as exc:
        parser.error(str(exc))

    latin_dir = Path(args.latin_dir)
    cjk_dir = Path(args.cjk_dir)
    base_output_dir = Path(args.output_dir)
    ttf_dir = base_output_dir / "ttf"
    otf_dir = base_output_dir / "otf"
    web_dir = base_output_dir / "webfont"

    ttf_dir.mkdir(parents=True, exist_ok=True)
    otf_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)

    stem = family_file_stem(args.family_name)
    logger.info("Starting Jetendard build for weights: %s", ", ".join(weights))

    for weight in weights:
        latin_path = latin_dir / f"JetBrainsMonoNerdFontMono-{weight}.ttf"
        cjk_path = cjk_dir / f"Pretendard-{weight}.ttf"
        output_path_ttf = ttf_dir / f"{stem}-{weight}.ttf"
        output_path_otf = otf_dir / f"{stem}-{weight}.otf"
        output_path_woff2 = web_dir / f"{stem}-{weight}.woff2"

        if not latin_path.exists():
            logger.error("Latin font file not found: %s", latin_path)
            logger.error("Run `make download` to fetch JetBrainsMonoNerdFontMono files.")
            return 1
        if not cjk_path.exists():
            logger.error("CJK font file not found: %s", cjk_path)
            logger.error("Run `make download` to fetch Pretendard files.")
            return 1

        try:
            stats = merge_fonts(
                latin_path=latin_path,
                cjk_path=cjk_path,
                output_path=output_path_ttf,
                family_name=args.family_name,
                subfamily_name=weight,
                korean_scale=args.korean_scale,
            )
            logger.info(
                "%s: copied=%d capped=%d latin_advance=%d korean_advance=%d",
                weight,
                stats.copied_count,
                stats.capped_count,
                stats.latin_advance,
                stats.korean_advance,
            )

            logger.info("Saving OTF-compatible output: %s", output_path_otf)
            otf_font = TTFont(str(output_path_ttf))
            otf_font.save(str(output_path_otf))
            TTFont(str(output_path_otf)).close()
            otf_font.close()

            logger.info("Converting to WOFF2: %s", output_path_woff2)
            web_font = TTFont(str(output_path_ttf))
            web_font.flavor = "woff2"
            web_font.save(str(output_path_woff2))
            web_font.close()
        except Exception:
            logger.exception("Failed to build weight %s", weight)
            return 1

    write_css(web_dir, args.family_name, weights)
    logger.info("All requested Jetendard weights built successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
