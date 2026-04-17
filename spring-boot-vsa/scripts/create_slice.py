#!/usr/bin/env python3
"""
create_slice.py — Scaffolds a new Spring Boot vertical slice from templates.

Generates the full directory tree for one feature slice, following the
Vertical Slice Architecture conventions described in ../SKILL.md.

Usage:
    python create_slice.py \\
        --feature payment \\
        --actions create,list,get,update,delete \\
        --base-package com.acme.billing \\
        --output-dir src/main/java

Placeholders substituted in every template file:
    {{Feature}}     -> PascalCase feature name (e.g. Payment)
    {{feature}}     -> camelCase feature name (e.g. payment)
    {{FEATURE}}     -> UPPER_SNAKE feature name (e.g. PAYMENT)
    {{BasePackage}} -> dotted base package (e.g. com.acme.billing)

The Controller template uses extra markers ({{HANDLER_FIELDS}}, {{ENDPOINTS}},
{{HANDLER_IMPORTS}}, {{DTO_IMPORTS}}, plus conditional import markers) that the
script fills in based on which actions were requested. Actions the user did not
request are simply omitted — no dead code.

The script NEVER overwrites existing files. If a file already exists it is
skipped with a warning, so you can re-run the script after filling in logic
without losing your work.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# All actions the script knows how to scaffold. Order matters for controller
# endpoint layout (create first, then reads, then mutations, then delete).
KNOWN_ACTIONS = ("create", "list", "get", "update", "delete")

# Templates that are generated unconditionally (one per slice).
CORE_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("Entity.java.tmpl",           "model/{Feature}.java"),
    ("Repository.java.tmpl",       "model/{Feature}Repository.java"),
    ("Mapper.java.tmpl",           "model/{Feature}Mapper.java"),
    ("Response.java.tmpl",         "api/response/{Feature}Response.java"),
    ("NotFoundException.java.tmpl","exception/{Feature}NotFoundException.java"),
)

# Templates that are generated only when their action is requested.
ACTION_TEMPLATES: dict[str, tuple[tuple[str, str], ...]] = {
    "create": (
        ("CreateRequest.java.tmpl", "api/request/Create{Feature}Request.java"),
        ("CreateHandler.java.tmpl", "handlers/Create{Feature}Handler.java"),
    ),
    "list": (
        ("ListHandler.java.tmpl",   "handlers/List{Feature}Handler.java"),
    ),
    "get": (
        ("GetHandler.java.tmpl",    "handlers/Get{Feature}Handler.java"),
    ),
    "update": (
        ("UpdateRequest.java.tmpl", "api/request/Update{Feature}Request.java"),
        ("UpdateHandler.java.tmpl", "handlers/Update{Feature}Handler.java"),
    ),
    "delete": (
        ("DeleteHandler.java.tmpl", "handlers/Delete{Feature}Handler.java"),
    ),
}


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

def to_pascal(name: str) -> str:
    """notification -> Notification ; user-profile -> UserProfile ; userProfile -> UserProfile."""
    parts = re.split(r"[-_\s]+", name.strip())
    result = []
    for part in parts:
        # Split on inner capital letters too so "userProfile" becomes ["user","Profile"].
        for sub in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z]|$)", part):
            if sub:
                result.append(sub[0].upper() + sub[1:].lower())
    return "".join(result)


def to_camel(name: str) -> str:
    pascal = to_pascal(name)
    return pascal[0].lower() + pascal[1:] if pascal else ""


def to_upper_snake(name: str) -> str:
    camel = to_camel(name)
    # Insert underscore before each uppercase letter, then uppercase the whole string.
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel).upper()


# ---------------------------------------------------------------------------
# Controller assembly — handled separately because it's action-driven
# ---------------------------------------------------------------------------

def build_controller(
    feature_pascal: str,
    feature_camel: str,
    base_package: str,
    actions: list[str],
    template_text: str,
) -> str:
    """Fill in Controller template based on requested actions.

    The template has several markers; we build each block conditionally so the
    generated controller only contains endpoints for actions the user asked for.
    """
    handler_imports: list[str] = []
    dto_imports: list[str] = []
    handler_fields: list[str] = []
    endpoints: list[str] = []

    needs_valid = any(a in actions for a in ("create", "update"))
    needs_page = "list" in actions

    # Handler fields + imports in canonical order.
    for action in KNOWN_ACTIONS:
        if action not in actions:
            continue
        action_pascal = action.capitalize()
        handler_imports.append(
            f"import {base_package}.features.{feature_camel}.handlers.{action_pascal}{feature_pascal}Handler;"
        )
        handler_fields.append(
            f"    private final {action_pascal}{feature_pascal}Handler {action}{feature_pascal}Handler;"
        )

    # DTO imports.
    if "create" in actions:
        dto_imports.append(
            f"import {base_package}.features.{feature_camel}.api.request.Create{feature_pascal}Request;"
        )
    if "update" in actions:
        dto_imports.append(
            f"import {base_package}.features.{feature_camel}.api.request.Update{feature_pascal}Request;"
        )
    dto_imports.append(
        f"import {base_package}.features.{feature_camel}.api.response.{feature_pascal}Response;"
    )

    # Endpoint blocks.
    if "create" in actions:
        endpoints.append(f"""    @PostMapping
    @Operation(summary = "Create a new {feature_camel}")
    @ApiResponses({{
            @ApiResponse(responseCode = "201", description = "Created"),
            @ApiResponse(responseCode = "400", description = "Invalid request"),
    }})
    public ResponseEntity<{feature_pascal}Response> create(@Valid @RequestBody Create{feature_pascal}Request request) {{
        log.info("Creating {feature_camel} with request={{}}", request);
        {feature_pascal}Response response = create{feature_pascal}Handler.handle(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }}""")
    if "list" in actions:
        endpoints.append(f"""    @GetMapping
    @Operation(summary = "List {feature_camel}s with pagination")
    @ApiResponses({{
            @ApiResponse(responseCode = "200", description = "OK"),
    }})
    public Page<{feature_pascal}Response> list(Pageable pageable) {{
        return list{feature_pascal}Handler.handle(pageable);
    }}""")
    if "get" in actions:
        endpoints.append(f"""    @GetMapping("/{{id}}")
    @Operation(summary = "Get a {feature_camel} by id")
    @ApiResponses({{
            @ApiResponse(responseCode = "200", description = "Found"),
            @ApiResponse(responseCode = "404", description = "Not found"),
    }})
    public {feature_pascal}Response get(@PathVariable Long id) {{
        return get{feature_pascal}Handler.handle(id);
    }}""")
    if "update" in actions:
        endpoints.append(f"""    @PutMapping("/{{id}}")
    @Operation(summary = "Update a {feature_camel}")
    @ApiResponses({{
            @ApiResponse(responseCode = "200", description = "Updated"),
            @ApiResponse(responseCode = "400", description = "Invalid request"),
            @ApiResponse(responseCode = "404", description = "Not found"),
    }})
    public {feature_pascal}Response update(@PathVariable Long id, @Valid @RequestBody Update{feature_pascal}Request request) {{
        log.info("Updating {feature_camel} id={{}} with request={{}}", id, request);
        return update{feature_pascal}Handler.handle(id, request);
    }}""")
    if "delete" in actions:
        endpoints.append(f"""    @DeleteMapping("/{{id}}")
    @Operation(summary = "Delete a {feature_camel}")
    @ApiResponses({{
            @ApiResponse(responseCode = "204", description = "Deleted"),
            @ApiResponse(responseCode = "404", description = "Not found"),
    }})
    public ResponseEntity<Void> delete(@PathVariable Long id) {{
        log.info("Deleting {feature_camel} id={{}}", id);
        delete{feature_pascal}Handler.handle(id);
        return ResponseEntity.noContent().build();
    }}""")

    # Conditional imports.
    page_import_lines = []
    if needs_page:
        page_import_lines.append("import org.springframework.data.domain.Page;")
        page_import_lines.append("import org.springframework.data.domain.Pageable;")
    valid_import = "import jakarta.validation.Valid;" if needs_valid else ""
    http_status_import = "import org.springframework.http.HttpStatus;" if "create" in actions else ""

    return (
        template_text
        .replace("{{HANDLER_IMPORTS}}", "\n".join(handler_imports))
        .replace("{{DTO_IMPORTS}}",     "\n".join(dto_imports))
        .replace("{{HANDLER_FIELDS}}",  "\n".join(handler_fields))
        .replace("{{ENDPOINTS}}",       "\n\n".join(endpoints))
        .replace("{{VALID_IMPORT}}",    valid_import)
        .replace("{{PAGE_IMPORT}}",     "\n".join(page_import_lines))
        .replace("{{HTTP_STATUS_IMPORT}}", http_status_import)
    )


# ---------------------------------------------------------------------------
# Placeholder substitution
# ---------------------------------------------------------------------------

def substitute(text: str, feature: str, base_package: str) -> str:
    return (
        text
        .replace("{{BasePackage}}", base_package)
        .replace("{{Feature}}",     to_pascal(feature))
        .replace("{{FEATURE}}",     to_upper_snake(feature))
        .replace("{{feature}}",     to_camel(feature))
    )


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def write_file(path: Path, content: str, overwrite: bool) -> bool:
    """Return True if the file was written, False if it was skipped."""
    if path.exists() and not overwrite:
        print(f"  SKIP   {path} (already exists, pass --overwrite to replace)")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  WRITE  {path}")
    return True


def generate_slice(
    feature: str,
    actions: list[str],
    base_package: str,
    output_dir: Path,
    assets_dir: Path,
    overwrite: bool,
    with_event: bool,
) -> None:
    feature_pascal = to_pascal(feature)
    feature_camel = to_camel(feature)

    # Resolve the slice root directory: output_dir/base/package/as/path/features/{feature}/
    slice_root = output_dir / Path(*base_package.split(".")) / "features" / feature_camel

    print(f"\nScaffolding slice '{feature_camel}' ({feature_pascal}) "
          f"at {slice_root}")
    print(f"Actions: {', '.join(actions)}")
    if with_event:
        print("Including domain event scaffold")
    print()

    written = 0
    skipped = 0

    # 1. Core templates (always generated).
    for template_name, dest_pattern in CORE_TEMPLATES:
        dest = slice_root / dest_pattern.format(Feature=feature_pascal)
        template_text = (assets_dir / template_name).read_text(encoding="utf-8")
        content = substitute(template_text, feature, base_package)
        if write_file(dest, content, overwrite):
            written += 1
        else:
            skipped += 1

    # 2. Action-specific templates.
    for action in actions:
        for template_name, dest_pattern in ACTION_TEMPLATES[action]:
            dest = slice_root / dest_pattern.format(Feature=feature_pascal)
            template_text = (assets_dir / template_name).read_text(encoding="utf-8")
            content = substitute(template_text, feature, base_package)
            if write_file(dest, content, overwrite):
                written += 1
            else:
                skipped += 1

    # 3. Controller — built programmatically from markers.
    controller_dest = slice_root / "api" / f"{feature_pascal}Controller.java"
    controller_template = (assets_dir / "Controller.java.tmpl").read_text(encoding="utf-8")
    controller_content = build_controller(
        feature_pascal=feature_pascal,
        feature_camel=feature_camel,
        base_package=base_package,
        actions=actions,
        template_text=controller_template,
    )
    controller_content = substitute(controller_content, feature, base_package)
    if write_file(controller_dest, controller_content, overwrite):
        written += 1
    else:
        skipped += 1

    # 4. Optional domain event.
    if with_event:
        event_dest = slice_root / "events" / f"{feature_pascal}ChangedEvent.java"
        template_text = (assets_dir / "Event.java.tmpl").read_text(encoding="utf-8")
        content = substitute(template_text, feature, base_package)
        if write_file(event_dest, content, overwrite):
            written += 1
        else:
            skipped += 1

    print(f"\nDone. {written} file(s) written, {skipped} skipped.")
    print(f"Next steps:")
    print(f"  1. Fill in real domain fields on {feature_pascal} entity")
    print(f"  2. Adjust Request/Response record components to match the API contract")
    print(f"  3. Replace the TODO comments in the mapper with real mappings")
    print(f"  4. Review @RequestMapping prefix and @Table name for project conventions")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_actions(raw: str) -> list[str]:
    requested = [a.strip().lower() for a in raw.split(",") if a.strip()]
    unknown = [a for a in requested if a not in KNOWN_ACTIONS]
    if unknown:
        raise SystemExit(
            f"Unknown action(s): {', '.join(unknown)}. "
            f"Supported: {', '.join(KNOWN_ACTIONS)}."
        )
    # Preserve canonical order regardless of how the user listed them.
    return [a for a in KNOWN_ACTIONS if a in requested]


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a Spring Boot vertical slice from templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--feature", required=True,
        help="Feature name (e.g. 'payment', 'user-profile'). A single noun is best.",
    )
    parser.add_argument(
        "--actions", default="create,list,get,update,delete",
        help=f"Comma-separated subset of: {', '.join(KNOWN_ACTIONS)}. "
             "Default: all five CRUD actions.",
    )
    parser.add_argument(
        "--base-package", required=True,
        help="Dotted base package, e.g. 'com.acme.billing'. The script creates "
             "'features/{feature}/' under this package.",
    )
    parser.add_argument(
        "--output-dir", default="src/main/java",
        help="Source root. Default: src/main/java",
    )
    parser.add_argument(
        "--with-event", action="store_true",
        help="Also scaffold a domain event stub in events/.",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite files that already exist. Default: skip them.",
    )
    parser.add_argument(
        "--assets-dir", default=None,
        help="Override the assets directory. Defaults to ../assets/ relative to this script.",
    )
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    assets_dir = Path(args.assets_dir) if args.assets_dir else script_dir.parent / "assets"
    if not assets_dir.is_dir():
        raise SystemExit(f"Assets directory not found: {assets_dir}")

    actions = parse_actions(args.actions)
    if not actions:
        raise SystemExit("At least one action is required.")

    generate_slice(
        feature=args.feature,
        actions=actions,
        base_package=args.base_package,
        output_dir=Path(args.output_dir).resolve(),
        assets_dir=assets_dir,
        overwrite=args.overwrite,
        with_event=args.with_event,
    )


if __name__ == "__main__":
    main()
