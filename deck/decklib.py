"""Low-level OOXML helpers.

Everything here emits PresentationML / DrawingML fragments that are valid inside
a `<p:spTree>`.  Units are EMU (1 inch = 914400, 1 pt = 12700).
"""

# ---------------------------------------------------------------- geometry ---
SLIDE_CX, SLIDE_CY = 12192000, 6858000  # 13.333in x 7.5in (16:9)
M = 365760                              # side margin (matches the template)
CW = SLIDE_CX - 2 * M                   # content width = 11460480

Y_EYEBROW, H_EYEBROW = 420000, 230000
Y_TITLE, H_TITLE = 690000, 620000
Y_RULE = 1400000
Y_TOP = 1620000                         # top of the content band
Y_BOTTOM = 5700000                      # content must end above this
Y_NOTE, H_NOTE = 5750000, 320000        # footnote line

# ----------------------------------------------------------------- palette ---
# UST template theme colours, plus text-safe tones that pass WCAG AA on white.
INK = "231F20"        # UST dk1  - headings
BODY = "3F4A52"       # body copy           9.0:1 on white
MUTED = "5A666E"      # captions/footnotes  5.8:1 on white
TEAL = "0097AC"       # UST accent1 - fills, rules (decorative only)
TEAL_TEXT = "00697A"  # teal that passes as text  6.4:1
DEEP = "003C51"       # UST accent4 - dark card fill
MINT = "E4F4F6"       # light teal tint
PAPER = "F2F1E9"      # warm tint
WHITE = "FFFFFF"
LINE = "DEDCD0"       # hairline border
ALERT = "B3321F"      # urgent / risk   6.6:1
GOOD = "01795A"       # positive        5.3:1

FONT = "Arial"


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ------------------------------------------------------------------ runs ----
def run(text, sz=1000, b=False, c=BODY, cap=None, spc=None, u=None, i=False):
    """One styled run of text."""
    r = (
        f'<a:r><a:rPr lang="en-US" sz="{sz}" b="{1 if b else 0}"'
        f' i="{1 if i else 0}" dirty="0"'
    )
    if cap:
        r += f' cap="{cap}"'
    if u:
        r += f' u="{u}"'
    if spc is not None:
        r += f' spc="{spc}"'
    r += f'><a:solidFill><a:srgbClr val="{c}"/></a:solidFill>'
    r += f'<a:latin typeface="{FONT}"/><a:cs typeface="{FONT}"/></a:rPr>'
    r += f"<a:t>{esc(text)}</a:t></a:r>"
    return r


def p_(runs, align="l", marL=None, indent=None, bu=None, lnSpc=None,
       before=None, after=None):
    """One paragraph. `runs` is a run() string, a list of them, or a bare str."""
    x = "<a:p><a:pPr"
    if marL is not None:
        x += f' marL="{marL}"'
    if indent is not None:
        x += f' indent="{indent}"'
    if align:
        x += f' algn="{align}"'
    x += ">"
    if lnSpc:
        x += f'<a:lnSpc><a:spcPct val="{lnSpc}"/></a:lnSpc>'
    if before is not None:
        x += f'<a:spcBef><a:spcPts val="{before}"/></a:spcBef>'
    if after is not None:
        x += f'<a:spcAft><a:spcPts val="{after}"/></a:spcAft>'
    if bu:
        x += f'<a:buFont typeface="{FONT}"/><a:buChar char="{esc(bu)}"/>'
    else:
        x += "<a:buNone/>"
    x += "</a:pPr>"
    if isinstance(runs, str):
        runs = [runs]
    x += "".join(runs) + "</a:p>"
    return x


def txbody(paras, anchor="t", ins=(137160, 137160, 68580, 68580), autofit=True):
    l, r, t, b = ins
    bp = (
        f'<a:bodyPr wrap="square" lIns="{l}" tIns="{t}" rIns="{r}" bIns="{b}"'
        f' anchor="{anchor}">'
    )
    if autofit:
        bp += "<a:normAutofit/>"
    bp += "</a:bodyPr>"
    return f'<p:txBody>{bp}<a:lstStyle/>{"".join(paras)}</p:txBody>'


