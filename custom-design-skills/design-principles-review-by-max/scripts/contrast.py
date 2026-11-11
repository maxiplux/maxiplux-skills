#!/usr/bin/env python3
"""WCAG contrast ratio between two colors.

Part of the design-principles-review-by-max skill. Author: max.

Usage:
    contrast.py FOREGROUND BACKGROUND [--min RATIO]
    contrast.py --report PATH/report.json      # check every pair captured by capture.mjs

Colors may be written as #rgb, #rrggbb, #rrggbbaa, rgb(r, g, b) or rgba(r, g, b, a).
A foreground with alpha is blended over the background first. The background must be opaque.

Examples:
    contrast.py '#777' '#fff'
    contrast.py 'rgb(15, 23, 42)' 'rgb(248, 250, 252)'
    contrast.py '#6b7280' '#ffffff' --min 4.5    # exit status 1 if the ratio is below 4.5

Thresholds (WCAG 2.x):
    4.5:1  normal text, level AA (1.4.3)
    3:1    large text (>= 24px, or >= 18.66px bold), level AA (1.4.3)
    3:1    UI components, meaningful graphics, focus indicators (1.4.11)
    7:1    normal text, level AAA (1.4.6)
    4.5:1  large text, level AAA (1.4.6)
"""
import argparse
import json
import re
import sys


def parse_color(text):
    """Return (r, g, b, a) with channels 0-255 and alpha 0-1."""
    value = text.strip().lower()
    if value.startswith("#"):
        digits = value[1:]
        if len(digits) in (3, 4):
            digits = "".join(ch * 2 for ch in digits)
        if len(digits) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", digits):
            raise ValueError(f"not a valid hex color: {text!r}")
        r, g, b = (int(digits[i:i + 2], 16) for i in (0, 2, 4))
        a = int(digits[6:8], 16) / 255 if len(digits) == 8 else 1.0
        return r, g, b, a
    match = re.fullmatch(r"rgba?\(([^)]+)\)", value)
    if match:
        parts = [p for p in re.split(r"[\s,/]+", match.group(1).strip()) if p]
        if len(parts) not in (3, 4):
            raise ValueError(f"not a valid rgb() color: {text!r}")
        r, g, b = (float(p) for p in parts[:3])
        a = 1.0
        if len(parts) == 4:
            a = float(parts[3][:-1]) / 100 if parts[3].endswith("%") else float(parts[3])
        if not all(0 <= c <= 255 for c in (r, g, b)) or not 0 <= a <= 1:
            raise ValueError(f"color out of range: {text!r}")
        return r, g, b, a
    raise ValueError(f"unsupported color format: {text!r} (use #hex or rgb())")


def blend(fg, bg):
    """Composite a foreground with alpha over an opaque background."""
    r, g, b, a = fg
    return tuple(a * f + (1 - a) * k for f, k in zip((r, g, b), bg[:3]))


def luminance(rgb):
    """Relative luminance as defined by WCAG 2.x."""
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(foreground, background):
    bg = parse_color(background)
    if bg[3] < 1:
        raise ValueError("background must be opaque; resolve it against what is behind it first")
    fg = blend(parse_color(foreground), bg)
    lighter, darker = sorted((luminance(fg), luminance(bg[:3])), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def font_weight(value):
    """CSS font-weight as a number. Browsers report numbers; accept the keywords as well."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 700.0 if str(value).strip().lower() in ("bold", "bolder") else 400.0


def check_report(path):
    """Check every color pair in a capture.mjs report. Returns the number of text failures."""
    with open(path, encoding="utf-8") as handle:
        report = json.load(handle)
    failures = 0
    for width, data in report.get("widths", {}).items():
        pairs = data.get("colors", [])
        failed = []
        for pair in pairs:
            ratio = contrast_ratio(pair["color"], pair["background"])
            size = float(pair["fontSize"].rstrip("px"))
            large = size >= 24 or (size >= 18.66 and font_weight(pair["fontWeight"]) >= 700)
            needed = 3.0 if large else 4.5
            if ratio < needed:
                failed.append((ratio, needed, pair))
        print(f"Width {width}px: {len(pairs)} text color pairs, {len(failed)} below AA")
        for ratio, needed, pair in sorted(failed, key=lambda item: item[0]):
            print(f"  FAIL {ratio:.2f}:1 (needs {needed}:1)  {pair['color']} on {pair['background']}  "
                  f"{pair['fontSize']}/{pair['fontWeight']}  x{pair['count']}  \"{pair['sample']}\"")
        failures += len(failed)

        # Non-text contrast (1.4.11): candidates only. Confirm on a screenshot before reporting.
        candidates = []
        for stop in data.get("focusOrder", []):
            label = f"#{stop['index']} <{stop['tag']}> \"{stop['name'][:30]}\""
            # Fields are identified by their boundary. A button with a text label needs none.
            if stop["tag"] in ("input", "select", "textarea"):
                edges = [stop["fill"]] + ([stop["border"]] if stop.get("border") else [])
                best = max(contrast_ratio(edge, stop["surround"]) for edge in edges)
                if best < 3.0:
                    candidates.append(f"  CHECK control boundary {best:.2f}:1 (needs 3:1)  {label}")
            if stop.get("outlineColor"):
                ratio = contrast_ratio(stop["outlineColor"], stop["surround"])
                if ratio < 3.0:
                    candidates.append(f"  CHECK focus outline {ratio:.2f}:1 (needs 3:1)  {label}")
            if not stop.get("focusChange", True):
                candidates.append(f"  CHECK no style change on focus  {label}")
        if candidates:
            print(f"  {len(candidates)} non-text candidates to confirm on a screenshot:")
            print("\n".join(candidates))
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description="WCAG contrast ratio between two colors.")
    parser.add_argument("foreground", nargs="?", help="text or graphic color, e.g. '#777'")
    parser.add_argument("background", nargs="?", help="background color, e.g. '#fff'")
    parser.add_argument("--min", type=float, dest="minimum", metavar="RATIO",
                        help="exit with status 1 if the ratio is below this value")
    parser.add_argument("--report", metavar="PATH",
                        help="check every pair in a report.json written by capture.mjs; "
                             "exit with status 1 if any text pair is below AA")
    args = parser.parse_args(argv)

    if args.report:
        try:
            return 1 if check_report(args.report) else 0
        except (OSError, ValueError, KeyError) as error:
            print(f"error: could not read report: {error}", file=sys.stderr)
            return 2
    if not args.foreground or not args.background:
        parser.error("give FOREGROUND and BACKGROUND, or --report PATH")

    try:
        ratio = contrast_ratio(args.foreground, args.background)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    # The ratio is rounded for display only. Pass/fail uses the exact value, so 4.499 fails 4.5.
    print(f"Contrast ratio: {ratio:.2f}:1  ({args.foreground} on {args.background})")
    checks = [
        ("AA  normal text (4.5:1)", 4.5),
        ("AA  large text (3:1)", 3.0),
        ("AA  UI components and graphics (3:1)", 3.0),
        ("AAA normal text (7:1)", 7.0),
        ("AAA large text (4.5:1)", 4.5),
    ]
    for label, threshold in checks:
        print(f"  {'PASS' if ratio >= threshold else 'FAIL'}  {label}")

    if args.minimum is not None and ratio < args.minimum:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
