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
{{HANDLER_IMPORTS}}, {{DTO_IMPORTS}}, {{OPENAPI_IMPORTS}}, {{PROBLEM_IMPORT}},
plus conditional import markers) that the script fills in based on which actions
were requested. Actions the user did not request are simply omitted — no dead code.

Prerequisite: the shared/ package (BaseEntity, EntityNotFoundException,
GlobalExceptionHandler) must exist — scaffold it once with init_shared.py.

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

# Allow running as a script from any CWD: the helpers module sits next to us.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _scaffold_common import (
    indefinite_article,
    substitute,
    to_camel,
    to_pascal,
    to_upper_snake,
    write_file,
)

# All actions the script knows how to scaffold. Order matters for controller
# endpoint layout (create first, then reads, then mutations, then delete).
KNOWN_ACTIONS = ("create", "list", "get", "update", "delete")

# Templates that are generated unconditionally (one per slice). The Mapper is
# NOT here: its methods/imports depend on which actions were requested, so it is
# assembled from markers by build_mapper (see generate_slice).
CORE_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("Entity.java.tmpl",           "model/{Feature}.java"),
    ("Repository.java.tmpl",       "model/{Feature}Repository.java"),
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
# Controller assembly — handled separately because it's action-driven
# ---------------------------------------------------------------------------

# OpenAPI response blocks. Deliberately %-formatted, NOT f-strings: the JSON
# example bodies are full of literal braces that f-strings would require
# doubling, and the generated Java uses text blocks (""") that would terminate
# a triple-double-quoted Python string. The blocks are interpolated into the
# endpoint f-strings as precomputed variables.

PROBLEM_TYPE_BASE = "https://api.example.com/problems/"

SUCCESS_RESPONSE_TMPL = (
    '            @ApiResponse(responseCode = "%(code)s", description = "%(description)s",\n'
    '                    content = @Content(mediaType = "application/json",\n'
    '                            schema = @Schema(implementation = %(schema)s.class))),'
)

ERROR_RESPONSE_TMPL = (
    '            @ApiResponse(responseCode = "%(code)s", description = "%(description)s",\n'
    '                    content = @Content(mediaType = "application/problem+json",\n'
    '                            schema = @Schema(implementation = ProblemDetail.class),\n'
    '                            examples = @ExampleObject(name = "%(name)s", value = """\n'
    '                                    {\n'
    '                                      "type": "%(type)s",\n'
    '                                      "title": "%(title)s",\n'
    '                                      "status": %(code)s,\n'
    '                                      "detail": "%(detail)s",\n'
    '                                      "instance": "%(instance)s"\n'
    '                                    }\n'
    '                                    """))),'
)


def success_response(code: str, description: str, schema: str) -> str:
    return SUCCESS_RESPONSE_TMPL % {"code": code, "description": description, "schema": schema}