# ---------------------------------------------------------------- shapes -----
def sp(sid, name, x, y, cx, cy, paras=None, geom="rect", adj=None, fill=None,
       line=None, line_w=12700, anchor="t", ins=(137160, 137160, 68580, 68580),
       autofit=True):
    """A shape with an optional text body."""
    prst = "<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom>"
    if geom == "roundRect":
        a = f'<a:gd name="adj" fmla="val {adj if adj is not None else 4000}"/>'
        prst = f'<a:prstGeom prst="roundRect"><a:avLst>{a}</a:avLst></a:prstGeom>'
    elif geom == "ellipse":
        prst = '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    fillx = (
        f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
        if fill
        else "<a:noFill/>"
    )
    if line:
        lnx = (
            f'<a:ln w="{line_w}"><a:solidFill><a:srgbClr val="{line}"/>'
            f"</a:solidFill></a:ln>"
        )
    else:
        lnx = "<a:ln><a:noFill/></a:ln>"

    spPr = (
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/>'
        f"</a:xfrm>{prst}{fillx}{lnx}<a:effectLst/></p:spPr>"
    )
    body = txbody(paras, anchor=anchor, ins=ins, autofit=autofit) if paras else \
        "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>"

    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)}"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>{spPr}{body}</p:sp>'
    )


def title_ph(sid, x, y, cx, cy, paras):
    """The slide's title placeholder, explicitly positioned.

    Using the real placeholder (rather than a plain text box) keeps the master's
    title styling, the outline view and the accessibility tree intact.
    """
    spPr = f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm></p:spPr>'
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Title"/>'
        f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        f'<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
        f'{spPr}{txbody(paras)}</p:sp>'
    )


def rect(sid, name, x, y, cx, cy, fill, geom="rect", adj=None, line=None,
         line_w=12700):
    return sp(sid, name, x, y, cx, cy, paras=None, geom=geom, adj=adj,
              fill=fill, line=line, line_w=line_w)


def hairline(sid, x, y, cx, color=LINE, w=9525):
    return rect(sid, "hairline", x, y, cx, w, color)


# ------------------------------------------------------------------ table ----
NS_TBL = "http://schemas.openxmlformats.org/drawingml/2006/table"
TBL_STYLE_NONE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # No Style, No Grid


def _tc(text, sz=1000, b=False, c=BODY, fill=None, align="l", w_ins=91440,
        anchor="ctr", borders=None):
    tcPr = f'<a:tcPr marL="{w_ins}" marR="{w_ins}" marT="45720" marB="45720" anchor="{anchor}">'
    for tag in ("lnL", "lnR", "lnT", "lnB"):
        col = (borders or {}).get(tag)
        if col:
            tcPr += (
                f'<a:{tag} w="9525" cap="flat" cmpd="sng" algn="ctr">'
                f'<a:solidFill><a:srgbClr val="{col}"/></a:solidFill>'
                f'<a:prstDash val="solid"/></a:{tag}>'
            )
    if fill:
        tcPr += f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
    tcPr += "</a:tcPr>"
    para = p_(run(text, sz=sz, b=b, c=c), align=align, lnSpc=100000)
    return (
        f"<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>{para}</a:txBody>{tcPr}</a:tc>"
    )


