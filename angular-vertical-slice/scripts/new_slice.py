#!/usr/bin/env python3
"""Stamp a vertical slice skeleton for an Angular app.

Creates the data layer (models + service + service spec), the slice-root error map, and one folder
per component (ts + html + spec), then prints the route and nav snippets to paste by hand — those
two files are hand-ordered and must not be machine-edited.

Existing files are never overwritten; they are reported as skipped.

Example:
    python new_slice.py --domain care-settings --singular care-setting \
        --base-path /admin/care-settings \
        --components care-setting-list,care-setting-editor

Then fill in the bodies. See ../references/scaffold.md for the fully worked versions.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

# --------------------------------------------------------------------------------------
# naming
# --------------------------------------------------------------------------------------


def pascal(kebab: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in kebab.split("-") if part)


def upper_snake(kebab: str) -> str:
    return kebab.replace("-", "_").upper()


def humanize(kebab: str) -> str:
    words = kebab.split("-")
    return " ".join([words[0].capitalize()] + words[1:])


def singularize(domain: str) -> str:
    """Best-effort singular of a kebab domain; --singular overrides it."""
    head, _, last = domain.rpartition("-")
    if last.endswith("ies") and len(last) > 3:
        last = last[:-3] + "y"
    elif last.endswith("ses") or last.endswith("xes") or last.endswith("ches"):
        last = last[:-2]
    elif last.endswith("s") and not last.endswith("ss"):
        last = last[:-1]
    return f"{head}-{last}" if head else last


KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def check_kebab(value: str, label: str) -> str:
    if not KEBAB.match(value):
        sys.exit(f"error: --{label} must be kebab-case (got {value!r})")
    return value


# --------------------------------------------------------------------------------------
# templates — placeholders are __TOKEN__ so TS template literals (${...}) survive untouched
# --------------------------------------------------------------------------------------

MODELS = """/** Exact word the user must type (and the API must receive) to delete a __TITLE_LOWER__. */
export const __CONST___DELETE_CONFIRMATION = 'DELETED';

/** __TITLE__ DTOs mirroring the backend contract (see __BASE_PATH__). */

export interface __ENTITY__Response {
  id: string;
  name: string;
  /** Null when left blank by the author — distinct from an absent field. */
  description: string | null;
  archived: boolean;
  displayOrder: number;
}

export interface Create__ENTITY__Request {
  name: string;
  description?: string | null;
  /** Create it archived. Omit/false for an active record. */
  archived?: boolean;
}

/** Partial update — omit a field to leave it unchanged. Send `archived` to archive/restore. */
export interface Update__ENTITY__Request {
  name?: string;
  description?: string | null;
  archived?: boolean;
}
"""

SERVICE = """import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Create__ENTITY__Request, __ENTITY__Response, Update__ENTITY__Request } from './__SINGULAR__.models';

/**
 * __TITLE__ management (`__BASE_PATH__`). Powers the __TITLE_LOWER__ screens: the directory and the
 * editor's create / edit / archive-restore / delete actions.
 *
 * Stateless by design — the container component owns the loaded list, so two screens cannot silently
 * share and corrupt one cache.
 */
@Injectable({ providedIn: 'root' })
export class __DOMAIN_PASCAL__Service {
  private readonly http = inject(HttpClient);
  private static readonly BASE = '__BASE_PATH__';

  list(): Observable<__ENTITY__Response[]> {
    return this.http.get<__ENTITY__Response[]>(__DOMAIN_PASCAL__Service.BASE);
  }

  get(id: string): Observable<__ENTITY__Response> {
    return this.http.get<__ENTITY__Response>(`${__DOMAIN_PASCAL__Service.BASE}/${id}`);
  }

  create(body: Create__ENTITY__Request): Observable<__ENTITY__Response> {
    return this.http.post<__ENTITY__Response>(__DOMAIN_PASCAL__Service.BASE, body);
  }

  update(id: string, body: Update__ENTITY__Request): Observable<__ENTITY__Response> {
    return this.http.patch<__ENTITY__Response>(`${__DOMAIN_PASCAL__Service.BASE}/${id}`, body);
  }

