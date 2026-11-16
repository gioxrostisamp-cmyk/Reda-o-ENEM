# What if… years of your life could be used as money?

A cinematic slide deck for the English class "What If…?" project.
Single offline HTML file: every scene, font and script is inside it.

**Open:** `dist/what-if-life-as-currency.html` in Chrome, Edge or Firefox. Press **F** for full screen.

> Status: **phase 1 preview.** Slides 1 and 3 only, with the camera move between them.
> The full 10-slide deck comes after the look and motion are approved.

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
- `node tools/check-contrast.js 1 3`: measures text contrast against the photo behind each text (needs Playwright).
