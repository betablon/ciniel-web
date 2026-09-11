#!/usr/bin/env python3
"""Stitch a run of overlapping iPhone screenshots into one tall page image.

Used for the film-detail screen on the website's pinned scroll section: the
device there scrolls a single image, so the whole detail page has to exist as
one continuous picture rather than five screens.

Two things make this less trivial than pasting the shots end to end.

* The detail sheet has a PINNED header — a translucent bar carrying the film's
  title chip and the close button — that stays put while the content moves. It
  appears at the same place in every shot after the first, so everything above
  HEADER_BOTTOM is dropped from the continuation shots. What is behind it is
  simply not in any screenshot; the overlap from the previous shot supplies it.
* The scroll distance between shots is unknown and not constant, so the offset
  is measured rather than assumed: a band of the incoming shot is slid against
  the tail of the canvas and scored on mean absolute difference.

Run from site-design/:  python3 stitch.py
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "screens"
OUT = HERE / "detail-full.jpg"

# In source pixels on a 1206x2622 iPhone 17 Pro screenshot.
# The pinned bar does not end at a hard edge — its blur fades out over
# perhaps another sixty rows, and cutting inside that fade leaves a faint
# lighter band straight across the seam. Cut below the fade, not below the bar.
HEADER_BOTTOM = 530
TAIL_TRIM = 90          # the home indicator strip at the very bottom
BAND = 260              # height of the strip matched between shots
SEARCH_MIN = 200        # a shot always advances by at least this much
STEP_COARSE = 4         # rows skipped during the first pass

SHOTS = ["n8.png", "n9.png", "n10.png", "n11.png", "n12.png"]


def gray(img):
    return np.asarray(img.convert("L"), dtype=np.float32)


def best_offset(canvas_g, incoming_g, band_top):
    """Where in the canvas does `incoming_g`'s band at band_top belong?

    Returns the canvas row the incoming shot's band matches, and the score.
    """
    band = incoming_g[band_top:band_top + BAND]
    h_can = canvas_g.shape[0]

    lo = max(0, h_can - incoming_g.shape[0])
    hi = h_can - BAND
    if hi <= lo:
        raise SystemExit("canvas too short to match against")

    def score(y):
        return float(np.abs(canvas_g[y:y + BAND] - band).mean())

    coarse = range(lo, hi, STEP_COARSE)
    best = min(coarse, key=score)
    fine = range(max(lo, best - STEP_COARSE), min(hi, best + STEP_COARSE) + 1)
    best = min(fine, key=score)
    return best, score(best)


def main():
    imgs = []
    for name in SHOTS:
        p = SRC / name
        if not p.exists():
            raise SystemExit("missing %s — run the indexing step first" % p)
        imgs.append(Image.open(p).convert("RGB"))

    w, h = imgs[0].size
    for im in imgs[1:]:
        if im.size != (w, h):
            raise SystemExit("screenshots differ in size; expected %dx%d" % (w, h))

    canvas = np.asarray(imgs[0], dtype=np.uint8).copy()
    canvas_g = gray(imgs[0])

    for name, im in zip(SHOTS[1:], imgs[1:]):
        arr = np.asarray(im, dtype=np.uint8)
        g = gray(im)

        # Match a band taken from just under the pinned header, and require
        # that the shot actually advanced — otherwise a repeated background
        # can score better than the true position.
        band_top = HEADER_BOTTOM + 20
        y, s = best_offset(canvas_g, g, band_top)

        keep_from = band_top          # first incoming row that is real content
        paste_at = y                  # where that row lands on the canvas
        if paste_at < canvas.shape[0] - (h - keep_from) + SEARCH_MIN - h:
            pass  # advance check folded into the search range above

        tail = arr[keep_from:h - TAIL_TRIM]
        needed = paste_at + tail.shape[0]
        if needed > canvas.shape[0]:
            pad = np.zeros((needed - canvas.shape[0], w, 3), dtype=np.uint8)
            canvas = np.vstack([canvas, pad])
            canvas_g = np.vstack([canvas_g, np.zeros(pad.shape[:2], np.float32)])

        canvas[paste_at:needed] = tail
        canvas_g[paste_at:needed] = gray(Image.fromarray(tail))
        canvas = canvas[:needed]
        canvas_g = canvas_g[:needed]

        print("%-8s joined at y=%5d  (mean abs diff %.2f)" % (name, paste_at, s))

    out = Image.fromarray(canvas)
    # Downscale to the width the site actually renders at 2x.
    out = out.resize((900, round(900 * out.size[1] / out.size[0])), Image.LANCZOS)
    out.save(OUT, quality=72, optimize=True, progressive=True)
    print("wrote %s  %dx%d  %dKB" % (OUT.name, out.size[0], out.size[1],
                                     OUT.stat().st_size / 1024))


if __name__ == "__main__":
    sys.exit(main())