  /**
   * Hard-delete. Pass the confirmation word — the server rejects a bare delete with 409
   * `__SINGULAR__-delete-confirmation-required`, and an in-use record with 409 `__SINGULAR__-in-use`.
   */
  delete(id: string, confirmation?: string): Observable<void> {
    let params = new HttpParams();
    if (confirmation) {
      params = params.set('confirmation', confirmation);
    }
    return this.http.delete<void>(`${__DOMAIN_PASCAL__Service.BASE}/${id}`, { params });
  }
}
"""

SERVICE_SPEC = """import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { __DOMAIN_PASCAL__Service } from './__DOMAIN__.service';

describe('__DOMAIN_PASCAL__Service', () => {
  let service: __DOMAIN_PASCAL__Service;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(__DOMAIN_PASCAL__Service);
    httpMock = TestBed.inject(HttpTestingController);
  });

  // Fails the spec if the code fired a request it did not declare — the usual refetch bug.
  afterEach(() => httpMock.verify());

  it('lists __TITLE_LOWER__', () => {
    service.list().subscribe();
    const req = httpMock.expectOne('__BASE_PATH__');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('creates a __SINGULAR_HUMAN__', () => {
    service.create({ name: 'Example' }).subscribe();
    const req = httpMock.expectOne('__BASE_PATH__');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Example' });
    req.flush({});
  });

  it('updates a __SINGULAR_HUMAN__', () => {
    service.update('id-1', { name: 'Renamed' }).subscribe();
    const req = httpMock.expectOne('__BASE_PATH__/id-1');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ name: 'Renamed' });
    req.flush({});
  });

  it('sends the confirmation word when deleting', () => {
    service.delete('id-1', 'DELETED').subscribe();
    const req = httpMock.expectOne((r) => r.url === '__BASE_PATH__/id-1');
    expect(req.request.method).toBe('DELETE');
    expect(req.request.params.get('confirmation')).toBe('DELETED');
    req.flush(null);
  });
});
"""

ERRORS = """/**
 * Friendly messages for __TITLE_LOWER__ errors, keyed on the RFC 9457 problem `type` slug (the last
 * path segment of `type`). The slug is a stable contract; `detail` is prose and must not be matched on.
 *
 * Deliberately omit a slug whose server `detail` names the specific row or file that blocked the
 * action — replacing that with a generic sentence throws away the only clue the user has. Say so in a
 * comment when you do, or someone will "complete" the map later.
 */
export const __CONST___ERROR_MESSAGES: Readonly<Record<string, string>> = {
  'duplicate-__SINGULAR__': 'A __SINGULAR_HUMAN__ with that name already exists.',
  '__SINGULAR__-in-use': 'This __SINGULAR_HUMAN__ is in use and cannot be deleted. Archive it instead.',
  '__SINGULAR__-already-first': 'This __SINGULAR_HUMAN__ is already first.',
  '__SINGULAR__-already-last': 'This __SINGULAR_HUMAN__ is already last.',
  '__SINGULAR__-delete-confirmation-required': 'Type DELETED to confirm deletion.',
};
"""

CONTAINER = """import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable } from 'rxjs';

import { __ENTITY__Response } from '__CORE_PATH__/__SINGULAR__.models';
import { __DOMAIN_PASCAL__Service } from '__CORE_PATH__/__DOMAIN__.service';
import { problemMessage } from '__CORE_ROOT__/http/problem-message';
import { __CONST___ERROR_MESSAGES } from '../__SINGULAR__-errors';

/** Directory status filter. */
type StatusFilter = 'all' | 'active' | 'archived';

/**
 * __TITLE__ directory. Owns the fetch, the filters, and the error banner; presentational children take
 * inputs and report back through outputs so there is exactly one place that talks to the service.
 *
 * TODO: describe what this screen is for and how it is reached, then delete this line.
 */
