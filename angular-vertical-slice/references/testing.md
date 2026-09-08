# Testing reference

Every file kind in a slice has a matching spec kind. Read this before writing any spec.

## Contents

- [What tests what](#what-tests-what)
- [Service specs](#service-specs)
- [Component specs](#component-specs)
- [Fixture builders](#fixture-builders)
- [Helper specs](#helper-specs)
- [E2E](#e2e)
- [Common failures](#common-failures)

## What tests what

| Layer | Tool | Scope | Rule |
|---|---|---|---|
| Service | TestBed + `HttpTestingController` | Method, URL, params, body per endpoint | No DOM |
| Slice-root helper | Plain unit spec | Pure function branches | No TestBed needed |
| Component | TestBed + `HttpTestingController`, queried through the DOM | Rendering, interaction, state transitions | Query by role/label/text, never by CSS class |
| Journey | Playwright | Multi-step flows across screens | Only critical paths |

The pyramid matters here because a vertical slice makes it tempting to test everything through the
container: it renders, it fetches, it filters, it deletes. Resist. A filter predicate tested directly
takes a millisecond and pins one rule; the same rule tested through a rendered table takes a fixture,
a flush, and two `detectChanges` calls, and fails for six unrelated reasons.

## Service specs

`core/<domain>/<domain>.service.spec.ts` — one `it` per endpoint, asserting method, URL, and body.
This is the cheapest test in the slice and the one that catches a contract drift first.

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { CareSettingsService } from './care-settings.service';

describe('CareSettingsService', () => {
  let service: CareSettingsService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CareSettingsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lists care settings', () => {
    service.list().subscribe();
    const req = httpMock.expectOne('/admin/care-settings');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('creates a care setting', () => {
    service.create({ name: 'Community outreach' }).subscribe();
    const req = httpMock.expectOne('/admin/care-settings');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Community outreach' });
    req.flush({});
  });

  it('sends the confirmation word when deleting', () => {
    service.delete('c1', 'DELETED').subscribe();
    const req = httpMock.expectOne((r) => r.url === '/admin/care-settings/c1');
    expect(req.request.method).toBe('DELETE');
    expect(req.request.params.get('confirmation')).toBe('DELETED');
    req.flush(null);
  });
});
```

`afterEach(() => httpMock.verify())` is not optional. It is what turns "the component fired an extra
request I did not expect" from a silent pass into a failure, which is exactly the bug class that
refetch logic produces.

Flushing `{}` where the body is irrelevant keeps the spec about the request. Only build a realistic
response when the assertion depends on it.

## Component specs

Query the DOM the way a user perceives it: by role, accessible name, and visible text. A spec that
queries `.fm-card__title` breaks the moment someone renames a class and passes even when the heading
has lost its semantics — it tests the stylesheet, not the screen.

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CareSettingResponse } from '../../../core/care-settings/care-setting.models';
import { CareSettingList } from './care-setting-list';

const CARE_SETTINGS: CareSettingResponse[] = [
  { id: 'c1', name: 'Ambulatory clinic', description: 'Office visits.', archived: false, displayOrder: 0, isDefault: true, entries: 28 },
  { id: 'c2', name: 'Telehealth', description: null, archived: true, displayOrder: 1, isDefault: false, entries: 0 },
];

describe('CareSettingList', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    // jsdom implements neither; a component that opens a <dialog> throws without these.
    HTMLDialogElement.prototype.showModal = (): void => undefined;
    HTMLDialogElement.prototype.close = (): void => undefined;

    await TestBed.configureTestingModule({
      imports: [CareSettingList],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  /** One helper that renders and satisfies the initial load, so each test starts at a known state. */
  function create(): { fixture: ComponentFixture<CareSettingList>; cmp: CareSettingList } {
    const fixture = TestBed.createComponent(CareSettingList);
    fixture.detectChanges(); // ngOnInit -> load
    httpMock.expectOne('/admin/care-settings').flush(CARE_SETTINGS);
    fixture.detectChanges();
    return { fixture, cmp: fixture.componentInstance };
  }

  function text(fixture: ComponentFixture<CareSettingList>): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function button(fixture: ComponentFixture<CareSettingList>, name: string): HTMLButtonElement {
    const match = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('button'),
    ).find((b) => (b.getAttribute('aria-label') ?? b.textContent ?? '').trim().includes(name));
    if (!match) {
      throw new Error(`No button matching "${name}"`);
    }
    return match as HTMLButtonElement;
  }

  it('renders the loaded rows', () => {
    const { fixture } = create();
    expect(text(fixture)).toContain('Ambulatory clinic');
    expect(text(fixture)).toContain('Telehealth');
  });

  it('filters the directory by search text', () => {
    const { fixture, cmp } = create();
    cmp.query.set('tele');
    fixture.detectChanges();
    expect(text(fixture)).not.toContain('Ambulatory clinic');
    expect(text(fixture)).toContain('Telehealth');
  });

  it('shows the mapped message when the server rejects a delete', () => {
    const { fixture, cmp } = create();
    cmp.onDeleteRequested(CARE_SETTINGS[0]);
    cmp.confirmDelete();
    httpMock.expectOne((r) => r.url === '/admin/care-settings/c1').flush(
      { type: 'https://example.test/problems/care-setting-in-use', detail: 'ignored' },
      { status: 409, statusText: 'Conflict' },
    );
    fixture.detectChanges();
    expect(text(fixture)).toContain('Archive it instead');
  });

  it('keeps existing rows visible while refetching', () => {
    const { fixture, cmp } = create();
    cmp.refresh();
    fixture.detectChanges();
    expect(text(fixture)).toContain('Ambulatory clinic');
    httpMock.expectOne('/admin/care-settings').flush(CARE_SETTINGS);
  });
});
```

The four tests above are the shape worth repeating for any directory screen: **it loads**, **it
filters**, **it surfaces a mapped server error**, **it behaves during a refetch**. The error test is
the one people skip and the one that catches the most regressions, because the mapping lives in a
file nobody opens.

Calling a public signal directly (`cmp.query.set('tele')`) to drive a filter is fine — it is part of
the component's API. Reaching into `cmp['pendingDelete']` is not; if a spec needs a private, the
behaviour under test has no user-visible path and probably should not exist.

## Fixture builders

`features/<domain>/<domain>-fixtures.spec-helper.ts` — builders with overrides, so each test states
only what it is about.

```ts
import { TrainingModuleResponse, TrainingStepResponse } from '../../core/training/training.models';

/** Builders for the training component specs, so each test states only what it is about. */

export function step(
  id: string,
  title: string,
  order: number,
  overrides: Partial<TrainingStepResponse> = {},
): TrainingStepResponse {
  return { id, title, content: `<p>${title}</p>`, videoProvider: null, videoId: null, stepOrder: order, ...overrides };
}

export function module(
  id: string,
  overrides: Partial<TrainingModuleResponse> = {},
): TrainingModuleResponse {
  const steps = overrides.steps ?? [];
  return {
    id,
    title: 'Completing a mid-block evaluation',
    status: 'DRAFT',
    displayOrder: 0,
    publishedAt: null,
    createdAt: '2026-08-01T09:00:00Z',
    roleIds: [],
    stepCount: steps.length,
    readers: 0,
    ...overrides,
    steps,   // after the spread, so a derived field stays consistent with the override
  };
}
```

Two details:

- **Spread `overrides` before any field you derive from it.** `stepCount` computed from
  `overrides.steps` must not then be clobbered by the spread — putting `steps` last keeps the object
  internally consistent.
- **Fixed ISO timestamps, never `new Date()`.** A fixture built from the current clock makes a spec
  that passes today and fails at a month boundary.

Introduce the builder file on the second component spec in the slice, not the first — a builder
written for one caller is usually shaped wrong.

## Helper specs

Slice-root helpers get plain specs with no TestBed:

```ts
import { CARE_SETTING_ERROR_MESSAGES } from './care-setting-errors';

describe('CARE_SETTING_ERROR_MESSAGES', () => {
  it('offers a way forward for an in-use record', () => {
    expect(CARE_SETTING_ERROR_MESSAGES['care-setting-in-use']).toContain('Archive it instead');
  });
});
```

Testing an error map looks trivial, but the assertion worth making is that the *actionable* half of
the sentence is present — that is the part someone shortens later.

## E2E

Reserve Playwright for journeys that cross screens: sign in → create → publish → verify from another
role. Do not re-test filtering or validation there; those are component-spec territory and cost
seconds each in a browser. Stub only third-party externals, never the app's own API — an E2E test
against a mocked backend proves the mock works.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `Expected one matching request, found none` | `detectChanges()` not called, so `ngOnInit` never ran | `detectChanges()` before `expectOne` |
| `verify()` fails with an outstanding request | A refetch the test did not account for | Flush it, or assert it is absent — do not delete `verify()` |
| Component shows stale data after a signal set | Missing `detectChanges()` after the change | Call it before asserting on the DOM |
| `showModal is not a function` | jsdom has no `<dialog>` implementation | Stub the prototype in `beforeEach` |
| Spec passes alone, fails in the suite | Shared mutable fixture constant | Build fixtures inside a builder, not as a shared literal that tests mutate |
| Flaky assertion on a formatted date | Fixture built from the current clock | Fixed ISO strings |