def error_response(code: str, description: str, name: str, type_uri: str,
                   title: str, detail: str, instance: str) -> str:
    return ERROR_RESPONSE_TMPL % {
        "code": code, "description": description, "name": name,
        "type": type_uri, "title": title, "detail": detail, "instance": instance,
    }


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
    needs_problem = any(a in actions for a in ("create", "get", "update", "delete"))
    base_path = f"/api/v1/{feature_camel}s"
    article = indefinite_article(feature_camel)  # "a"/"an" for OpenAPI prose

    def err_400(instance: str) -> str:
        # Framework validation errors keep Spring's default type "about:blank".
        return error_response("400", "Validation failure", "validation-error",
                              "about:blank", "Bad Request",
                              "Invalid request content.", instance)

    def err_404(instance: str) -> str:
        return error_response("404", f"{feature_pascal} not found", "not-found",
                              PROBLEM_TYPE_BASE + "not-found", "Resource not found",
                              f"{feature_pascal} not found: id=42", instance)

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

    # Endpoint blocks. NOTE: f''' (single-quote) delimiters are required — the
    # generated @ExampleObject values are Java text blocks (""") which would
    # terminate an f-string delimited with triple double quotes. JSON-bearing
    # chunks come from the %-format constants above, interpolated as variables.
    if "create" in actions:
        ok = success_response("201", "Created", feature_pascal + "Response")
        err = err_400(base_path)
        endpoints.append(f'''    @PostMapping
    @Operation(summary = "Create a new {feature_camel}",
            description = "Creates {article} {feature_camel} from the supplied payload and returns the created resource.")
    @ApiResponses({{
{ok}
{err}
    }})
    public ResponseEntity<{feature_pascal}Response> create(@Valid @RequestBody Create{feature_pascal}Request request) {{
        log.info("Creating {feature_camel}");
        {feature_pascal}Response response = create{feature_pascal}Handler.handle(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }}''')
    if "list" in actions:
        # Page<T> success deliberately has no explicit content: springdoc infers
        # the generic type; @Schema(implementation = Page.class) would erase it.
        endpoints.append(f'''    @GetMapping
    @Operation(summary = "List {feature_camel}s with pagination",
            description = "Returns a page of {feature_camel}s. Page, size and sort come from standard Pageable query parameters.")
    @ApiResponses({{
            @ApiResponse(responseCode = "200", description = "Page of {feature_camel}s"),
    }})
    public Page<{feature_pascal}Response> list(Pageable pageable) {{
        return list{feature_pascal}Handler.handle(pageable);
    }}''')
    if "get" in actions:
        ok = success_response("200", "Found", feature_pascal + "Response")
        err = err_404(base_path + "/42")
        endpoints.append(f'''    @GetMapping("/{{id}}")
    @Operation(summary = "Get {article} {feature_camel} by id",
            description = "Returns the {feature_camel} with the given id, or an RFC 9457 problem response if it does not exist.")
    @ApiResponses({{
{ok}
{err}
    }})
    public {feature_pascal}Response get(@PathVariable Long id) {{
        return get{feature_pascal}Handler.handle(id);
    }}''')
    if "update" in actions:
        ok = success_response("200", "Updated", feature_pascal + "Response")
        err400 = err_400(base_path + "/42")
        err404 = err_404(base_path + "/42")
        endpoints.append(f'''    @PutMapping("/{{id}}")
    @Operation(summary = "Update {article} {feature_camel}",
            description = "Applies the supplied payload to the {feature_camel} with the given id and returns the updated resource.")
    @ApiResponses({{
{ok}
{err400}
{err404}
    }})
    public {feature_pascal}Response update(@PathVariable Long id, @Valid @RequestBody Update{feature_pascal}Request request) {{
        log.info("Updating {feature_camel} id={{}}", id);
        return update{feature_pascal}Handler.handle(id, request);
    }}''')
    if "delete" in actions:
        err = err_404(base_path + "/42")
        endpoints.append(f'''    @DeleteMapping("/{{id}}")
    @Operation(summary = "Delete {article} {feature_camel}",
            description = "Deletes the {feature_camel} with the given id. Returns an RFC 9457 problem response if it does not exist.")
    @ApiResponses({{
            @ApiResponse(responseCode = "204", description = "Deleted"),
{err}
    }})
    public ResponseEntity<Void> delete(@PathVariable Long id) {{
        log.info("Deleting {feature_camel} id={{}}", id);
        delete{feature_pascal}Handler.handle(id);
        return ResponseEntity.noContent().build();
    }}''')

    # Conditional imports.
    page_import_lines = []
    if needs_page:
        page_import_lines.append("import org.springframework.data.domain.Page;")
        page_import_lines.append("import org.springframework.data.domain.Pageable;")
    valid_import = "import jakarta.validation.Valid;" if needs_valid else ""
    http_status_import = "import org.springframework.http.HttpStatus;" if "create" in actions else ""

    openapi_imports = ["import io.swagger.v3.oas.annotations.Operation;"]
    if needs_problem:
        openapi_imports += [
            "import io.swagger.v3.oas.annotations.media.Content;",
            "import io.swagger.v3.oas.annotations.media.ExampleObject;",
            "import io.swagger.v3.oas.annotations.media.Schema;",
        ]
    openapi_imports += [
        "import io.swagger.v3.oas.annotations.responses.ApiResponse;",
        "import io.swagger.v3.oas.annotations.responses.ApiResponses;",
        "import io.swagger.v3.oas.annotations.tags.Tag;",
    ]
    problem_import = "import org.springframework.http.ProblemDetail;" if needs_problem else ""

    result = (
        template_text
        .replace("{{HANDLER_IMPORTS}}", "\n".join(handler_imports))
        .replace("{{DTO_IMPORTS}}",     "\n".join(dto_imports))
        .replace("{{OPENAPI_IMPORTS}}", "\n".join(openapi_imports))
        .replace("{{HANDLER_FIELDS}}",  "\n".join(handler_fields))
        .replace("{{ENDPOINTS}}",       "\n\n".join(endpoints))
        .replace("{{VALID_IMPORT}}",    valid_import)
        .replace("{{PAGE_IMPORT}}",     "\n".join(page_import_lines))
        .replace("{{HTTP_STATUS_IMPORT}}", http_status_import)
        .replace("{{PROBLEM_IMPORT}}",  problem_import)
    )
    # Collapse the blank-line runs left behind by empty conditional markers.
    return re.sub(r"\n{3,}", "\n\n", result)


# ---------------------------------------------------------------------------
# Mapper assembly — action-driven, because toEntity/applyUpdate depend on the
# Create/Update request DTOs, which are only generated for those actions.
# ---------------------------------------------------------------------------