@Component({
  selector: 'app-__COMP__',
  imports: [],
  templateUrl: './__COMP__.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class __COMP_CLASS__ implements OnInit {
  private readonly service = inject(__DOMAIN_PASCAL__Service);
  private readonly destroyRef = inject(DestroyRef);

  readonly items = signal<__ENTITY__Response[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly query = signal('');
  readonly statusFilter = signal<StatusFilter>('all');
  /** Id of the row whose action is in flight, so only that row's controls disable. */
  readonly actionInFlight = signal<string | null>(null);

  readonly filtered = computed<readonly __ENTITY__Response[]>(() => {
    const status = this.statusFilter();
    const q = this.query().trim().toLowerCase();
    return this.items().filter((item) => {
      if (status === 'active' && item.archived) {
        return false;
      }
      if (status === 'archived' && !item.archived) {
        return false;
      }
      if (!q) {
        return true;
      }
      return (
        item.name.toLowerCase().includes(q) ||
        (item.description?.toLowerCase().includes(q) ?? false)
      );
    });
  });

  ngOnInit(): void {
    this.load();
  }

  refresh(): void {
    this.load();
  }

  onSearch(value: string): void {
    this.query.set(value);
  }

  setStatusFilter(status: StatusFilter): void {
    this.statusFilter.set(status);
  }

  private load(): void {
    this.loading.set(true);
    // Cleared at the START of the request: otherwise a stale banner outlives the failure it described.
    this.error.set(null);
    this.service
      .list()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (items) => {
          this.items.set(items);
          this.loading.set(false);
        },
        error: (err: unknown) => {
          this.error.set(problemMessage(err, 'Failed to load __TITLE_LOWER__.'));
          // Also on the error path — a spinner that survives a failure is the classic bug here.
          this.loading.set(false);
        },
      });
  }

  /** One shape for every single-record action, so in-flight state and error handling cannot drift. */
  protected runAction(id: string, request$: Observable<unknown>, fallback: string): void {
    this.actionInFlight.set(id);
    this.error.set(null);
    request$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.actionInFlight.set(null);
        this.load();
      },
      error: (err: unknown) => {
        this.actionInFlight.set(null);
        this.error.set(problemMessage(err, fallback, __CONST___ERROR_MESSAGES));
      },
    });
  }
}
"""

CONTAINER_HTML = """@if (error(); as message) {
  <div role="alert" class="alert alert-error mb-4">{{ message }}</div>
}

<div class="mb-4 flex gap-2">
  <input
    type="search"
    class="input input-bordered"
    placeholder="Search __TITLE_LOWER__"
    aria-label="Search __TITLE_LOWER__"
    [value]="query()"
    (input)="onSearch($any($event.target).value)"
  />
</div>

@if (loading() && items().length === 0) {
  <!-- Spinner only on the FIRST load; a refetch keeps existing rows on screen. -->
  <div class="flex justify-center py-10">
    <span class="loading loading-spinner" aria-label="Loading __TITLE_LOWER__"></span>
  </div>
} @else if (filtered().length === 0) {
  <p class="py-10 text-center">No __TITLE_LOWER__ match your filters.</p>
} @else {
  <table class="table">
    <thead>
      <tr>
        <th scope="col">Name</th>
        <th scope="col">Status</th>
      </tr>
    </thead>
    <tbody>
      <!-- track on a stable id: tracking by index re-renders every row on a reorder and loses focus. -->
      @for (item of filtered(); track item.id) {
        <tr>
          <td>{{ item.name }}</td>
          <td>{{ item.archived ? 'Archived' : 'Active' }}</td>
        </tr>
      }
    </tbody>
  </table>
}
"""

PRESENTER = """import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import { __ENTITY__Response } from '__CORE_PATH__/__SINGULAR__.models';

/**
 * TODO: say what this renders and how the container drives it, then delete this line.
 *
 * Presentational: takes what it renders through `input()` and reports every outcome through `output()`,
 * so the container remains the only place that decides what happens next.
 */
