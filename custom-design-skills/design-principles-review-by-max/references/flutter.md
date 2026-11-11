# Flutter: checks and fixes

Author of this reference: max · Part of `design-principles-review-by-max`

Read `mobile.md` first. This file adds what to look for in Flutter code and how to fix it. Flutter
draws its own widgets, so platform accessibility and conventions are not inherited for free: they
come from the semantics tree and from choosing Material or Cupertino widgets deliberately.

## What to look for in code

| Rubric | Look for | Fix |
| --- | --- | --- |
| J4, J5, B4 | `IconButton` without `tooltip`; `Icon` / `Image` conveying meaning without `semanticLabel`; `GestureDetector` or `InkWell` wrapping a custom control with no `Semantics`. | Add `tooltip:` to `IconButton` (it also becomes the semantic label). Set `semanticLabel:`. Wrap custom controls in `Semantics(button: true, label: '…', onTap: …)`. |
| J5 | Decorative images announced by the screen reader. | `Image(..., excludeFromSemantics: true)` or wrap in `ExcludeSemantics`. |
| J3 | Rows read as fragments (icon, title, subtitle announced separately). | `MergeSemantics` around the row, or use `ListTile`. |
| J3 | Wrong reading or focus order in custom layouts. | Fix widget order first; otherwise `FocusTraversalGroup` with an `OrderedTraversalPolicy`, or `Semantics(sortKey: OrdinalSortKey(n))`. |
| J9 | `GestureDetector` on a small child; `IconButton` with `constraints` or `visualDensity` shrinking it; `MaterialTapTargetSize.shrinkWrap`. | Keep the 48 × 48 dp minimum (`kMinInteractiveDimension`). Pad the child or use `ConstrainedBox(constraints: BoxConstraints(minWidth: 48, minHeight: 48))`. |
| J7 | `SizedBox(height: …)` or fixed-height containers around text; `textScaler: TextScaler.noScaling`; `maxLines: 1` with ellipsis on essential text. | Let text size its container. Remove scaling overrides. Allow wrapping, or use `Flexible` / `Expanded`. |
| J7 | Content under the notch, home indicator or keyboard. | `SafeArea`; `Scaffold(resizeToAvoidBottomInset: true)`; scrollable forms with `MediaQuery.viewInsetsOf(context)`. |
| J1, C4 | `Color(0xFF…)` and `TextStyle(fontSize: …)` scattered in widgets. | Read from `Theme.of(context).colorScheme` and `textTheme`. Define light and dark `ThemeData`. |
| J8 | Animations that ignore the system setting. | Check `MediaQuery.disableAnimationsOf(context)` and shorten or skip the animation. |
| D1, D2 | `FutureBuilder` / `StreamBuilder` / state classes handling only the data case. | Handle waiting, error (message plus retry), and empty explicitly. Keep previously loaded data visible during refresh. |
| D5 | Status changes with no announcement. | `SemanticsService.announce(message, textDirection)` or a `Semantics(liveRegion: true)` wrapper. |
| E1, G4 | `TextField` without `keyboardType`, `textInputAction`, `autofillHints`. | Set all three. Group related fields in `AutofillGroup`. |
| E3 | `validator` returning terse text ("Invalid"); errors shown only by a red border. | Return a sentence that says how to fix it. `InputDecoration(errorText:)` shows it and exposes it to the screen reader. |
| J4 | `hintText` used as the only label. | `InputDecoration(labelText: …)`; keep `hintText` for an example. |
| E2 | `Dismissible` deleting on swipe with no undo. | `confirmDismiss`, or a `SnackBar` with an Undo `SnackBarAction`. |
| F1 | `PopScope(canPop: false)` with no explanation; dialogs with `barrierDismissible: false` and no close action. | Give a visible way out. Block back only to protect unsaved work, and then ask. |
| C3 | Material widgets with iOS-only patterns, or Cupertino on Android. | Use `.adaptive` constructors (`Switch.adaptive`, `CircularProgressIndicator.adaptive`, `showAdaptiveDialog`) or branch on `Theme.of(context).platform`. |
| B1, I3 | Hard-coded strings; layouts that break with long translations. | Move strings to `.arb` files; test with a long locale and `Directionality` RTL. |

## Tools that produce evidence

- **Accessibility guideline tests** (`flutter_test`). Add to a widget test for each screen:

  ```dart
  testWidgets('invoice screen meets accessibility guidelines', (tester) async {
    final handle = tester.ensureSemantics();
    await tester.pumpWidget(const MyApp());
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline)); // 48x48
    await expectLater(tester, meetsGuideline(iOSTapTargetGuideline));     // 44x44
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline)); // tappables have labels
    await expectLater(tester, meetsGuideline(textContrastGuideline));     // WCAG text contrast
    handle.dispose();
  });
  ```

  A failing guideline is evidence for J9, J4/J5 and J1 and names the offending widget.
- **`flutter analyze`** for lints. Do not report what it already reports.
- **Semantics debugger**: `MaterialApp(showSemanticsDebugger: true)` shows what the screen reader
  sees.
- **Text scale**: wrap the app in `MediaQuery` with `textScaler: TextScaler.linear(2.0)` in a
  widget test or golden test to catch overflow (the yellow-black stripes are an I3/J7 finding).
- **Device**: TalkBack on Android, VoiceOver on iOS, and Android's Accessibility Scanner.

When remediating, add the guideline test for each screen you fix. It is the cheapest way to prove
the finding is closed and to keep it closed.

## Sources

- Flutter accessibility: <https://docs.flutter.dev/ui/accessibility-and-internationalization/accessibility>
- `flutter_test` accessibility guidelines API:
  <https://api.flutter.dev/flutter/flutter_test/AccessibilityGuideline-class.html>
