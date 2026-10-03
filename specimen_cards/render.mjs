// Renders SPECIMEN-stamped preview cards for the first N synthetic roster records, using the card renderer
// from the issuing app. Every card carries a SPECIMEN watermark and non-operational codes.
//
//   NODE_PATH=$(npm root -g) node render.mjs <app.html> <roster.json> <portraits-dir> <out-dir> [count]
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const [appHtml, rosterPath, portraitDir, outDir, countArg] = process.argv.slice(2);
const COUNT = +(countArg || 100);
const SCALE = 14; // px per mm (preview size, not print resolution)
const { chromium } = createRequire(import.meta.url)("playwright");
const libs = process.env.LIBS_DIR;

const roster = JSON.parse(fs.readFileSync(rosterPath, "utf8")).slice(0, COUNT);
const portraits = fs.readdirSync(portraitDir).filter(f => f.endsWith(".jpg")).sort()
  .map(f => "data:image/jpeg;base64," + fs.readFileSync(path.join(portraitDir, f)).toString("base64"));

const BRANCH = { "Army": "army", "Navy": "navy", "Air Force": "af", "Joint Staff": "hc", "Gendarmerie": "hc" };
const BLOOD = ["O+", "A+", "B+", "AB+", "O−", "A−", "B−", "AB−"];

const browser = await chromium.launch({ args: ["--no-sandbox"] });
const ctx = await browser.newContext({
  ignoreHTTPSErrors: true,
  ...(process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {}),
});
const page = await ctx.newPage();
// serve the CDN libs from local copies; the PDF lib is not needed here
await page.route("**/qrcode.min.js", r => r.fulfill({ contentType: "text/javascript", body: fs.readFileSync(`${libs}/qrcode-generator/qrcode.js`) }));
await page.route("**/JsBarcode.all.min.js", r => r.fulfill({ contentType: "text/javascript", body: fs.readFileSync(`${libs}/jsbarcode/dist/JsBarcode.all.min.js`) }));
await page.route("**/jspdf.umd.min.js", r => r.fulfill({ contentType: "text/javascript", body: "window.jspdf={};" }));
await page.goto("file://" + path.resolve(appHtml));
await page.waitForFunction(() => document.getElementById("cvFront")?.width > 0, null, { timeout: 30000 });
await page.waitForTimeout(1500);

fs.mkdirSync(outDir, { recursive: true });
const result = await page.evaluate(async ({ roster, portraits, BRANCH, BLOOD, SCALE }) => {
  const load = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => r(null); i.src = src; });
  const imgs = await Promise.all(portraits.map(load));

  // Non-operational codes: the QR and barcode only ever say this is a specimen.
  window.qrPayload = d => "SPECIMEN - NOT A VALID CREDENTIAL - " + d.idno;
  settings.sig = "AUTHORISED SIGNATORY (SPECIMEN)"; settings.sig_kh = ""; sigImg = null;

  const RANK = { "LIEUTENANT": "FIRST LIEUTENANT" };
  const SPEC_RED = "rgba(184,67,58,";

  function specimen(cv, S, back) {
    const c = cv.getContext("2d");
    c.save();
    c.globalCompositeOperation = "source-atop";   // only paint on the card itself
    c.textAlign = "center"; c.textBaseline = "middle";
    c.font = `700 ${11 * S}px Cinzel, serif`; c.letterSpacing = (1.2 * S) + "px";
    for (const y of [22, 46, 70]) {
      c.save(); c.translate(27 * S, y * S); c.rotate(-0.55);
      c.fillStyle = SPEC_RED + ".34)"; c.fillText("SPECIMEN", 0, 0); c.restore();
    }
    c.font = `700 ${1.1 * S}px "Barlow Semi Condensed", sans-serif`; c.letterSpacing = (.25 * S) + "px";
    c.fillStyle = "#ff8a80"; c.fillText("DESIGN CONCEPT · NOT A VALID CREDENTIAL", 27 * S, 85.0 * S);
    c.restore();
  }

  const out = [];
  roster.forEach((o, i) => {
    const n = String(i + 1).padStart(5, "0");
    const rank = (o.r || "").toUpperCase();
    const d = {
      name: o.n.toUpperCase(), name_kh: "", rank: RANK[rank] || rank, rank_kh: o.rk || "",
      position: (o.sp || "").toUpperCase(), position_kh: "", unit: (o.u || "").toUpperCase(), unit_kh: "",
      branch: BRANCH[o.br] || "hc", phone: "", blood: BLOOD[i % BLOOD.length], dob: o.dob, nat: "CAMBODIAN",
      idno: "KH-SPEC-" + n, issue: "2026-10-03", expiry: "2031-10-02", lang: "bi", qrmode: "id",
      pz: 1, px: 50, py: 8,
    };
    photoImg = imgs[i % imgs.length];
    const f = document.createElement("canvas"), b = document.createElement("canvas");
    drawFront(f, SCALE, d); specimen(f, SCALE, false);
    drawBack(b, SCALE, d); specimen(b, SCALE, true);
    out.push({ n, front: f.toDataURL("image/png"), back: b.toDataURL("image/png"), meta: { sn: o.sn, name: o.n, rank: o.r, branch: o.br } });
  });
  return out;
}, { roster, portraits, BRANCH, BLOOD, SCALE });

for (const r of result) {
  fs.writeFileSync(`${outDir}/${r.n}_front.png`, Buffer.from(r.front.split(",")[1], "base64"));
  fs.writeFileSync(`${outDir}/${r.n}_back.png`, Buffer.from(r.back.split(",")[1], "base64"));
}
fs.writeFileSync(`${outDir}/index.json`, JSON.stringify(result.map(r => ({ file: r.n, ...r.meta })), null, 1));
console.log("rendered", result.length, "cards");
await browser.close();
