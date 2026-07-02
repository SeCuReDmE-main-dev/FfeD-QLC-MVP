# Edge User Console

The SecuredMe Education site includes two public support controls for readers.

## Dark / Light mode

Use the `Dark` / `Light` button in the upper-right header to switch the whole site between the Education light and dark themes.

This button is separate from the accessibility console. It controls the MkDocs Material color palette and keeps the selected mode while users move between pages.

## Accessibility menu

Use the `Access` button in the lower-right corner, or press `Ctrl+U`, to open the self-hosted accessibility menu.

The menu is designed for edge users, students, teachers, and readers who need a calmer first week with the documentation.

Available profiles:

| Profile | Purpose |
| --- | --- |
| Teacher Focus | Stronger link visibility, readable font, and reduced motion. |
| Low Vision | Larger text, stronger contrast, smart contrast, and oversized controls. |
| Dyslexia Support | Readable font, wider spacing, and reading guide. |
| Motion Safe | Reduced motion with stronger panel contrast. |

Available adjustments:

| Control | Effect |
| --- | --- |
| Bigger Text | Cycles through three text-size levels. |
| Text Spacing | Adds more line, letter, and word spacing in content. |
| Contrast + | Strengthens foreground and background contrast. |
| Smart Contrast | Strengthens key interface panels without inverting the whole page. |
| Highlight Links | Adds strong outlines and underlines to links. |
| Readable Font | Uses a simpler system font stack. |
| Reading Guide | Shows a horizontal reading guide that follows the pointer. |
| Pause Animation | Minimizes page animation and transitions. |
| Oversized Widget | Enlarges the accessibility launcher and panel. |
| Reset All | Returns the console to the default state. |

## Public boundary

This console is a reader-support layer, not a legal compliance certificate and not an automated remediation service. It does not send data to a third party, does not load a SaaS widget, and does not track users.

The implementation is static and self-hosted in the SecuredMe Education MkDocs site so future users can inspect, fork, and adapt it.
