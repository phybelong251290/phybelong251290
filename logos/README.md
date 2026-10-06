# RCAF badge set — individual logos

The two 5×4 badge grids in `source/` split into 40 separate files, numbered in the
same order as the grids (`#01`–`#20` from `grid_01-20.jpg`, `#21`–`#40` from `grid_21-40.jpg`).

| Folder | What it is |
|---|---|
| `transparent/logo_NN.png` | Badge cut out on a transparent background, cropped tight with a 6 px margin |
| `white-background/logo_NN.png` | The same crop with the original white background kept |
| `contact_sheet.png` | All 40 cut-outs on one sheet for a quick visual check |

The small `#NN` index labels from the grids are removed from every crop.

## Using the files in design tools

The transparent PNGs drop straight into:

- **Adobe** (Photoshop, Illustrator, Express): *File → Place* / drag-and-drop. In Illustrator, *Image Trace* turns them into vectors.
- **Figma**: drag the PNGs onto the canvas, or *Place image* (Shift+Ctrl/Cmd+K).
- **Canva**: *Uploads → Upload files*. The transparency is preserved.
- **Sketch**: drag onto the canvas, or *Insert → Image*.

## Regenerating

```sh
python3 logos/split_logos.py logos/source/grid_01-20.jpg logos/source/grid_21-40.jpg logos
```

The background is removed by flood-filling the white surround from the cell border. Badge
`#18` also has white background showing through its wreath; that one is listed in
`HOLE_SEEDS` in the script.