def build_mapper(
    feature_pascal: str,
    feature_camel: str,
    base_package: str,
    actions: list[str],
    template_text: str,
) -> str:
    """Fill in the Mapper template, including only the methods (and their request
    DTO imports) for the requested actions. toResponse is always present."""
    imports: list[str] = []
    methods: list[str] = []

    if "create" in actions:
        imports.append(
            f"import {base_package}.features.{feature_camel}.api.request.Create{feature_pascal}Request;"
        )
        methods.append(f"""    public {feature_pascal} toEntity(Create{feature_pascal}Request request) {{
        return {feature_pascal}.builder()
                .name(request.name())
                // TODO: map remaining fields from the request record
                .build();
    }}""")
    if "update" in actions:
        imports.append(
            f"import {base_package}.features.{feature_camel}.api.request.Update{feature_pascal}Request;"
        )
        methods.append(f"""    public void applyUpdate({feature_pascal} entity, Update{feature_pascal}Request request) {{
        entity.setName(request.name());
        // TODO: apply remaining updates from the request record to the entity
    }}""")

    # toResponse is always emitted, so its Response import is always needed.
    imports.append(
        f"import {base_package}.features.{feature_camel}.api.response.{feature_pascal}Response;"
    )

    result = (
        template_text
        .replace("{{MAPPER_IMPORTS}}", "\n".join(imports))
        # Trailing blank line keeps one gap before the always-present toResponse.
        .replace("{{MAPPER_METHODS}}", ("\n\n".join(methods) + "\n\n") if methods else "")
    )
    return re.sub(r"\n{3,}", "\n\n", result)


# ---------------------------------------------------------------------------
# Placeholder substitution
# ---------------------------------------------------------------------------

def substitute_slice(text: str, feature: str, base_package: str) -> str:
    return substitute(text, {
        "BasePackage": base_package,
        "Feature": to_pascal(feature),
        "FEATURE": to_upper_snake(feature),
        "feature": to_camel(feature),
    })


# ---------------------------------------------------------------------------
# Slice generation
# ---------------------------------------------------------------------------

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

    # Slices depend on shared/ infrastructure that init_shared.py scaffolds.
    shared_base = output_dir / Path(*base_package.split(".")) / "shared" / "entity" / "BaseEntity.java"
    if not shared_base.exists():
        print("WARNING: shared/entity/BaseEntity.java not found under the base package.")
        print("         Run scripts/init_shared.py first - the slice entity extends BaseEntity and")
        print(f"         {feature_pascal}NotFoundException extends the shared EntityNotFoundException.")
        print()

    written = 0
    skipped = 0

    # 1. Core templates (always generated).
    for template_name, dest_pattern in CORE_TEMPLATES:
        dest = slice_root / dest_pattern.format(Feature=feature_pascal)
        template_text = (assets_dir / template_name).read_text(encoding="utf-8")
        content = substitute_slice(template_text, feature, base_package)
        if write_file(dest, content, overwrite):
            written += 1
        else:
            skipped += 1

    # 2. Action-specific templates.
    for action in actions:
        for template_name, dest_pattern in ACTION_TEMPLATES[action]:
            dest = slice_root / dest_pattern.format(Feature=feature_pascal)
            template_text = (assets_dir / template_name).read_text(encoding="utf-8")
            content = substitute_slice(template_text, feature, base_package)
            if write_file(dest, content, overwrite):
                written += 1
            else:
                skipped += 1

    # 3. Mapper — built programmatically from markers (action-dependent methods).
    mapper_dest = slice_root / "model" / f"{feature_pascal}Mapper.java"
    mapper_template = (assets_dir / "Mapper.java.tmpl").read_text(encoding="utf-8")
    mapper_content = build_mapper(
        feature_pascal=feature_pascal,
        feature_camel=feature_camel,
        base_package=base_package,
        actions=actions,
        template_text=mapper_template,
    )
    mapper_content = substitute_slice(mapper_content, feature, base_package)
    if write_file(mapper_dest, mapper_content, overwrite):
        written += 1
    else:
        skipped += 1

    # 4. Controller — built programmatically from markers.
    controller_dest = slice_root / "api" / f"{feature_pascal}Controller.java"
    controller_template = (assets_dir / "Controller.java.tmpl").read_text(encoding="utf-8")
    controller_content = build_controller(
        feature_pascal=feature_pascal,
        feature_camel=feature_camel,
        base_package=base_package,
        actions=actions,
        template_text=controller_template,
    )
    controller_content = substitute_slice(controller_content, feature, base_package)
    if write_file(controller_dest, controller_content, overwrite):
        written += 1
    else:
        skipped += 1

    # 5. Optional domain event.
    if with_event:
        event_dest = slice_root / "events" / f"{feature_pascal}ChangedEvent.java"
        template_text = (assets_dir / "Event.java.tmpl").read_text(encoding="utf-8")
        content = substitute_slice(template_text, feature, base_package)
        if write_file(event_dest, content, overwrite):
            written += 1
        else:
            skipped += 1

    print(f"\nDone. {written} file(s) written, {skipped} skipped.")
    print("Next steps:")
    print("  1. If shared/ does not exist yet, run scripts/init_shared.py (BaseEntity,")
    print("     EntityNotFoundException and GlobalExceptionHandler are required to compile)")
    print(f"  2. Fill in real domain fields on {feature_pascal} entity")
    print("  3. Adjust Request/Response record components - keep @Schema(description, example)")
    print("     on every field")
    print("  4. Replace the TODO comments in the mapper with real mappings")
    print("  5. Review @RequestMapping prefix, @Table name, and the ProblemDetail example")
    print("     'instance' paths if you changed the API prefix")


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
             "Default: all five CRUD actions. Order is ignored — files and "
             "controller endpoints are always generated in this canonical order.",
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
