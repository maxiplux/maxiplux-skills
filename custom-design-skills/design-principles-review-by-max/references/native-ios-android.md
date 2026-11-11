# Native iOS and Android: checks and fixes

Author of this reference: max · Part of `design-principles-review-by-max`

Read `mobile.md` first. Native toolkits give accessible, conventional behavior by default. Most
findings come from custom controls and from overriding defaults: fixed font sizes, hard-coded
colors, custom gestures, hidden system affordances.

## iOS (SwiftUI and UIKit)

Conventions come from Apple's Human Interface Guidelines (HIG). Minimum touch target: 44 × 44 pt.

| Rubric | Look for | Fix |
| --- | --- | --- |
| J4, J5, B4 | `Image(systemName:)` buttons with no label; `onTapGesture` on a non-control view. | Use `Button` with a `Label("Delete", systemImage: "trash")` and `.labelStyle(.iconOnly)` if needed, or add `.accessibilityLabel("Delete invoice")`. For custom tappable views add `.accessibilityAddTraits(.isButton)`. UIKit: set `accessibilityLabel`, `accessibilityTraits`, `isAccessibilityElement`. |
| J5 | Decorative images read by VoiceOver. | `Image(decorative:)` or `.accessibilityHidden(true)`. |
| J3 | Rows announced as fragments; illogical order. | `.accessibilityElement(children: .combine)`; `.accessibilitySortPriority(_:)` only when layout order cannot be fixed. |
| J7 | `.font(.system(size: 14))`; fixed frame heights around text; `lineLimit(1)` on essential text. | Text styles (`.font(.body)`, `.headline`); `@ScaledMetric` for spacing and icon sizes. UIKit: `UIFontMetrics` and `adjustsFontForContentSizeCategory = true`. Let rows grow. |
| J7 | Content under the notch or home indicator; `.ignoresSafeArea()` on content. | Keep content inside safe areas; extend only backgrounds. Handle the keyboard with scroll views and `.scrollDismissesKeyboard`. |
| J1, C4 | `Color(red:green:blue:)` literals; colors that do not adapt to dark mode. | Semantic colors (`Color.primary`, `Color(.systemBackground)`) or asset-catalog colors with light, dark and high-contrast variants. |
| J2 | State shown by color alone. | Add a symbol or text; honor `@Environment(\.accessibilityDifferentiateWithoutColor)`. |
| J8 | Animations that ignore the setting. | `@Environment(\.accessibilityReduceMotion)`; UIKit `UIAccessibility.isReduceMotionEnabled`. Replace movement with a fade or nothing. |
| J9 | Small custom buttons, tight toolbars. | `.frame(minWidth: 44, minHeight: 44)` and `.contentShape(Rectangle())` so the whole frame is tappable. |
| C3, F1 | Custom back button that disables the edge-swipe; full-screen covers with no close; non-standard tab bars. | Use `NavigationStack` and the system back button; give every sheet and cover a visible dismiss control. |
| D1, D2 | `task {}` / async loads with only the success view. | Model loading, empty, failed and loaded states; use `ProgressView`, `ContentUnavailableView`, and a retry. |
| D5 | Status changes not announced. | `AccessibilityNotification.Announcement("Saved").post()`; UIKit `UIAccessibility.post(notification: .announcement, argument:)`. |
| E1, G4 | `TextField` with no content type or keyboard. | `.textContentType(.emailAddress)`, `.keyboardType(.emailAddress)`, `.textInputAutocapitalization(.never)`, `.submitLabel(.next)`. |
| E2 | Destructive action with no guard. | `Button(role: .destructive)` inside `.confirmationDialog`, or offer undo. |
| F2, H3 | Permission prompts at launch. | Ask at the moment of use, after explaining why. |

Evidence tools:

- **Accessibility Inspector** (Xcode → Open Developer Tool): inspects labels and traits and runs an
  audit for contrast, hit-area size and missing labels.
- **Automated audit in UI tests** (Xcode 15+): `try app.performAccessibilityAudit()` fails the test
  with the offending element. Add it for each screen you fix.
- **Xcode Previews / Simulator**: Dynamic Type at the largest accessibility size, dark appearance,
  Increase Contrast, Reduce Motion, VoiceOver.

## Android (Jetpack Compose and XML views)

Conventions come from Material Design. Minimum touch target: 48 × 48 dp.