def table(sid, name, x, y, cols, rows, row_h, header_h=None, head_fill=DEEP,
          head_color=WHITE, border=LINE, band=PAPER, head_sz=1000, body_sz=950,
          aligns=None):
    """cols: list of widths (sum must equal the table width).
    rows: list of lists of cell strings (header is passed as rows[0]).
    """
    aligns = aligns or ["l"] * len(cols)
    grid = "".join(f'<a:gridCol w="{w}"/>' for w in cols)
    trs = []
    for i, row in enumerate(rows):
        h = (header_h or row_h) if i == 0 else row_h
        cells = []
        for j, cell in enumerate(row):
            if i == 0:
                cells.append(_tc(cell, sz=head_sz, b=True, c=head_color,
                                 fill=head_fill, align=aligns[j]))
            else:
                fill = band if (i % 2 == 1) else None
                cells.append(_tc(cell, sz=body_sz, b=False, c=BODY, fill=fill,
                                 align=aligns[j]))
        trs.append(f'<a:tr h="{h}">{"".join(cells)}</a:tr>')
    tbl = (
        f'<a:tbl><a:tblPr firstRow="0" bandRow="0">'
        f'<a:tableStyleId>{TBL_STYLE_NONE}</a:tableStyleId></a:tblPr>'
        f"<a:tblGrid>{grid}</a:tblGrid>{''.join(trs)}</a:tbl>"
    )
    cx = sum(cols)
    cy = (header_h or row_h) + row_h * (len(rows) - 1)
    return (
        f'<p:graphicFrame><p:nvGraphicFramePr>'
        f'<p:cNvPr id="{sid}" name="{esc(name)}"/>'
        f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>'
        f"<p:nvPr/></p:nvGraphicFramePr>"
        f'<p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
        f'<a:graphic><a:graphicData uri="{NS_TBL}">{tbl}</a:graphicData></a:graphic>'
        f"</p:graphicFrame>"
    )


def video(sid, name, x, y, cx, cy, vid_rid, poster_rid, media_rid):
    """An embedded video: `a:videoFile` links the media, `p14:media` embeds it."""
    return (
        f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{esc(name)}">'
        f'<a:hlinkClick r:id="" action="ppaction://media"/></p:cNvPr>'
        f'<p:cNvPicPr><a:picLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvPicPr>'
        f'<p:nvPr><a:videoFile r:link="{vid_rid}"/>'
        f'<p14:media r:embed="{media_rid}" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main"/>'
        f"</p:nvPr></p:nvPicPr>"
        f'<p:blipFill><a:blip r:embed="{poster_rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
    )


def picture(sid, name, x, y, cx, cy, rid, descr=""):
    """A still image from the deck's media, with alt text for screen readers."""
    return (
        f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{esc(name)}" descr="{esc(descr)}"/>'
        f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
        f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{LINE}"/></a:solidFill></a:ln></p:spPr></p:pic>'
    )


def media_timing(spid):
    """Timing node that makes the embedded video play on click in a show."""
    return (
        '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never"'
        ' nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek">'
        '<p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        '<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
        '</p:stCondLst><p:childTnLst><p:par><p:cTn id="4" fill="hold">'
        '<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        f'<p:video><p:cMediaNode vol="80000"><p:cTn id="5" fill="hold" display="0">'
        '<p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
        f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cMediaNode></p:video>'
        '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'
        '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0">'
        '<p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/>'
        '</p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par>'
        "</p:tnLst></p:timing>"
    )


# ------------------------------------------------------------------ slide ----
SLD_HEAD = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
    '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
    "<p:cSld><p:spTree>"
    '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
    '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
)
SLD_TAIL = "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>"


def slide(shapes, timing=None):
    return SLD_HEAD + "".join(shapes) + SLD_TAIL + (timing or "") + "</p:sld>"


# ------------------------------------------------------------------ notes ----
NSLIDE_NUM_GUID = "{91CB8535-DC0F-AF47-A510-8461A80C06B7}"

NOTES_HEAD = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
    '<p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
    "<p:cSld><p:spTree>"
    '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
    '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
    '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/>'
    '<p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr>'
    '<p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
)


def notes_slide(paragraphs):
    body = "".join(
        p_(run(t, sz=1000, c="000000"), lnSpc=100000, after=600) for t in paragraphs
    )
    return (
        NOTES_HEAD
        + '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
        f"<p:txBody><a:bodyPr/><a:lstStyle/>{body}</p:txBody></p:sp>"
        + '<p:sp><p:nvSpPr><p:cNvPr id="4" name="Slide Number Placeholder 3"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        '<p:nvPr><p:ph type="sldNum" sz="quarter" idx="5"/></p:nvPr></p:nvSpPr>'
        "<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p>"
        f'<a:fld id="{NSLIDE_NUM_GUID}" type="slidenum">'
        '<a:rPr lang="en-US" smtClean="0"/><a:t>1</a:t></a:fld>'
        '<a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>'
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>"
        "</p:notes>"
    )
