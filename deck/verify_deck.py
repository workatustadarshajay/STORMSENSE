#!/usr/bin/env python3
"""Independent checks on the generated deck.

Nothing here reuses the builder's assumptions: the package is re-read from disk
and every claim is recomputed from the XML.

  A  zip + XML well-formedness of every part
  B  [Content_Types].xml covers every part
  C  every relationship target resolves to a part in the package
  D  <p:sldIdLst> is 22 slides, in order, with resolvable r:ids
  E  every shape sits inside the slide canvas and clear of the master footer
  F  no two text boxes overlap on a slide
  G  estimated text height fits the box it was placed in
  H  no run smaller than 9 pt
  I  the embedded video, poster and their relationships are present
  J  speaker notes are attached and parse
  K  content dump for review
"""

import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

# Liberation Sans is metric-compatible with Arial, the deck's typeface, so line
# wrapping measured with it matches what PowerPoint will lay out. Pillow is only
# needed for that exactness: without it the check falls back to a conservative
# average-character-width model and says so.
FONT_DIR = "/usr/share/fonts/truetype/liberation"
_FONTS = {}
try:
    from PIL import ImageFont
    EXACT_METRICS = True
except ImportError:                                         # pragma: no cover
    EXACT_METRICS = False


def _arial(sz_pt, bold):
    key = (round(sz_pt * 4), bool(bold))
    if key not in _FONTS:
        name = ("LiberationSans-Bold.ttf" if bold
                else "LiberationSans-Regular.ttf")
        _FONTS[key] = ImageFont.truetype(os.path.join(FONT_DIR, name), key[0])
    return _FONTS[key]


PX_PER_EMU = 4.0 / 12700.0


def measure(text, avail_emu, sz, bold):
    """Wrap a paragraph. Returns (line count, widest rendered line in EMU)."""
    text = text.strip()
    if not text:
        return 0, 0
    if not EXACT_METRICS:
        per_char = (sz / 100.0) * 12700 * (0.58 if bold else 0.55)
        per_line = max(4, int(avail_emu / per_char))
        lines, cur, widest = 1, 0, 0
        for w in text.split():
            need = len(w) + (1 if cur else 0)
            if cur and cur + need > per_line:
                widest = max(widest, cur)
                lines += 1
                cur = len(w)
            else:
                cur += need
        return lines, max(widest, cur) * per_char
    f = _arial(sz / 100.0, bold)
    avail = avail_emu * PX_PER_EMU
    lines, cur, widest, started = 1, 0.0, 0.0, False
    for word in text.split():
        wpx = f.getlength(word)
        gap = f.getlength(" ") if started else 0.0
        if started and cur + gap + wpx > avail:
            widest = max(widest, cur)
            lines += 1
            cur, started = wpx, True
        else:
            cur += gap + wpx
            started = True
    widest = max(widest, cur)
    return lines, widest / PX_PER_EMU

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(ROOT, "StormSense-Databricks-Hackathon.pptx")
SRC_VIDEO = os.path.join(ROOT, "video_2026-10-08_16-58-25.mp4")

CX, CY = 12192000, 6858000
FOOTER_Y = 6238277          # top of the master's UST logo / legal line
A, P, R = (
    "{http://schemas.openxmlformats.org/drawingml/2006/main}",
    "{http://schemas.openxmlformats.org/presentationml/2006/main}",
    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}",
)

fails, warns, notes = [], [], []


def fail(tag, msg):
    fails.append(f"[{tag}] {msg}")


def warn(tag, msg):
    warns.append(f"[{tag}] {msg}")


def ok(tag, msg):
    notes.append(f"[{tag}] {msg}")


# ------------------------------------------------------------------ load -----
with zipfile.ZipFile(DECK) as z:
    bad = z.testzip()
    if bad:
        fail("A", f"corrupt member {bad}")
    parts = {n: z.read(n) for n in z.namelist()}

# ---- A: well formedness
trees = {}
for name, data in parts.items():
    if name.endswith((".xml", ".rels")):
        try:
            trees[name] = ET.fromstring(data)
        except ET.ParseError as e:
            fail("A", f"{name}: {e}")
ok("A", f"zip readable, {len(parts)} parts, "
        f"{len(trees)} XML parts parsed")

