# RCAF badge set — individual logos

The two 5×4 badge grids in `source/` split into 40 separate files, numbered in the
same order as the grids (`#01`–`#20` from `grid_01-20.jpg`, `#21`–`#40` from `grid_21-40.jpg`).

| Folder | What it is |
|---|---|
| `transparent/logo_NN.png` | Badge cut out on a transparent background, cropped tight with a 6 px margin |
| `white-background/logo_NN.png` | The same crop with the original white background kept |
| `contact_sheet.png` | All 40 cut-outs on one sheet for a quick visual check |
| `fixed-text/logo_NN.png` | **Clean Khmer lettering**: the garbled text replaced with properly shaped Khmer, transparent background, 2× size |
| `fixed-text/contact_sheet.png` | All 40 fixed badges on one sheet |

The small `#NN` index labels from the grids are removed from every crop.

## Using the files in design tools

The transparent PNGs drop straight into:

- **Adobe** (Photoshop, Illustrator, Express): *File → Place* / drag-and-drop. In Illustrator, *Image Trace* turns them into vectors.
- **Figma**: drag the PNGs onto the canvas, or *Place image* (Shift+Ctrl/Cmd+K).
- **Canva**: *Uploads → Upload files*. The transparency is preserved.
- **Sketch**: drag onto the canvas, or *Insert → Image*.

## Fixed Khmer lettering

The lettering in the source grids was broken: the Khmer letters were misshapen and the
subscript consonants and vowels sat in the wrong places. `fix_text.py` removes the old
lettering (it masks the pixels that don't match the band's background colours and inpaints
them), then typesets new text with a real Khmer font along the same straight line or arc.
Text is shaped with HarfBuzz (Pillow + raqm), so stacked consonants and vowels are placed correctly.

- Fonts: **Koulen** for most lettering and **Moul** for #06 and #20 (the coat of arms motto
  ជាតិ សាសនា ព្រះមហាក្សត្រ). Both are in `fonts/` (SIL Open Font License), so this works offline.
- Every badge's wording lives in `badge_text.json`. **Please check the wording.** It is my
  reading of what each unit's name should be, and some of the originals were too garbled to read
  with certainty. To change a name, edit its `"text"` and re-run the script.
- Badges #16, #18, #25 and #26 have no lettering and are unchanged.

```sh
python3 logos/fix_text.py logos/badge_text.json logos/transparent logos/fixed-text \
    --font Koulen=logos/fonts/Koulen.ttf --font Moul=logos/fonts/Moul.ttf
```

Options: `--only 7 22` re-renders just those badges, and `--size 4` sets the output to 4× the
crop (default 2×). To use another font for the lettering, map it to the same name, e.g.
`--font Koulen=Kh_ST_Yeaksa_Pro_V2.otf`.

Needs `pip install pillow numpy opencv-python-headless` (Pillow must be built with raqm).

## Regenerating the cut-outs

```sh
python3 logos/split_logos.py logos/source/grid_01-20.jpg logos/source/grid_21-40.jpg logos
```

The background is removed by flood-filling the white surround from the cell border. Badge
`#18` also has white background showing through its wreath; that one is listed in
`HOLE_SEEDS` in the script.
