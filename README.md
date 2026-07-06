# Jetendard

Jetendard is a reproducible font build project that combines
[JetBrainsMono Nerd Font Mono](https://github.com/ryanoasis/nerd-fonts) with
[Pretendard](https://github.com/orioncactus/pretendard) Korean glyphs.

The generated family is named `Jetendard`. Latin glyphs, programming ligatures,
and Nerd Font symbols come from the ligature-enabled `JetBrainsMonoNerdFontMono`
files. Korean and CJK glyphs come from Pretendard and are fitted into exactly two
Latin monospace advances.

The implementation follows the local reference project at `../reference/yeomil-mono`
while meeting the product requirements in `${DOC_PATH}/prd/2607061108_PRD_JETENDARD_FONT.md`.

## Build

```bash
uv sync --all-groups
make download
make run
make test
```

Generated files are written to:

- `fonts/ttf/Jetendard-*.ttf`
- `fonts/otf/Jetendard-*.otf`
- `fonts/webfont/Jetendard-*.woff2`
- `fonts/webfont/jetendard.css`

Generated outputs and upstream downloads are intentionally ignored by git.

## CLI

```bash
uv run jetendard --help
```

Important options:

- `--latin-dir`: directory containing `JetBrainsMonoNerdFontMono-*.ttf`
- `--cjk-dir`: directory containing `Pretendard-*.ttf`
- `--weights`: weights to build, defaulting to `Regular Light Bold`
- `--korean-scale`: visual scale for Korean/CJK glyph fitting
- `--scale`: compatibility alias for `--korean-scale`

The default Korean scale is `1.08`. The builder caps glyphs that would exceed
safe horizontal or vertical bounds, while keeping every Korean/CJK advance width
at exactly two measured Latin advances.

## Scope

Jetendard only uses `JetBrainsMonoNerdFontMono`. It does not use
`JetBrainsMonoNerdFont`, `JetBrainsMonoNerdFontPropo`, or `JetBrainsMonoNL`
no-ligature variants. Because the base font is already Nerd Font patched, this
project does not run a second Nerd Fonts patching step.

## Visual Check Samples

Use the same renderer, point size, and line height when comparing Jetendard
against yeomil-mono or another monospace baseline:

```text
Jetendard 테스트 ABC abc 0123456789
가각간갇갈감갑값같꿇뷁힣
한글과 English가 섞인 source comment
if (상태 === "완료") return "성공";
ㄱㄴㄷㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ
（）［］｛｝，．：；！？
```

## Release Packaging

The initial build writes installable files under `fonts/ttf`, `fonts/otf`, and
`fonts/webfont`. Release archives can be prepared from those directories after a
manual visual pass confirms the default Korean scale. The OTF files are
OTF-compatible outputs using the same TrueType outlines as the generated TTFs.

## License

Jetendard is distributed under the [SIL Open Font License 1.1](LICENSE). Review
the upstream JetBrains Mono, Nerd Fonts, Pretendard, and Yeomil Mono projects for
their full copyright and reserved-name notices.
