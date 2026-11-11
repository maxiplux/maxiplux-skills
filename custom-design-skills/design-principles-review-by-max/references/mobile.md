# Mobile: stack-agnostic checks

Author of this reference: max · Part of `design-principles-review-by-max`

The rubric applies to mobile apps unchanged. This file says what each theme means on a phone or
tablet, whatever the framework. For Flutter add `flutter.md`; for SwiftUI, UIKit, Compose or
Android XML add `native-ios-android.md`.

What changes on mobile: input is a finger, not a pointer; the screen is small and partly covered by
system UI and the keyboard; attention is interrupted; the platform has strong conventions that
users already know; and assistive technology is a screen reader driven by gestures (VoiceOver,
TalkBack), plus system-wide text size, contrast and motion settings.

## Checks by rubric theme

| Rubric | On mobile, check that… |
| --- | --- |
| A1, A2 | Each screen does one thing. The primary action is within thumb reach or in the platform's standard position, and is not hidden behind a menu. |
| B2 | Tappable elements look tappable. There is pressed feedback (highlight, ripple, opacity) on every control. |
| B4 | Tab bar and toolbar icons have text labels or are platform-standard symbols. |
| C3 | The app follows its platform: back navigation (edge swipe on iOS; system back, including predictive back, on Android), tab bar at the bottom, standard sheets, pickers, share and permission flows. An iOS-styled app on Android, or the reverse, is a C3 finding. |
| D1 | Pull-to-refresh, button presses and form submits respond at once. Network work shows progress and never freezes the UI. |
| D2 | There are states for offline, slow network, and a failed request, with a retry. Content already loaded stays visible. |
| E1 | Each field has the right keyboard (email, number, phone, URL), the right autofill hint, and correct capitalization and autocorrect settings. |
| E2 | Destructive swipe actions and buttons are confirmed or undoable, and are not placed where a thumb lands by accident. |
| E4 | Input survives rotation, backgrounding, an incoming call, and process death where the platform restores state. |
| F1 | Every screen and sheet can be left: back gesture, close button, or swipe-to-dismiss. A gesture never replaces the visible control; it adds to it. |
| F2 | No permission prompts on first launch before the user has a reason to grant them. No auto-playing sound. |
| G1 | No codes to copy between apps by hand: use one-time-code autofill, paste, deep links, scanning. |
| G3 | Shortcuts exist for frequent use: swipe actions, long-press menus, home-screen shortcuts, recent items. Each has a visible alternative. |
| G4 | Sign-in supports password managers, passkeys or biometrics. Forms are short and split across steps where needed. |
| H3 | Notifications are requested in context and are useful. No badges or nags to draw the user back. |
| I3 | Layout holds with long translations, the largest system text size, a small device and a tablet. |
| J1 | Contrast holds in both light and dark appearance, and with the system's increased-contrast setting. |
| J3 | Every control is reachable and operable with the screen reader and with switch or keyboard access, in a logical order. Custom gestures have an accessible alternative. |
| J4, J5 | Every control and meaningful image has an accessibility label. Decorative images are hidden from the screen reader. Labels describe purpose ("Delete invoice"), not appearance ("trash icon"). |
| J7 | Text scales with the system font size without clipping or overlap. Content respects safe areas (notch, home indicator, rounded corners) and the on-screen keyboard. Both orientations work unless the task needs one. |
| J8 | Animation is reduced or removed when the system "reduce motion" setting is on. |
| J9 | Touch targets meet the platform minimum, with space between them. |
| K1 | The app is frugal: no needless background work, location or network polling; images sized for the device; dark appearance supported. |

## Touch target sizes

| Guideline | Minimum target |
| --- | --- |
| Apple Human Interface Guidelines | 44 × 44 pt |
| Material Design (Android, Flutter) | 48 × 48 dp |
| WCAG 2.2, 2.5.8 Target Size (Minimum), level AA | 24 × 24 CSS px, or enough spacing around a smaller target |
| WCAG 2.2, 2.5.5 Target Size (Enhanced), level AAA | 44 × 44 CSS px |

Judge a native app against its platform's figure. The visible glyph may be smaller as long as the
tappable area meets the minimum.

## Evidence on mobile

- **Code**: accessibility labels, text styles (scalable or fixed), hard-coded sizes and colors,
  keyboard types, safe-area handling, navigation structure.
- **Screenshots**: ask for or capture light and dark appearance, the largest text size, and a small
  device.
- **Live**: a simulator or emulator with the screen reader on, the largest text size, reduce motion
  on, and airplane mode for the offline states. If the app cannot run in the current environment,
  mark these checks not assessed.

## Sources

- Apple Human Interface Guidelines: <https://developer.apple.com/design/human-interface-guidelines/>
- Material Design 3: <https://m3.material.io/>
- WCAG 2.2: <https://www.w3.org/TR/WCAG22/>
- W3C, "Mobile Accessibility: How WCAG 2.0 and Other W3C/WAI Guidelines Apply to Mobile":
  <https://www.w3.org/TR/mobile-accessibility-mapping/>
