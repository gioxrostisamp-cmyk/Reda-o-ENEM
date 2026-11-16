# What if… years of your life could be used as money?

A cinematic slide deck for the English class "What If…?" project.
Single offline HTML file: every scene, font and script is inside it.

**Open:** `dist/what-if-life-as-currency.html` in Chrome, Edge or Firefox. Press **F** for full screen.

> Status: **full deck, 10 slides.** The closing question (slide 9) is its own page: a hard cut to
> black, then the question alone. The PDF therefore has 11 pages.

## Presenting

| Key | Action |
| --- | --- |
| → · Space · Page Down · click | next beat / next slide |
| ← · Page Up · right-click | previous beat; at the first beat, the camera move plays in reverse |
| F | full screen |
| N | speaker notes in a second window (keys work there too) |
| R | replay the current slide |
| B or . | black screen |

Most clickers send Page Down / Page Up, so they work out of the box.
On a phone or tablet: swipe left (or tap the right side) for next, swipe right (or tap the left side) for back. Hold the phone sideways.
Open `…html#3` to jump straight to slide 3 in its final state (for rehearsing).

## Exporting

- **PDF:** open `…html#print` and print to PDF (1920×1080, background graphics on), or run
  `node tools/export-pdf.js`. Every slide is printed in its final state.
- `dist/what-if-life-as-currency.pdf` is the current export.

## Editing and rebuilding

- `src/deck.html`: slides, styles, choreography and speaker notes (`<aside class="notes">`).
- `assets/scenes/`: the six photos (`img1-time-bank` … `img6-ana`).
- `assets/fonts/`: Barlow Condensed and IBM Plex Mono (SIL Open Font License).
- `python3 build.py`: rebuilds `dist/`. Needs Python 3 with Pillow and NumPy.
  `python3 build.py --web PATH` also writes a copy without the `<html>/<head>/<body>` skeleton,
  for hosts that wrap the page in their own document (used for the private preview link).
- `node tools/check-contrast.js`: measures the contrast of every text against the photo behind it, on all slides (needs Playwright).
