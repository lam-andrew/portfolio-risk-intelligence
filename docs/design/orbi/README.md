# Orbi — saved design prototype

Status: design direction approved for preservation; not integrated or production-ready.
Saved from the Orbit design conversation on 2026-09-06.

## Preview

Open [prototype.html](prototype.html) in a modern browser. It works offline, with no
installation, API keys, server, or external assets. The HTML contains the editable
styles and animation code, not a recording. GitHub shows its source; download the
file or open the local checkout to see the animation.

This file is the repository source of truth for this concept. It does not depend
on the original conversation, its local preview server, or the avatar studio.

## Preserve this direction

- Midnight-blue spherical body with a glass-like face and cyan starlight eyes.
- Two gently shifting tilted orbital paths and three moving satellites.
- Rear paths and satellites render behind the body; front paths render over it.
- Subtle floating, blinking, luminous trails, and restrained star-field backdrop.
- Idle, Researching (faster orbital motion and scanning gaze), and Happy expressions.
- Pause/play control and an initially still state for reduced-motion preferences.

The custom version replaces the earlier bright-blue avatar-studio concept as the
preferred reference. It is drawn with the browser's 2D Canvas API; it does not
import the avatar studio's exported JSON, runtime, or animation library.
The optional guarded `Tweak` block only enables design controls in compatible
preview hosts; normal browser operation does not require it.

## Future integration handoff

1. Read this note and preview the file before implementing. Preserve the approved
   appearance and actual front/back orbital motion; do not substitute a static icon.
2. Extract the renderer into a reusable React/TypeScript mascot component. Suggested
   inputs: state (`idle`, `researching`, `happy`), size, and motion-enabled preference.
   Keep the demonstration buttons and star-field stage separate from the mascot.
3. Replace the fixed DOM ID with a component ref so multiple instances work. Add
   proper cleanup for animation frames, ResizeObserver, and media-query listeners.
   Remove preview-only Tweak bindings from the production component.
4. Connect expressions to actual assistant lifecycle events, not fabricated progress.
   Listening, error, cancellation, and response-streaming states are not implemented
   in this prototype and need design when the assistant feature is built.
5. Verify small chat-avatar sizes, light/dark surfaces, mobile layout, contrast,
   keyboard controls, reduced motion, pause/resume, background/offscreen behavior,
   multiple instances, and unmount cleanup. Provide a static fallback where needed.
6. Add component tests and visual/motion checks. Capture acceptance evidence before
   claiming the mascot is integrated or complete.

No app dependencies, architecture, existing stories, sprint allocation, or acceptance
statuses change by saving this prototype. No ADR is needed for this reversible
design experiment; assess architectural significance when integrating it.

Future prompt: "Integrate the saved Orbi mascot from docs/design/orbi, preserving
its appearance and orbital animation. Follow the handoff checklist in its README."