| Rubric | Look for | Fix |
| --- | --- | --- |
| J4, J5, B4 | `Icon(..., contentDescription = null)` inside a clickable; `ImageView` / `ImageButton` without `android:contentDescription`. | Give meaningful icons a `contentDescription` that states the action. For decorative images pass `null` (Compose) or `android:importantForAccessibility="no"`. |
| J3 | `Modifier.clickable` on a `Box` with no role; rows read as fragments. | `Modifier.clickable(role = Role.Button, onClickLabel = "Open invoice")`; `Modifier.semantics(mergeDescendants = true) {}`. XML: `android:focusable`, `android:screenReaderFocusable`. |
| J4 | `EditText` with only a hint; a label `TextView` not tied to its field. | Compose `TextField(label = { Text("Email") })`. XML: `TextInputLayout` with `android:hint`, or `android:labelFor` on the label. |
| J7 | Text sizes in `dp` or `px`; fixed heights around text; `maxLines = 1` on essential text. | `sp` for text; `MaterialTheme.typography` styles; `heightIn(min = …)` instead of fixed heights; allow wrapping. |
| J7 | Content drawn under system bars or the keyboard in edge-to-edge layouts. | Apply `WindowInsets` (`Modifier.safeDrawingPadding()`, `imePadding()`); XML: handle insets with `ViewCompat.setOnApplyWindowInsetsListener`. |
| J1, C4 | `Color(0xFF…)` literals; hex colors in layouts. | `MaterialTheme.colorScheme` roles; `@color` resources with `values-night` variants. |
| J8 | Animations that ignore the system setting. | Check the animator duration scale (`Settings.Global.ANIMATOR_DURATION_SCALE`) or reduce-motion state and skip non-essential motion. |
| J9 | `Modifier.size(24.dp).clickable`; small `ImageButton`s. | `Modifier.minimumInteractiveComponentSize()` or `IconButton` (48dp by default). XML: `android:minWidth="48dp"`, `android:minHeight="48dp"`. |
| C3, F1 | Intercepted back with no reason; custom back that ignores predictive back; iOS-style navigation. | Use `BackHandler` only to protect unsaved work; support predictive back; bottom navigation, top app bar and sheets from Material. |
| D1, D2 | Screens with only the success state. | A UI state type covering loading, empty, error and content; `CircularProgressIndicator`, an empty-state composable, a retry. |
| D5 | Status changes not announced. | `Modifier.semantics { liveRegion = LiveRegionMode.Polite }`; XML `android:accessibilityLiveRegion="polite"`. |
| E1, G4 | Text fields with default keyboard and no autofill. | `KeyboardOptions(keyboardType = KeyboardType.Email, imeAction = ImeAction.Next)` and autofill content types; XML `android:inputType`, `android:autofillHints`. |
| E2 | Swipe-to-delete with no recovery. | `Snackbar` with an Undo action, or a confirmation `AlertDialog` for irreversible deletes. |
| E4 | State lost on rotation or process death. | `rememberSaveable`, `SavedStateHandle`. |
| F2, H3 | Notification and location permission requested on first launch. | Request in context, with a rationale. |

Evidence tools:

- **Accessibility Scanner** (Google app on a device or emulator): reports touch-target size,
  contrast and missing labels on the visible screen.
- **Espresso**: `AccessibilityChecks.enable()` makes existing view tests fail on accessibility
  issues. **Compose**: assert semantics in UI tests (`onNodeWithContentDescription`,
  `assertHasClickAction`, `assertHeightIsAtLeast(48.dp)`).
- **Android Lint**: reports missing `contentDescription` and hard-coded text. Do not repeat what it
  reports.
- **Layout Inspector** and Compose previews with `fontScale = 2f` and night mode; **TalkBack** on a
  device.

## Sources

- Apple, Human Interface Guidelines, Accessibility:
  <https://developer.apple.com/design/human-interface-guidelines/accessibility>
- Apple, Accessibility for developers: <https://developer.apple.com/accessibility/>
- Android, Build accessible apps: <https://developer.android.com/guide/topics/ui/accessibility>
- Android, Accessibility in Jetpack Compose:
  <https://developer.android.com/develop/ui/compose/accessibility>
- Material Design 3, Accessibility: <https://m3.material.io/foundations/designing/overview>
