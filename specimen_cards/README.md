# Specimen cards

Renders SPECIMEN-stamped preview cards (design concept, not valid credentials) from the first 100 synthetic
records in `../roster1000.json`, using the card renderer from the issuing app.

Every card carries a diagonal SPECIMEN watermark, a "not a valid credential" footer, `KH-SPEC-` ID numbers and a
QR/barcode that only says it is a specimen. Output is preview resolution (14 px/mm), not print resolution.

1. `python3 emblem_tiles.py <emblem-sheet.webp> emblems` cuts a numbered emblem sheet into 19:24 photo tiles
   (or `python3 portraits.py ../_sp.zip portraits` for head-and-shoulders crops).
2. `NODE_PATH=$(npm root -g) LIBS_DIR=<dir with qrcode-generator + jsbarcode> [FONTS_DIR=<local Google Fonts>] node render.mjs <app.html> ../roster1000.json emblems png 100`
3. `python3 sheet.py png specimen_cards_100.pdf` lays them out 5 officers per A4 page.

`specimen_cards_100.pdf` is the result for the 100 officers, with a unit emblem in the photo slot.
`png/`, `emblems/` and `portraits/` are git-ignored.
