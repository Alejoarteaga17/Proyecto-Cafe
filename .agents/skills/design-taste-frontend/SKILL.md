---
name: design-taste-frontend
description: >-
  Review and improve the project's static frontend with clear hierarchy,
  consistent spacing, accessible controls, responsive layouts, and restrained
  visual styling. Use for changes to frontend/index.html or frontend/dashboard.html.
---

# Frontend design and consistency

This project uses a small static frontend in `frontend/`. Keep changes aligned
with the existing CSV upload, IoT simulation, and QuickSight dashboard flows.
Do not introduce a framework, build step, WebGL, shader effects, image
pipelines, or external UI kits unless the project requirements explicitly call
for them.

## Design rules

- Preserve the existing functionality and API interactions.
- Use a clear visual hierarchy and one primary action per interaction.
- Keep spacing, typography, controls, and status messages consistent across
  the tabs.
- Support the existing desktop and mobile layouts without horizontal overflow.
- Keep labels visible, controls keyboard-accessible, and focus states clear.
- Use concise Spanish copy consistent with the current interface.
- Avoid decorative effects that reduce readability or distract from data
  submission and dashboard use.

## Validation

Run the consistency checker against the changed page when Chrome/Chromium is
available:

```bash
node .agents/skills/design-taste-frontend/scripts/consistency.mjs \
  frontend/index.html \
  --widths 1440,1024,768,390 \
  --rhythm-widths 1440,768,390 \
  --page service
```

For `frontend/dashboard.html`, replace the page path in the command. Review
every `FAIL` and relevant `WARN`; do not hide findings by weakening the
checker. If the checker cannot run because the environment lacks a browser,
report that limitation explicitly.