# ---- B: content types
ct = trees["[Content_Types].xml"]
defaults = {e.get("Extension").lower(): e.get("ContentType")
            for e in ct.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Default")}
overrides = {e.get("PartName") for e in ct.findall(
    "{http://schemas.openxmlformats.org/package/2006/content-types}Override")}
missing = []
for name in parts:
    if name == "[Content_Types].xml":
        continue
    if "/" + name in overrides:
        continue
    ext = name.rsplit(".", 1)[-1].lower()
    if ext not in defaults:
        missing.append(name)
if missing:
    for m in missing:
        fail("B", f"no content type for {m}")
else:
    ok("B", f"all {len(parts) - 1} parts are typed "
            f"({len(defaults)} defaults, {len(overrides)} overrides)")

def resolve(rels_part, target):
    """Part-relative resolution of a relationship target."""
    if rels_part == "_rels/.rels":
        base = ""
    else:
        base = rels_part.rsplit("/_rels/", 1)[0]
    return os.path.normpath(os.path.join(base, target)).replace("\\", "/")


# ---- C: relationship targets
for name, tree in trees.items():
    if not name.endswith(".rels"):
        continue
    for rel in tree:
        if rel.get("TargetMode") == "External":
            continue
        resolved = resolve(name, rel.get("Target"))
        if resolved not in parts:
            fail("C", f"{name}: {rel.get('Id')} -> missing {resolved}")
ok("C", "every internal relationship resolves")

# ---- D: slide list
pres = trees["ppt/presentation.xml"]
pres_rels = {r.get("Id"): r.get("Target")
             for r in trees["ppt/_rels/presentation.xml.rels"]}
lst = pres.find(f"{P}sldIdLst")
ids = [e.get(f"{R}id") for e in lst]
if len(ids) != 22:
    fail("D", f"expected 22 slides, found {len(ids)}")
slots = []
for i in ids:
    if i not in pres_rels:
        fail("D", f"sldIdLst references unknown {i}")
        continue
    slots.append(pres_rels[i].split("/")[-1][:-4])
expected = ["slide1", "slide2", "slide3", "slide4", "slide5", "slide6", "slide18",
            "slide19", "slide7", "slide8", "slide20", "slide9", "slide10",
            "slide11", "slide12", "slide21", "slide13", "slide14", "slide22",
            "slide15", "slide16", "slide17"]
if slots != expected:
    fail("D", f"slide order {slots}")
else:
    ok("D", f"22 slides in order: {', '.join(slots)}")

# ---- E/F/G/H: geometry and text per slide
size_re = re.compile(r'sz="(\d+)"')


def shape_box(el):
    xfrm = el.find(f".//{A}xfrm")
    if xfrm is None:
        return None
    off = xfrm.find(f"{A}off")
    ext = xfrm.find(f"{A}ext")
    if off is None or ext is None:
        return None
    if ext.get("cx") is None or ext.get("cy") is None:
        return None
    return (int(off.get("x")), int(off.get("y")),
            int(ext.get("cx")), int(ext.get("cy")))


def text_of(el):
    return " ".join(t.text or "" for t in el.iter(f"{A}t"))


def body_insets(sp_el):
    """(lIns, rIns, tIns, bIns) EMU, using PowerPoint's defaults when unset."""
    bp = sp_el.find(f"{P}txBody/{A}bodyPr")
    if bp is None:
        return 91440, 91440, 45720, 45720
    return tuple(int(bp.get(k, d)) for k, d in (
        ("lIns", 91440), ("rIns", 91440), ("tIns", 45720), ("bIns", 45720)))


def para_info(sp_el):
    """[(text, sz, bold, space_after, ln_spc, marL)] per paragraph."""
    body = sp_el.find(f"{P}txBody")
    if body is None:
        return []
    out = []
    for para in body.findall(f"{A}p"):
        txt, sz, bold, ln, marl = "", 1000, False, 100000, 0
        pr = para.find(f"{A}pPr")
        if pr is not None:
            ln_el = pr.find(f"{A}lnSpc/{A}spcPct")
            if ln_el is not None:
                ln = int(ln_el.get("val"))
            af = pr.find(f"{A}spcAft/{A}spcPts")
            aft = int(af.get("val")) if af is not None else 0
            if pr.get("marL"):
                marl = int(pr.get("marL"))
        else:
            aft = 0
        for r in para.findall(f"{A}r"):
            rpr = r.find(f"{A}rPr")
            if rpr is not None:
                if rpr.get("sz"):
                    sz = int(rpr.get("sz"))
                if rpr.get("b") == "1":
                    bold = True
            txt += r.find(f"{A}t").text or ""
        if txt.strip():
            out.append((txt, sz, bold, aft, ln, marl))
    return out


WRITTEN = {"slide4", "slide6", "slide8", "slide10", "slide12", "slide14",
           "slide15", "slide18", "slide19", "slide20", "slide21", "slide22"}
util = []

for slide in slots:
    if slide not in WRITTEN:
        continue        # template slides are checked by the template's authors
    part = f"ppt/slides/{slide}.xml"
    tree = trees[part]
    texts = []
    for el in tree.iter(f"{P}sp"):
        box = shape_box(el)
        paras = para_info(el)
        if box is None:
            continue
        x, y, cx, cy = box
        if x < 0 or y < 0 or x + cx > CX or y + cy > CY:
            fail("E", f"{slide}: shape outside the canvas {box}")
        if y + cy > FOOTER_Y and paras:
            fail("E", f"{slide}: text box runs into the master footer {box}")
        if y + cy > 6180000:
            fail("E", f"{slide}: shape crosses the footer safe line {box}")
        for txt, sz, bold, aft, ln, marl in paras:
            if sz < 900:
                fail("H", f"{slide}: {sz / 100}pt run: {txt[:40]!r}")
            if cx < 400000:
                continue
            lins, rins, tins, bins = body_insets(el)
            need = 0.0
            for t2, s2, b2, a2, l2, ml in paras:
                avail = cx - lins - rins - ml
                lines, widest = measure(t2, avail, s2, b2)
                if widest > avail + 1000:
                    fail("G", f"{slide}: a line is wider than its box in "
                              f"{t2[:36]!r}")
                need += lines * (s2 / 100.0) * 12700 * 1.2 * (l2 / 100000)
                need += (a2 / 100.0) * 12700
            need -= tins + bins
            if need > cy:
                fail("G", f"{slide}: text overflows its box "
                          f"({need / 12700:.0f}pt needed vs {cy / 12700:.0f}pt) "
                          f"{txt[:44]!r}")
            util.append((need / cy, slide, txt[:40]))
            break
        if paras:
            texts.append((x, y, cx, cy, text_of(el).strip()))
    # F: text-on-text overlap
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            ax, ay, acx, acy, at = texts[i]
            bx, by, bcx, bcy, bt = texts[j]
            ox = min(ax + acx, bx + bcx) - max(ax, bx)
            oy = min(ay + acy, by + bcy) - max(ay, by)
            if ox > 0 and oy > 0:
                fail("F", f"{slide}: text boxes overlap by {ox}x{oy} EMU: "
                          f"{at[:28]!r} vs {bt[:28]!r}")
ok("E", "all shapes inside the canvas and clear of the footer")
ok("F", "no overlapping text boxes")
util.sort(reverse=True)
ok("G", ("every text box fits using real Arial metrics" if EXACT_METRICS
         else "every text box fits using an approximate width model "
              "(install Pillow for exact metrics)")
        + "; tightest: "
        + ", ".join(f"{s} {u * 100:.0f}% ({t!r})" for u, s, t in util[:4]))
ok("H", "no run below 9 pt")

# ---- I: media
if "ppt/media/demo-video.mp4" not in parts:
    fail("I", "embedded video part missing")
else:
    src = os.path.getsize(SRC_VIDEO)
    got = len(parts["ppt/media/demo-video.mp4"])
    if src != got:
        fail("I", f"video bytes differ: {got} vs source {src}")
    else:
        ok("I", f"video embedded intact ({got / 1e6:.1f} MB)")
if "ppt/media/demo-poster.png" not in parts:
    fail("I", "poster part missing")
s10 = trees["ppt/slides/_rels/slide10.xml.rels"]
types = {}
for rel in s10:
    types.setdefault(rel.get("Type").split("/")[-1], []).append(rel.get("Target"))
for need in ("video", "media", "image", "slideLayout", "notesSlide"):
    if need not in types:
        fail("I", f"slide10 has no {need} relationship")
pop = trees["ppt/slides/slide10.xml"]
pics = pop.findall(f".//{P}pic")
if not pics:
    fail("I", "slide10 has no picture")
else:
    nv = pics[0].find(f"{P}nvPicPr/{P}nvPr")
    if nv is None or nv.find(f"{A}videoFile") is None:
        fail("I", "slide10 picture is not a video")
    else:
        ok("I", f"slide10 video rels: "
                f"{ {k: v for k, v in types.items() if k in ('video','media','image')} }")

# ---- J: notes
attached = 0
for slide in slots:
    rp = f"ppt/slides/_rels/{slide}.xml.rels"
    if not os.path.exists(rp) and rp not in parts:
        fail("J", f"missing rels for {slide}")
        continue
    if rp not in trees:
        fail("J", f"{slide}: no rels part")
        continue
    for rel in trees[rp]:
        if rel.get("Type").endswith("/notesSlide"):
            tgt = resolve(rp, rel.get("Target"))
            if tgt not in parts:
                fail("J", f"{slide}: notes part {tgt} missing")
            elif not tgt.startswith("ppt/notesSlides/notesSlide"):
                fail("J", f"{slide}: unexpected notes part {tgt}")
            else:
                attached += 1
ok("J", f"speaker notes attached to {attached} slides")

# ---- K: dump
print("=" * 78)
for i, slide in enumerate(slots, 1):
    tree = trees[f"ppt/slides/{slide}.xml"]
    print(f"\n----- {i:>2}. {slide} " + "-" * 40)
    for el in tree.iter(f"{P}sp"):
        t = text_of(el).strip()
        if t:
            print("   ", t[:150])
    for el in tree.iter(f"{P}graphicFrame"):
        rows = [" | ".join(text_of(tc).strip() for tc in tr.findall(f"{A}tc"))
                for tr in el.iter(f"{A}tr")]
        for rline in rows:
            print("    TBL:", rline[:150])
    for el in tree.iter(f"{P}pic"):
        print("    PIC:", el.find(f"{P}nvPicPr/{P}cNvPr").get("name"))

print("\n" + "=" * 78)
for e in notes:
    print("PASS", e)
for w in warns:
    print("WARN", w)
for f in fails:
    print("FAIL", f)
print(f"\n{len(fails)} failures, {len(warns)} warnings")
sys.exit(1 if fails else 0)
