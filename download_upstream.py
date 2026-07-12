"""Download and extract upstream font files for D2tendard."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from jetendard.builder import DEFAULT_VARIANTS, SUPPORTED_WEIGHTS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

NERD_FONTS_VERSION = "v3.4.0"
PRETENDARD_VERSION = "1.3.9"
D2CODING_RELEASE_TAG = "VER1.3.2"
D2CODING_STAMP = "Ver1.3.2-20180524"

JETBRAINS_MONO_URL = (
    f"https://github.com/ryanoasis/nerd-fonts/releases/download/"
    f"{NERD_FONTS_VERSION}/JetBrainsMono.zip"
)
PRETENDARD_URL = (
    "https://github.com/orioncactus/pretendard/releases/download/"
    f"v{PRETENDARD_VERSION}/Pretendard-{PRETENDARD_VERSION}.zip"
)
D2CODING_URL = (
    "https://github.com/naver/d2codingfont/releases/download/"
    f"{D2CODING_RELEASE_TAG}/D2Coding-{D2CODING_STAMP}.zip"
)

UPSTREAM_DIR = Path("upstream")
ARCHIVE_DIR = UPSTREAM_DIR / "_archives"
JETBRAINS_DIR = UPSTREAM_DIR / "jetbrainsmono"
PRETENDARD_DIR = UPSTREAM_DIR / "pretendard"
D2CODING_DIR = UPSTREAM_DIR / "d2coding"
OPTIONAL_PRETENDARD_FILES = ("PretendardVariable.ttf",)
D2CODING_RENAMES = {
    f"D2Coding-{D2CODING_STAMP}.ttf": "D2Coding-Regular.ttf",
    f"D2CodingBold-{D2CODING_STAMP}.ttf": "D2Coding-Bold.ttf",
}


def download_file(url: str, output_path: Path) -> None:
    """Download a URL to a file, reusing an existing non-empty file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("Archive already exists: %s", output_path)
        return

    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    logger.info("Downloading %s", url)
    request = urllib.request.Request(url, headers={"User-Agent": "D2tendard builder"})
    try:
        with (
            urllib.request.urlopen(request, timeout=120) as response,
            tmp_path.open("wb") as handle,
        ):
            shutil.copyfileobj(response, handle)
    except Exception as exc:
        if not shutil.which("curl"):
            raise
        logger.warning("Python download failed (%s). Retrying with curl.", exc)
        subprocess.run(
            [
                "curl",
                "-fL",
                "--retry",
                "3",
                "--connect-timeout",
                "30",
                "-A",
                "D2tendard builder",
                "-o",
                str(tmp_path),
                url,
            ],
            check=True,
        )
    tmp_path.replace(output_path)
    logger.info("Downloaded %s", output_path)


def extract_expected_fonts(
    archive_path: Path,
    output_dir: Path,
    required_basenames: set[str],
    optional_basenames: set[str] | None = None,
) -> None:
    """Extract the requested font basenames from a zip archive."""
    output_dir.mkdir(parents=True, exist_ok=True)
    optional_basenames = optional_basenames or set()
    expected_basenames = required_basenames | optional_basenames
    found: dict[str, str] = {}

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            basename = Path(member.filename).name
            if basename not in expected_basenames:
                continue

            target_path = output_dir / basename
            logger.info("Extracting %s -> %s", member.filename, target_path)
            with archive.open(member) as source, target_path.open("wb") as target:
                shutil.copyfileobj(source, target)
            found[basename] = member.filename

    missing = sorted(required_basenames - set(found))
    if missing:
        msg = (
            f"{archive_path} did not contain expected files: {', '.join(missing)}. "
            "Check the pinned upstream version or archive layout."
        )
        raise FileNotFoundError(msg)

    missing_optional = sorted(optional_basenames - set(found))
    if missing_optional:
        logger.warning(
            "%s did not contain optional files: %s",
            archive_path,
            ", ".join(missing_optional),
        )


def write_sources_note() -> None:
    """Write a small note documenting the downloaded upstream versions."""
    jetbrains_files = sorted({variant.latin_filename for variant in DEFAULT_VARIANTS})
    pretendard_files = [f"Pretendard-{weight}.ttf" for weight in SUPPORTED_WEIGHTS]
    note = "\n".join(
        [
            "# D2tendard Upstream Sources",
            "",
            f"- Nerd Fonts JetBrainsMono: {NERD_FONTS_VERSION}",
            f"- Pretendard: {PRETENDARD_VERSION}",
            f"- D2Coding: {D2CODING_RELEASE_TAG}",
            "",
            "## Extracted JetBrainsMono Nerd Font Mono Files",
            "",
            *[f"- `{filename}`" for filename in jetbrains_files],
            "",
            "## Extracted Pretendard Files",
            "",
            *[f"- `{filename}`" for filename in pretendard_files],
            *[
                f"- `{filename}` (optional future variable-weight support)"
                for filename in OPTIONAL_PRETENDARD_FILES
            ],
            "",
            "## Extracted D2Coding Files",
            "",
            *[
                f"- `{renamed}` (from `{original}`)"
                for original, renamed in D2CODING_RENAMES.items()
            ],
            "",
        ]
    )
    (UPSTREAM_DIR / "SOURCES.md").write_text(note, encoding="utf-8")


def main() -> int:
    """Download upstream JetBrainsMono Nerd Font Mono and Pretendard files."""
    jetbrains_archive = ARCHIVE_DIR / f"JetBrainsMono-{NERD_FONTS_VERSION}.zip"
    pretendard_archive = ARCHIVE_DIR / f"Pretendard-{PRETENDARD_VERSION}.zip"
    d2coding_archive = ARCHIVE_DIR / f"D2Coding-{D2CODING_STAMP}.zip"

    jetbrains_expected = {variant.latin_filename for variant in DEFAULT_VARIANTS}
    pretendard_expected = {f"Pretendard-{weight}.ttf" for weight in SUPPORTED_WEIGHTS}

    try:
        download_file(JETBRAINS_MONO_URL, jetbrains_archive)
        download_file(PRETENDARD_URL, pretendard_archive)
        download_file(D2CODING_URL, d2coding_archive)
        extract_expected_fonts(jetbrains_archive, JETBRAINS_DIR, jetbrains_expected)
        extract_expected_fonts(
            pretendard_archive,
            PRETENDARD_DIR,
            pretendard_expected,
            optional_basenames=set(OPTIONAL_PRETENDARD_FILES),
        )
        extract_expected_fonts(d2coding_archive, D2CODING_DIR, set(D2CODING_RENAMES))
        for original, renamed in D2CODING_RENAMES.items():
            (D2CODING_DIR / original).replace(D2CODING_DIR / renamed)
        write_sources_note()
    except Exception:
        logger.exception("Failed to prepare upstream resources")
        return 1

    logger.info("All upstream resources are ready under %s", UPSTREAM_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