@Component({
  selector: 'app-__COMP__',
  imports: [],
  templateUrl: './__COMP__.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class __COMP_CLASS__ {
  readonly item = input.required<__ENTITY__Response>();
  readonly busy = input(false);

  /** Emitted when the user asks to edit this record — the container opens its editor. */
  readonly editRequested = output<__ENTITY__Response>();
  /** Emitted when the user asks to delete this record — the container confirms, then deletes. */
  readonly deleteRequested = output<__ENTITY__Response>();

  readonly statusLabel = computed(() => (this.item().archived ? 'Archived' : 'Active'));

  edit(): void {
    this.editRequested.emit(this.item());
  }

  requestDelete(): void {
    if (!this.busy()) {
      this.deleteRequested.emit(this.item());
    }
  }
}
"""

PRESENTER_HTML = """<div class="flex items-center justify-between gap-2">
  <span>{{ item().name }}</span>
  <span class="badge">{{ statusLabel() }}</span>

  <!-- Repeated row controls need a distinguishing accessible name, or every row reads as "Edit". -->
  <button type="button" class="btn btn-sm" [disabled]="busy()" (click)="edit()">
    Edit<span class="sr-only"> {{ item().name }}</span>
  </button>
  <button type="button" class="btn btn-sm btn-error" [disabled]="busy()" (click)="requestDelete()">
    Delete<span class="sr-only"> {{ item().name }}</span>
  </button>
</div>
"""

CONTAINER_SPEC = """import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { __ENTITY__Response } from '__CORE_PATH__/__SINGULAR__.models';
import { __COMP_CLASS__ } from './__COMP__';

const ITEMS: __ENTITY__Response[] = [
  {
    id: 'id-1',
    name: 'First record',
    description: 'A description.',
    archived: false,
    displayOrder: 0,
  },
  { id: 'id-2', name: 'Second record', description: null, archived: true, displayOrder: 1 },
];

describe('__COMP_CLASS__', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [__COMP_CLASS__],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  /** Render and satisfy the initial load, so every test starts from a known state. */
  function create(): { fixture: ComponentFixture<__COMP_CLASS__>; cmp: __COMP_CLASS__ } {
    const fixture = TestBed.createComponent(__COMP_CLASS__);
    fixture.detectChanges(); // ngOnInit -> load
    httpMock.expectOne('__BASE_PATH__').flush(ITEMS);
    fixture.detectChanges();
    return { fixture, cmp: fixture.componentInstance };
  }

  function text(fixture: ComponentFixture<__COMP_CLASS__>): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  it('renders the loaded rows', () => {
    const { fixture } = create();
    expect(text(fixture)).toContain('First record');
    expect(text(fixture)).toContain('Second record');
  });

  it('filters the directory by search text', () => {
    const { fixture, cmp } = create();
    cmp.onSearch('second');
    fixture.detectChanges();
    expect(text(fixture)).not.toContain('First record');
    expect(text(fixture)).toContain('Second record');
  });

  it('surfaces a mapped server error and stops the spinner', () => {
    const fixture = TestBed.createComponent(__COMP_CLASS__);
    fixture.detectChanges();
    httpMock
      .expectOne('__BASE_PATH__')
      .flush(
        { type: 'https://example.test/problems/__SINGULAR__-in-use', detail: 'ignored' },
        { status: 409, statusText: 'Conflict' },
      );
    fixture.detectChanges();
    expect(fixture.componentInstance.loading()).toBe(false);
    expect(fixture.componentInstance.error()).not.toBeNull();
  });

  it('keeps existing rows visible while refetching', () => {
    const { fixture, cmp } = create();
    cmp.refresh();
    fixture.detectChanges();
    expect(text(fixture)).toContain('First record');
    httpMock.expectOne('__BASE_PATH__').flush(ITEMS);
  });
});
"""

PRESENTER_SPEC = """import { ComponentFixture, TestBed } from '@angular/core/testing';

import { __ENTITY__Response } from '__CORE_PATH__/__SINGULAR__.models';
import { __COMP_CLASS__ } from './__COMP__';

const ITEM: __ENTITY__Response = {
  id: 'id-1',
  name: 'First record',
  description: 'A description.',
  archived: false,
  displayOrder: 0,
};

