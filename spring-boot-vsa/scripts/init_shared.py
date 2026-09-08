#!/usr/bin/env python3
"""
init_shared.py — Scaffolds the shared/ package for a Spring Boot VSA project.

Run ONCE per project, before the first slice. create_slice.py output depends on
these classes: the slice Entity extends shared.entity.BaseEntity, and the slice
{Feature}NotFoundException extends shared.exception.EntityNotFoundException.

Usage:
    python init_shared.py \\
        --base-package com.acme.billing \\
        --output-dir src/main/java

    Add --with-json-logging to also scaffold JSON logs + MDC request correlation
    (logback-spring.xml, RequestIdFilter, MdcTaskDecorator).

Placeholders substituted in every template file:
    {{BasePackage}} -> dotted base package (e.g. com.acme.billing)

AsyncConfig.java.tmpl additionally carries a {{TASK_DECORATOR_WIRING}} marker
that this script resolves: with --with-json-logging it becomes the
MdcTaskDecorator wiring line, otherwise the line is removed entirely.

The script NEVER overwrites existing files. If a file already exists it is
skipped with a warning, so re-running is always safe.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

# Allow running as a script from any CWD: the helpers module sits next to us.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _scaffold_common import substitute, write_file

# Template name (under assets/shared/) -> destination under {base}/shared/.
CORE_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("BaseEntity.java.tmpl",              "entity/BaseEntity.java"),
    ("EntityNotFoundException.java.tmpl", "exception/EntityNotFoundException.java"),
    ("GlobalExceptionHandler.java.tmpl",  "exception/GlobalExceptionHandler.java"),
    # AsyncConfig is handled separately: its {{TASK_DECORATOR_WIRING}} marker
    # depends on --with-json-logging.
)

# Written only with --with-json-logging.
LOGGING_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("RequestIdFilter.java.tmpl",  "config/RequestIdFilter.java"),
    ("MdcTaskDecorator.java.tmpl", "config/MdcTaskDecorator.java"),
)

MDC_WIRING_LINE = "        executor.setTaskDecorator(new MdcTaskDecorator());\n"


def build_async_config(template_text: str, with_mdc: bool) -> str:
    """Resolve the AsyncConfig wiring marker.

    The marker is a full line replaced together with its trailing newline so the
    plain variant leaves no blank-line residue inside the method body.
    """
    wiring = MDC_WIRING_LINE if with_mdc else ""
    return template_text.replace("{{TASK_DECORATOR_WIRING}}\n", wiring)


def generate_shared(
    base_package: str,
    output_dir: Path,
    resources_dir: Path,
    assets_dir: Path,
    with_json_logging: bool,
    overwrite: bool,
) -> None:
    shared_root = output_dir / Path(*base_package.split(".")) / "shared"
    mapping = {"BasePackage": base_package}

    print(f"\nScaffolding shared/ package at {shared_root}")
    if with_json_logging:
        print("Including JSON logging + MDC correlation scaffold")
    print()

    written = 0
    skipped = 0

    # 1. Core templates (always generated).
    for template_name, dest_pattern in CORE_TEMPLATES:
        dest = shared_root / dest_pattern
        template_text = (assets_dir / template_name).read_text(encoding="utf-8")
        content = substitute(template_text, mapping)
        if write_file(dest, content, overwrite):
            written += 1
        else:
            skipped += 1

    # 2. AsyncConfig — marker resolved before substitution.
    async_dest = shared_root / "config" / "AsyncConfig.java"
    async_text = (assets_dir / "AsyncConfig.java.tmpl").read_text(encoding="utf-8")
    async_content = substitute(build_async_config(async_text, with_json_logging), mapping)
    if write_file(async_dest, async_content, overwrite):
        written += 1
    else:
        skipped += 1
        # Files are never overwritten, so a second run that ADDS --with-json-logging
        # to an existing project would silently leave AsyncConfig unwired. Warn.
        if with_json_logging and "setTaskDecorator" not in async_dest.read_text(encoding="utf-8"):
            print()
            print("WARNING: AsyncConfig.java already exists and does NOT wire MdcTaskDecorator,")
            print("         so --with-json-logging cannot enable async MDC propagation here.")
            print("         Add this line inside taskExecutor(), just before executor.initialize():")
            print("             executor.setTaskDecorator(new MdcTaskDecorator());")
            print("         (or re-run with --overwrite to regenerate AsyncConfig.java).")

    # 3. Opt-in JSON logging assets.
    if with_json_logging:
        for template_name, dest_pattern in LOGGING_TEMPLATES:
            dest = shared_root / dest_pattern
            template_text = (assets_dir / template_name).read_text(encoding="utf-8")
            content = substitute(template_text, mapping)
            if write_file(dest, content, overwrite):
                written += 1
            else:
                skipped += 1

        logback_dest = resources_dir / "logback-spring.xml"
        logback_text = (assets_dir / "logback-spring.xml.tmpl").read_text(encoding="utf-8")
        if write_file(logback_dest, substitute(logback_text, mapping), overwrite):
            written += 1
        else:
            skipped += 1

    print(f"\nDone. {written} file(s) written, {skipped} skipped.")
    print("Next steps:")
    print("  1. Set spring.mvc.problemdetails.enabled=true (application.yml or .properties) so")
    print("     framework errors render as application/problem+json.")
    print("  2. Replace the problem-type base URI https://api.example.com/problems/ in")
    print("     GlobalExceptionHandler with your API's real one.")
    print("  3. Scaffold your first slice: python scripts/create_slice.py --feature ... --base-package ...")
    print("  4. Spring Boot 2.x? ProblemDetail needs Boot 3.x+ - see references/shared-and-logging.md")
    print("     for the hand-rolled ErrorResponse fallback.")
    if with_json_logging:
        print("  5. Add the logstash-logback-encoder dependency:")
        print("       Maven (pom.xml):")
        print("         <dependency>")
        print("             <groupId>net.logstash.logback</groupId>")
        print("             <artifactId>logstash-logback-encoder</artifactId>")
        print("             <version>8.1</version> <!-- check for the latest version -->")
        print("         </dependency>")
        print("       Gradle (build.gradle):")
        print("         implementation 'net.logstash.logback:logstash-logback-encoder:8.1'")
        print("       Gradle Kotlin DSL (build.gradle.kts):")
        print("         implementation(\"net.logstash.logback:logstash-logback-encoder:8.1\")")
        print("  6. Activate JSON output with the json-logging profile:")
        print("       SPRING_PROFILES_ACTIVE=json-logging  (or --spring.profiles.active=json-logging)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold the shared/ package for a Spring Boot VSA project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base-package", required=True,
        help="Dotted base package, e.g. 'com.acme.billing'. The script creates "
             "'shared/' under this package.",
    )
    parser.add_argument(
        "--output-dir", default="src/main/java",
        help="Source root. Default: src/main/java",
    )
    parser.add_argument(
        "--resources-dir", default="src/main/resources",
        help="Resources root for logback-spring.xml (only used with "
             "--with-json-logging). Default: src/main/resources",
    )
    parser.add_argument(
        "--with-json-logging", action="store_true",
        help="Also scaffold JSON logging + MDC correlation: logback-spring.xml, "
             "RequestIdFilter, MdcTaskDecorator (wired into AsyncConfig).",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite files that already exist. Default: skip them.",
    )
    parser.add_argument(
        "--assets-dir", default=None,
        help="Override the shared-assets directory. Defaults to ../assets/shared/ "
             "relative to this script.",
    )
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    assets_dir = (
        Path(args.assets_dir) if args.assets_dir
        else script_dir.parent / "assets" / "shared"
    )
    if not assets_dir.is_dir():
        raise SystemExit(f"Shared assets directory not found: {assets_dir}")

    generate_shared(
        base_package=args.base_package,
        output_dir=Path(args.output_dir).resolve(),
        resources_dir=Path(args.resources_dir).resolve(),
        assets_dir=assets_dir,
        with_json_logging=args.with_json_logging,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