describe('__COMP_CLASS__', () => {
  let fixture: ComponentFixture<__COMP_CLASS__>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [__COMP_CLASS__] }).compileComponents();
    fixture = TestBed.createComponent(__COMP_CLASS__);
    fixture.componentRef.setInput('item', ITEM);
    fixture.detectChanges();
  });

  function button(name: string): HTMLButtonElement {
    const match = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('button'),
    ).find((b) => (b.getAttribute('aria-label') ?? b.textContent ?? '').includes(name));
    if (!match) {
      throw new Error(`No button matching "${name}"`);
    }
    return match as HTMLButtonElement;
  }

  it('renders the record name and status', () => {
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('First record');
    expect(text).toContain('Active');
  });

  it('emits the record when edit is pressed', () => {
    let emitted: __ENTITY__Response | undefined;
    fixture.componentInstance.editRequested.subscribe((v) => (emitted = v));
    button('Edit').click();
    expect(emitted).toEqual(ITEM);
  });

  it('does not emit a delete while busy', () => {
    fixture.componentRef.setInput('busy', true);
    fixture.detectChanges();
    let emitted = false;
    fixture.componentInstance.deleteRequested.subscribe(() => (emitted = true));
    fixture.componentInstance.requestDelete();
    expect(emitted).toBe(false);
  });
});
"""

CONTAINER_SUFFIXES = ("-list", "-page", "-workspace", "-shell", "-directory", "-overview")


# --------------------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------------------


def render(template: str, tokens: dict[str, str]) -> str:
    out = template
    for key, value in tokens.items():
        out = out.replace(key, value)
    return out


def write(path: str, content: str, dry_run: bool, created: list[str], skipped: list[str]) -> None:
    if os.path.exists(path):
        skipped.append(path)
        return
    created.append(path)
    if dry_run:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def detect_root() -> str | None:
    for candidate in ("src/app", "frontend/src/app", "../src/app"):
        if os.path.isdir(candidate):
            return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--domain", required=True, help="kebab-case plural domain, e.g. care-settings")
    parser.add_argument("--singular", help="kebab-case singular, e.g. care-setting (inferred if omitted)")
    parser.add_argument("--base-path", help="API base path, e.g. /admin/care-settings")
    parser.add_argument(
        "--components",
        help="comma-separated component names. The first, or any ending in -list/-page/-workspace/"
        "-shell/-directory/-overview, is generated as the container.",
    )
    parser.add_argument("--root", help="Angular app root (default: auto-detect src/app)")
    parser.add_argument(
        "--data-dir",
        choices=("core", "features"),
        default="core",
        help="where the service and models go (default: core)",
    )
    parser.add_argument("--dry-run", action="store_true", help="list files without writing them")
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="skip running Prettier over the newly created files (it is never run over existing ones)",
    )
    args = parser.parse_args()

    domain = check_kebab(args.domain, "domain")
    singular = check_kebab(args.singular or singularize(domain), "singular")
    base_path = args.base_path or f"/admin/{domain}"
    root = args.root or detect_root()
    if not root:
        return fail("could not find the Angular app root; pass --root (e.g. --root frontend/src/app)")
    if not os.path.isdir(root):
        return fail(f"--root {root!r} is not a directory")

    components = [check_kebab(c.strip(), "components") for c in (args.components or f"{singular}-list").split(",") if c.strip()]

    feature_dir = os.path.join(root, "features", domain)
    data_dir = os.path.join(root, args.data_dir, domain)
    # Relative import from features/<domain>/<component>/ back to the data layer and to core/.
    core_path = f"../../../{args.data_dir}/{domain}" if args.data_dir == "core" else ".."
    core_root = "../../../core"

    tokens = {
        "__DOMAIN__": domain,
        "__DOMAIN_PASCAL__": pascal(domain),
        "__SINGULAR__": singular,
        "__ENTITY__": pascal(singular),
        "__CONST__": upper_snake(singular),
        "__BASE_PATH__": base_path,
        "__TITLE__": humanize(domain),
        "__TITLE_LOWER__": humanize(domain).lower(),
        "__SINGULAR_HUMAN__": humanize(singular).lower(),
        "__CORE_PATH__": core_path,
        "__CORE_ROOT__": core_root,
    }

    created: list[str] = []
    skipped: list[str] = []

    write(os.path.join(data_dir, f"{singular}.models.ts"), render(MODELS, tokens), args.dry_run, created, skipped)
    write(os.path.join(data_dir, f"{domain}.service.ts"), render(SERVICE, tokens), args.dry_run, created, skipped)
    write(os.path.join(data_dir, f"{domain}.service.spec.ts"), render(SERVICE_SPEC, tokens), args.dry_run, created, skipped)
    write(os.path.join(feature_dir, f"{singular}-errors.ts"), render(ERRORS, tokens), args.dry_run, created, skipped)

    container_assigned = False
    for index, comp in enumerate(components):
        is_container = comp.endswith(CONTAINER_SUFFIXES) or (index == 0 and not any(c.endswith(CONTAINER_SUFFIXES) for c in components))
        if is_container and container_assigned:
            is_container = False
        container_assigned = container_assigned or is_container

        comp_tokens = dict(tokens, __COMP__=comp, __COMP_CLASS__=pascal(comp))
        comp_dir = os.path.join(feature_dir, comp)
        body, html, spec = (
            (CONTAINER, CONTAINER_HTML, CONTAINER_SPEC) if is_container else (PRESENTER, PRESENTER_HTML, PRESENTER_SPEC)
        )
        write(os.path.join(comp_dir, f"{comp}.ts"), render(body, comp_tokens), args.dry_run, created, skipped)
        write(os.path.join(comp_dir, f"{comp}.html"), render(html, comp_tokens), args.dry_run, created, skipped)
        write(os.path.join(comp_dir, f"{comp}.spec.ts"), render(spec, comp_tokens), args.dry_run, created, skipped)

    report(created, skipped, args.dry_run)
    if created and not args.dry_run and not args.no_format:
        format_files(created)
    print_snippets(domain, components, tokens)
    return 0


def format_files(paths: list[str]) -> None:
    """Prettier-format the files this run created.

    Line wrapping depends on how long the generated identifiers turn out to be, so a template that is
    clean for one domain name overflows for another. Only newly created files are passed — an existing
    file is never reformatted, because a repo-wide reformat buried in a scaffold command is a nasty
    surprise in a diff.
    """
    npx = shutil.which("npx")
    if not npx:
        print("\nnpx not found — skipping formatting. Run Prettier over the new files yourself.")
        return
    try:
        result = subprocess.run(
            [npx, "--no-install", "prettier", "--write", *paths],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"\nFormatting skipped ({exc}). Run Prettier over the new files yourself.")
        return
    if result.returncode == 0:
        print(f"\nFormatted {len(paths)} new file(s) with Prettier.")
    else:
        print("\nPrettier did not run cleanly; the files are written but unformatted.")
        if result.stderr.strip():
            print(result.stderr.strip().splitlines()[0])


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def report(created: list[str], skipped: list[str], dry_run: bool) -> None:
    verb = "Would create" if dry_run else "Created"
    print(f"{verb} {len(created)} file(s):")
    for path in created:
        print(f"  {path}")
    if skipped:
        print(f"\nSkipped {len(skipped)} existing file(s) — nothing was overwritten:")
        for path in skipped:
            print(f"  {path}")


def print_snippets(domain: str, components: list[str], tokens: dict[str, str]) -> None:
    container = next((c for c in components if c.endswith(CONTAINER_SUFFIXES)), components[0])
    title = tokens["__TITLE__"]
    print("\n--- paste into app.routes.ts (hand-ordered; not machine-edited) ---")
    print(
        f"""{{
  path: 'admin/{domain}',
  title: '{title}',
  canActivate: [adminGuard],
  loadComponent: () =>
    import('./features/{domain}/{container}/{container}').then((m) => m.{pascal(container)}),
}},"""
    )
    print("\n--- paste into the sidebar registry (declare the group explicitly) ---")
    print(f"{{ label: '{title}', icon: 'category', path: '/admin/{domain}', group: 'program-setup' }},")
    print("\nNext: fill in the DTOs from the API contract, then the service methods, then the UI.")
    print("See ../references/scaffold.md for the fully worked versions of each file.")


if __name__ == "__main__":
    raise SystemExit(main())
