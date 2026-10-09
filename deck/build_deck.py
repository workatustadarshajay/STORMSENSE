#!/usr/bin/env python3
"""Build the StormSense Databricks Hackathon deck.

Base file : "Databricks Hackathon_Idea #_Idea Title_Presenter Name.pptx" (UST template)
Output    : StormSense-Databricks-Hackathon.pptx

The template is used as the container, so its slide masters, layouts, theme,
footers, section dividers, closing slide and copyright slide are kept exactly
as delivered.  Only the content slides are written — plus new slides placed
inside the existing sections, following the same design language as the earlier
StormSense overview deck (eyebrow label, headline, card grid, footnote).

Run:  python3 deck/build_deck.py
"""

import os
import re
import zipfile

from decklib import (
    SLIDE_CX, CW, M,
    Y_EYEBROW, H_EYEBROW, Y_TITLE, H_TITLE, Y_RULE, Y_TOP, Y_BOTTOM,
    INK, BODY, MUTED, TEAL, TEAL_TEXT, DEEP, MINT, PAPER, WHITE, LINE,
    ALERT, GOOD, FONT,
    esc, run, p_, txbody, sp, rect, title_ph, table, video, slide, notes_slide,
    media_timing, run as _run,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, "Databricks Hackathon_Idea #_Idea Title_Presenter Name.pptx")
OUT = os.path.join(ROOT, "StormSense-Databricks-Hackathon.pptx")
POSTER = os.path.join(HERE, "assets", "demo-poster.png")
VIDEO = os.path.join(ROOT, "video_2026-10-08_16-58-25.mp4")

# ------------------------------------------------------------ layout bands ---
CARD_Y, CARD_H = 1620000, 3300000      # 3- and 2-column card rows
GRID_Y, GRID_H, GRID_GAP = 1620000, 1600000, 200000   # 2x2 grids
NOTE_RULE_Y, NOTE_Y, NOTE_H = 5180000, 5240000, 420000
FOOT_LIMIT = 6180000        # nothing below this: the master's UST logo sits at 6238277


def cols(n, gap=200000, width=CW, x0=M):
    w = (width - (n - 1) * gap) // n
    return [(x0 + i * (w + gap), w) for i in range(n)]


# ---------------------------------------------------------------- elements ---
class Slide:
    """Accumulates shapes and hands out unique shape ids."""

    def __init__(self):
        self.shapes = []
        self._id = 2
        self.timing = None

    def nid(self):
        self._id += 1
        return self._id

    def add(self, xml):
        self.shapes.append(xml)
        return self

    def eyebrow(self, text):
        self.add(sp(self.nid(), "eyebrow", M, Y_EYEBROW, CW, H_EYEBROW,
                    [p_(run(text.upper(), sz=1000, b=True, c=TEAL_TEXT, spc=180),
                        lnSpc=100000)]))
        return self

    def headline(self, text):
        self.add(title_ph(self.nid(), M, Y_TITLE, CW, H_TITLE,
                          [p_(run(text, sz=2600, b=True, c=INK), lnSpc=100000)]))
        return self

    def rule(self):
        self.add(rect(self.nid(), "accent rule", M, Y_RULE, 640080, 38100, TEAL))
        return self

    def head(self, eyebrow, title):
        return self.eyebrow(eyebrow).headline(title).rule()

    def note(self, text, color=MUTED, rule_y=NOTE_RULE_Y, y=NOTE_Y, h=NOTE_H):
        self.add(rect(self.nid(), "note rule", M, rule_y, CW, 9525, LINE))
        self.add(sp(self.nid(), "note", M, y, CW, h,
                    [p_(run(text, sz=950, c=color), lnSpc=108000)]))
        return self

    def text(self, x, y, cx, cy, paras, anchor="t"):
        self.add(sp(self.nid(), "text", x, y, cx, cy, paras, anchor=anchor))
        return self

    def xml(self):
        return slide(self.shapes, self.timing)


def card(sl, x, y, cx, cy, heading, bullets=(), subtitle=None, tint=None,
         accent=TEAL, head_color=INK, sub_color=TEAL_TEXT, rule_color=LINE,
         bullet_sz=1000, pad=137160, head_sz=1400, sub_sz=1050):
    """A bordered card: accent chip, heading, optional subtitle, bullet list."""
    sl.add(rect(sl.nid(), "card", x, y, cx, cy, tint or WHITE, geom="roundRect",
                adj=3200, line=LINE))
    sl.add(rect(sl.nid(), "chip", x + pad, y + 150000, 330200, 45720, accent))
    paras = [p_(run(heading, sz=head_sz, b=True, c=head_color), lnSpc=100000,
                 after=(200 if (subtitle or bullets) else 0))]
    if subtitle:
        paras.append(p_(run(subtitle, sz=sub_sz, b=True, c=sub_color),
                        lnSpc=100000, after=500))
    for b in bullets:
        if isinstance(b, tuple):
            lead, rest = b
            paras.append(p_([run(lead, sz=bullet_sz, b=True, c=INK),
                             run(rest, sz=bullet_sz, c=BODY)],
                            bu="•", marL=170180, indent=-170180, lnSpc=108000,
                            after=500))
        else:
            paras.append(p_(run(b, sz=bullet_sz, c=BODY), bu="•", marL=170180,
                            indent=-170180, lnSpc=108000, after=500))
    sl.add(sp(sl.nid(), "card body", x + pad, y + 300000, cx - 2 * pad,
              cy - 300000 - 137160, paras))
    return sl


def tile(sl, x, y, cx, cy, value, label, source=None, tint=MINT,
         value_color=INK, value_sz=2000, label_sz=950):
    sl.add(rect(sl.nid(), "tile", x, y, cx, cy, tint, geom="roundRect",
                adj=4200, line=LINE))
    paras = [
        p_(run(value, sz=value_sz, b=True, c=value_color), align="ctr",
           lnSpc=100000, after=200),
        p_(run(label, sz=label_sz, c=BODY), align="ctr", lnSpc=100000,
           after=(200 if source else 0)),
    ]
    if source:
        paras.append(p_(run(source, sz=850, c=MUTED), align="ctr", lnSpc=100000))
    sl.add(sp(sl.nid(), "tile text", x + 91440, y + 91440, cx - 182880, cy - 182880,
              paras, anchor="ctr"))
    return sl


def chain(sl, y, cy, steps, gap=180000, box_h=None):
    """A numbered left-to-right chain of equal boxes with arrows between."""
    n = len(steps)
    w = (CW - (n - 1) * gap) // n
    h = box_h or cy
    x = M
    for i, (name, sub) in enumerate(steps):
        sl.add(rect(sl.nid(), "step", x, y, w, h, WHITE, geom="roundRect",
                    adj=3400, line=LINE))
        paras = [
            p_(run(f"{i + 1:02d}", sz=1000, b=True, c=TEAL_TEXT), lnSpc=100000,
               after=200),
            p_(run(name, sz=1150, b=True, c=INK), lnSpc=100000, after=300),
        ]
        if sub:
            paras.append(p_(run(sub, sz=900, c=BODY), lnSpc=110000))
        sl.add(sp(sl.nid(), "step text", x + 91440, y + 120000, w - 182880,
                  h - 240000, paras))
        if i < n - 1:
            sl.add(sp(sl.nid(), "arrow", x + w, y + h // 2 - 120000, gap, 240000,
                      [p_(run("\u2192", sz=1200, b=True, c=TEAL_TEXT),
                          align="ctr", lnSpc=100000)]))
        x += w + gap
    return sl


def big_bars(sl, x, y, cx, cy, rows, max_val, track, head, caption):
    """Horizontal bar chart drawn with rectangles (deterministic, no chart part).

    Each row is its own label line with the bar underneath: the label gets the
    full card width, so nothing has to wrap inside a narrow column.
    """
    sl.add(rect(sl.nid(), "chart card", x, y, cx, cy, WHITE, geom="roundRect",
                adj=3200, line=LINE))
    pad = 137160
    inner = cx - 2 * pad
    sl.add(sp(sl.nid(), "chart head", x + pad, y + 150000, inner, 320000,
              [p_(run(head, sz=1150, b=True, c=INK), lnSpc=100000)]))
    for i, (label, value, color) in enumerate(rows):
        ry = y + 620000 + i * 560000
        sl.add(sp(sl.nid(), "bar label", x + pad, ry, inner, 190000,
                  [p_(run(label, sz=1000, b=True, c=BODY), lnSpc=100000)],
                  ins=(0, 0, 0, 0)))
        by = ry + 250000
        sl.add(rect(sl.nid(), "bar track", x + pad, by, track, 190500, "EEEDE6",
                    geom="roundRect", adj=12000))
        sl.add(rect(sl.nid(), "bar fill", x + pad, by,
                    int(track * value / max_val), 190500, color,
                    geom="roundRect", adj=12000))
        sl.add(sp(sl.nid(), "bar value", x + pad + track + 91440, ry + 230000,
                  700000, 230000,
                  [p_(run(f"{value:.3f}", sz=1100, b=True, c=INK), lnSpc=100000)],
                  ins=(0, 0, 0, 0)))
    sl.add(sp(sl.nid(), "chart caption", x + pad, y + cy - 420000, inner,
              420000, [p_(run(caption, sz=900, c=MUTED), lnSpc=108000)],
              ins=(0, 0, 0, 0)))
    return sl


# ----------------------------------------------------------------- slides ----
def s_cover(sl):
    """Cover: title = the idea, subtitle = the one-line promise."""
    sl.headline("StormSense")
    return sl


def s_team(sl):
    sl.head("Team introduction", "Adarsh Ajay")
    sl.add(rect(sl.nid(), "profile", M, CARD_Y, CW, 900000, PAPER,
                geom="roundRect", adj=4200, line=LINE))
    sl.text(M + 137160, CARD_Y + 200000, CW - 274320, 520000, [
        p_([run("Owner and builder \u00b7 ", sz=1150, b=True, c=INK),
            run("solution architecture, the Databricks layer, the forecasting "
                "model, the API, the planner app and the business case.",
                sz=1150, c=BODY)], lnSpc=108000, after=300),
        p_(run("308638@ust.com  \u00b7  Databricks workspace administrator "
               "(CLI profile \u201cstormsense\u201d)  \u00b7  the whole system "
               "rebuilds from code", sz=950, c=MUTED), lnSpc=100000),
    ])
    grid = cols(3, gap=228600)
    bodies = [
        ("Databricks layer",
         ["15 governed Delta tables in Unity Catalog, 10 serverless notebooks, "
          "a registered model served behind the champion alias, three Lakeflow "
          "jobs and a Genie Ask space \u2014 every asset created from code."]),
        ("Application layer",
         ["A FastAPI gatekeeper with bound-parameter SQL, roles, audited "
          "approvals and OpenAPI-generated types, behind a React 18 / TypeScript "
          "planner app built phone-first."]),
        ("Proof and governance",
         ["16 library tests, 47 API tests, 25 web unit tests and 23 browser "
          "tests, plus a nine-check live smoke script run against the real "
          "workspace."]),
    ]
    for (x, w), (headline, bl) in zip(grid, bodies):
        card(sl, x, 2760000, w, 2160000, headline, bl)
    sl.note("One person built and verified the system shown in this deck. "
            "Everything that follows is either a measured output of it or is "
            "labelled as sample data.")
    return sl


def s_problem(sl):
    sl.head("Idea overview", "Weather moves demand faster than stock moves")
    grid = cols(3, gap=228600)
    bodies = [
        ("Storms pull demand forward",
         ["A named storm in the 7-day forecast spikes generators, tarps, pumps "
          "and plywood for a few days.",
          "It spikes in the stores in its path \u2014 not chain-wide, and not in "
          "every store that stocks the product."]),
        ("Heat drives a second surge",
         ["A heat wave lifts coolers and pumps instead.",
          "Two different weather drivers can hit two different regions in the "
          "same week."]),
        ("Demand is local, stock is local",
         ["A shortage and a surplus can sit one region apart, while both are "
          "true at once.",
          "The window to act is a few days. A manual pass over 50 store \u00d7 "
          "product positions against a 7-day forecast usually finishes after it "
          "has closed."]),
    ]
    for (x, w), (headline, bl) in zip(grid, bodies):
        card(sl, x, CARD_Y, w, CARD_H, headline, bl)
    sl.note("Ten stores across Florida, Texas and California, five "
            "weather-sensitive products, one seven-day decision window. Every "
            "figure in this deck is an output of the running system, measured on "
            "labelled sample data.")
    return sl


def s_solution(sl):
    sl.head("Idea overview", "One question, answered every morning at 6:00 AM")
    chain(sl, CARD_Y, 1750000, [
        ("Weather", "Observed history + the 7-day forecast"),
        ("Forecast", "Demand per store and product"),
        ("Gaps", "Shortage and surplus against the week ahead"),
        ("Transfers", "Nearest spare stock, ranked"),
        ("Planner decides", "Approve or reject on a phone"),
    ])
    card(sl, M, 3570000, CW, 1350000, "The daily cycle", [
        "A scheduled job refreshes weather, rebuilds leak-free features, scores "
        "with the current champion model, finds gaps and writes ranked transfer "
        "recommendations \u2014 idempotent, so re-running changes nothing it "
        "should not.",
        "The planner sees only the last box: a short, ranked list with the "
        "reason attached to every move.",
    ])
    sl.note("This is the whole product in one line: weather in, a ranked "
            "decision out, every morning before the stores open.")
    return sl


def s_novelty(sl):
    sl.head("Why it's different", "A decision, not another dashboard")
    g = cols(2, gap=200000)
    rows = [CARD_Y, CARD_Y + GRID_H + GRID_GAP]
    bodies = [
        ("It ends in a decision, not a dashboard",
         ["The output is a ranked move with its reason in plain words, sized to "
          "the week \u2014 something a planner approves in seconds."]),
        ("The horizon is the decision window",
         ["Features are lagged by the full 7-day horizon so nothing leaks, and "
          "the model is judged on the exact window a move has to land in."]),
        ("Trust is a gate the model has to pass",
         ["It reaches champion only by beating \u201csame as last week\u201d and "
          "the trailing 28-day average on data held out of training."]),
        ("Ask anything, change nothing",
         ["A read-only space answers open questions in the planner's own words "
          "and cannot modify a single row."]),
    ]
    for i, (headline, bl) in enumerate(bodies):
        x, w = g[i % 2]
        card(sl, x, rows[i // 2], w, GRID_H, headline, bl)
    sl.note("The unit of decision is what is new: a per-store, per-product gap "
            "over the weather horizon, resolved to a move a non-technical "
            "planner can approve. It is not a new charting technique.")
    return sl


def s_architecture(sl):
    sl.head("Architecture and solution", "Three layers, one decision")
    grid = cols(3, gap=228600)
    bodies = [
        ("Databricks", "Data and forecasting",
         ["15 Delta tables in Unity Catalog",
          "Leak-free features over a 7-day horizon",
          "Promoted and served through the champion alias"]),
        ("FastAPI gatekeeper", "The only path to the data",
         ["Bound-parameter SQL only",
          "Roles, guarded and idempotent approvals",
          "Every attempt written to an audit trail"]),
        ("React app", "Where the planner works",
         ["Today, Transfers, Store forecast, Ask, History",
          "Plain-language loading, empty and error states",
          "Phone-first and accessibility-tested"]),
    ]
    for (x, w), (headline, sub, bl) in zip(grid, bodies):
        card(sl, x, CARD_Y, w, 2300000, headline, bl, subtitle=sub)
    sl.add(rect(sl.nid(), "chain rule", M, 4080000, CW, 9525, LINE))
    sl.text(M, 4130000, CW, 250000,
            [p_(run("The 6:00 AM daily cycle", sz=1150, b=True, c=INK),
                lnSpc=100000)])
    chain(sl, 4440000, 1, [
        ("Weather", "NWS or sample feed"),
        ("Features", "lagged, no leakage"),
        ("Score", "champion alias"),
        ("Gaps", "short vs surplus"),
        ("Transfers", "ranked and merged"),
        ("Verify", "idempotency check"),
    ], gap=140000, box_h=760000)
    sl.note("The browser never talks to Databricks. The API holds the service "
            "principal, so credentials never reach the client \u2014 and every "
            "statement it runs is parameterised.",
            rule_y=5300000, y=5360000)
    return sl


def s_databricks(sl):
    sl.head("Databricks features", "Every capability does real work")
    rows = [
        ["Databricks capability", "Where it does real work here", "What it buys"],
        ["Unity Catalog",
         "15 Delta tables, the registered model and every grant for the app's "
         "identity in one governed home",
         "One permission model for data, model and app"],
        ["Serverless notebooks",
         "10 notebooks, setup through verify, importing a shared pandas library "
         "from the notebook path",
         "No cluster to size, stop or pay for while idle"],
        ["Lakeflow Jobs (Workflows)",
         "The 6:00 AM daily cycle: six tasks, retries and an email to the owner "
         "on failure",
         "Runs unattended; idempotent when re-run"],
        ["MLflow + Model Registry",
         "Versioned runs and a registered model; the live model is served "
         "through the champion alias",
         "Promote or roll back without a code change"],
        ["Genie (Ask space)",
         "A read-only space over eight tables, created from code, answering the "
         "planner's own questions",
         "Open questions without a query editor"],
        ["Declarative Automation Bundles",
         "Tables, jobs, the model, the Ask space and the app are defined as code "
         "and deployed by bundle",
         "The whole environment is reproducible in one command"],
    ]
    sl.add(table(sl.nid(), "Databricks alignment", M, CARD_Y,
                 [2900000, 4860480, 3700000], rows, row_h=500000,
                 header_h=420000))
    sl.note("Also used: Unity Catalog grants and RBAC for the app's "
            "least-privilege identity, and scikit-learn HistGradientBoosting "
            "with Poisson loss running on the serverless runtime.")
    return sl


def s_video(sl):
    sl.head("Video demo", "The planner's morning, end to end")
    vx, vy, vcx = M, CARD_Y, 6300000
    vcy = int(vcx * 9 / 16)
    vid = sl.nid()
    sl.add(video(vid, "StormSense demo", vx, vy, vcx, vcy,
                 "rId3", "rId4", "rId5"))
    sl.timing = media_timing(vid)
    sl.add(sp(sl.nid(), "video caption", vx, vy + vcy + 120000, vcx, 320000,
              [p_(run("Click to play \u2014 StormSense in 63 seconds, recorded "
                      "from the running application (1920\u00d71080).", sz=950,
                      c=MUTED), lnSpc=108000)]))
    tx = vx + vcx + 220000
    tcw = CW - vcx - 220000
    paras = [p_(run("What you will see", sz=1150, b=True, c=INK), lnSpc=100000,
                 after=700)]
    for lead, rest in [
        ("Today \u2014 ", "11 positions short, 16 holding extra, 23 balanced: "
                          "what needs attention this morning."),
        ("Transfers \u2014 ", "13 ranked moves waiting on a decision, 4 urgent, "
                              "about $54k of stock cover, each with its reason."),
        ("Forecast \u2014 ", "seven days of demand per product for one store, "
                             "and what the model got wrong before."),
        ("Ask \u2014 ", "an open question answered in plain language from the "
                        "same governed tables."),
    ]:
        paras.append(p_([run(lead, sz=1000, b=True, c=INK),
                         run(rest, sz=1000, c=BODY)], bu="\u2022", marL=170180,
                        indent=-170180, lnSpc=108000, after=600))
    sl.add(sp(sl.nid(), "video bullets", tx, vy, tcw, vcy, paras))
    return sl


def s_tests(sl):
    sl.head("Test cases", "What is tested, and how it is proved")
    grid = cols(3, gap=228600)
    bodies = [
        ("The model must earn its place",
         ["Promotion to champion is a test, not a promise: it has to beat "
          "\u201csame as last week\u201d and the trailing 28-day average on the "
          "last 28 days, held out of training."]),
        ("An approval cannot double-apply",
         ["Only still-pending rows change, stamped with a request id, so a "
          "repeat \u2014 or a second person \u2014 is told it is already "
          "handled. Browser tests approve the same transfer twice."]),
        ("The planner's vocabulary is enforced",
         ["A test fails the build if SQL, Delta, Databricks, Genie, MLflow, "
          "warehouse, SKU, MAPE, WAPE, model or API appears anywhere in the "
          "user interface."]),
    ]
    for (x, w), (headline, bl) in zip(grid, bodies):
        card(sl, x, CARD_Y, w, 2500000, headline, bl)
    tiles = cols(4)
    for (x, w), (value, label) in zip(tiles, [
        ("16", "library tests"),
        ("47", "API tests"),
        ("48", "web tests \u00b7 25 unit + 23 browser"),
        ("9 / 9", "live smoke checks on the workspace"),
    ]):
        tile(sl, x, 4240000, w, 900000, value, label)
    sl.note("The smoke script also asserts the two things Q&A is most likely to "
            "probe: Ask answers 10 of 10 sample questions, and Ask cannot change "
            "data.")
    return sl


def s_results(sl):
    sl.head("Results", "Measured, not asserted")
    big_bars(sl, M, CARD_Y, 5760000, 2900000,
             [("Champion model", 0.403, GOOD),
              ("Trailing 28-day average", 0.571, "AEBBC6"),
              ("Same as last week", 0.667, "AEBBC6")],
             max_val=0.70, track=4000000,
             head="Weighted forecast error by method (WAPE)",
             caption="Lower is better. The grey bars are the simple methods the "
                     "business effectively runs on today. Measured on the last "
                     "28 days, held out of training.")
    sx = 6400000
    sw = (11826240 - sx - 200000) // 2
    stats = [
        ("350", "forecasts every run", "10 stores \u00d7 5 products \u00d7 7 days"),
        ("13", "transfer recommendations", "ranked, awaiting a decision"),
        ("4", "marked urgent", "where the shortfall is largest"),
        ("~$54k", "sales protected", "stock the recommended moves cover"),
    ]
    for i, (v, l, s) in enumerate(stats):
        tile(sl, sx + (i % 2) * (sw + 200000), CARD_Y + (i // 2) * (1350000 + 200000),
             sw, 1350000, v, l, source=s)
    sl.note("A single daily run on labelled sample data. The forecast beats both "
            "naive baselines by a wide margin; no figure here is an estimate.")
    return sl


def s_impact(sl):
    sl.head("Business impact", "Revenue protected, effort removed")
    grid = cols(2, gap=200000)
    bodies = [
        ("Revenue impact",
         ["Stock moves to the store the forecast says will sell it, inside the "
          "few days the weather creates \u2014 instead of sitting where demand "
          "has moved away from.",
          "One morning's run covers about $54k of sales across 13 ranked moves; "
          "done by hand it is 50 store \u00d7 product positions against a 7-day "
          "forecast.",
          "Nothing is estimated: the value is the sales the covered stock "
          "represents, read from the run."]),
        ("Cost effectiveness",
         ["The cycle runs unattended at 6:00 AM on serverless compute that stops "
          "when the job ends \u2014 no cluster kept warm between runs.",
          "Every asset is defined in code and created by one command, so there "
          "is no hand-built environment to maintain or drift.",
          "A planner's time goes into deciding a short ranked list, not "
          "assembling one \u2014 and surplus moves off the shelf instead of "
          "being written down."]),
    ]
    for (x, w), (headline, bl) in zip(grid, bodies):
        card(sl, x, CARD_Y, w, CARD_H, headline, bl)
    sl.note("Revenue and cost statements are limited to what the running system "
            "actually outputs. No ROI, adoption or savings figure has been "
            "invented for this deck.")
    return sl


# ------------------------------------------------------- speaker notes -------
NOTE = {
 "slide4": [
  "Introduce yourself in one line: owner of the whole stack, and the person "
  "who ran it.",
  "Stress that everything in this deck was executed: the notebooks ran, the "
  "jobs ran, the tests ran, the smoke script ran.",
  "Set the expectation for the next three minutes: the problem, the flow, then "
  "the running application.",
 ],
 "slide6": [
  "Open with the planner's morning question, not with technology.",
  "The two weather drivers matter: a storm and a heat wave can hit two regions "
  "in the same week, in opposite directions.",
  "Land the constraint: the window is a few days, and 50 positions by hand "
  "does not fit inside it.",
 ],
 "slide18": [
  "Walk the chain left to right. Weather in, ranked decision out.",
  "Emphasise what is behind each box: leak-free features, a champion model "
  "promoted only if it beats the baselines, and an idempotent merge into "
  "pending rows.",
  "The planner only ever sees the last box.",
 ],
 "slide19": [
  "Answer the obvious question before it is asked: this is not another "
  "dashboard.",
  "The unit of decision \u2014 a per-store, per-product gap over the weather "
  "horizon \u2014 is what is new. Be honest that the techniques are standard; "
  "the framing, the constraints and the trust gates are the contribution.",
  "Mention Ask here: it answers open questions and cannot change a row.",
 ],
 "slide8": [
  "Three layers, one decision. The browser never touches Databricks.",
  "Point at the FastAPI layer as the security boundary: bound parameters, "
  "roles, an audit row for every attempt.",
  "Then read the daily cycle: six tasks, 6:00 AM, idempotent.",
 ],
 "slide20": [
  "This is the slide to come back to when the judges ask about Databricks "
  "alignment.",
  "For each row, say where it does real work \u2014 not that it is used, but "
  "what it buys: reproducibility, no idle cost, alias-based rollout, governed "
  "access.",
  "If asked what is missing: the app itself has not been deployed, and that is "
  "a network-policy decision.",
 ],
 "slide10": [
  "Play the 63-second video. It is the whole story: the problem, the flow, "
  "then the application.",
  "While it plays, point at the four things to watch: Today, Transfers, the "
  "forecast view and Ask.",
  "If it cannot play, use this slide's bullets \u2014 they are the video's "
  "content.",
 ],
 "slide12": [
  "Test cases are the argument, not a list. Each card is a claim someone "
  "could challenge.",
  "Give the numbers: 16 + 47 + 48 tests, and 9 of 9 smoke checks on the real "
  "workspace.",
  "Offer the double-approve case as a live Q&A probe.",
 ],
 "slide21": [
  "Read the chart once: 0.403 against 0.667 and 0.571. Lower is better, and "
  "the grey bars are what the business effectively uses today.",
  "Then the run itself: 350 forecasts, 13 recommendations, 4 urgent, about "
  "$54k of stock cover.",
  "Say plainly that the dataset is generated sample data, labelled as such in "
  "the app.",
 ],
 "slide14": [
  "Split the slide in two: revenue on the left, cost on the right.",
  "Revenue: stock reaches the store the forecast says will sell it, inside "
  "the window the weather creates.",
  "Cost: serverless compute that stops when the job ends, everything from "
  "code, and a planner approving a list instead of assembling one.",
  "Do not invent an ROI number \u2014 say what the system outputs.",
 ],
 "slide22": [
  "Show that the architecture survives the sample data leaving.",
  "Be direct about the one blocker: the hosted app is not deployed because "
  "this network filters one upload; the code is written and the workspace is "
  "wired.",
  "Close on the roadmap: real feeds, more stores, go-live alerting.",
 ],
 "slide15": [
  "Thank the panel, state the one-line pitch, then invite questions.",
  "Keep the contact line on screen while you take questions.",
 ],
}

# text substitutions on slides that are kept but lightly edited
EDITS = {
    "slide1": [
        ("<a:t>Databricks Hackathon</a:t>", "<a:t>StormSense</a:t>"),
        ("<a:t>Solution and POC</a:t>",
         "<a:t>Weather-aware inventory planning</a:t>"),
        ("<a:t>08 October 2026</a:t>",
         "<a:t>Databricks Hackathon \u00b7 Adarsh Ajay \u00b7 09 October 2026</a:t>"),
    ],
    "slide2": [("<a:t>Demo</a:t>", "<a:t>Video Demo</a:t>")],
}

SLIDE_REL_TYPE = ("http://schemas.openxmlformats.org/officeDocument/2006/"
                  "relationships/slide")
TITLES = {
    "slide1": "StormSense \u2014 weather-aware inventory planning",
    "slide4": "Adarsh Ajay",
    "slide6": "Weather moves demand faster than stock moves",
    "slide18": "One question, answered every morning at 6:00 AM",
    "slide19": "A decision, not another dashboard",
    "slide8": "Three layers, one decision",
    "slide20": "Every capability does real work",
    "slide10": "The planner's morning, end to end",
    "slide12": "What is tested, and how it is proved",
    "slide21": "Measured, not asserted",
    "slide14": "Revenue protected, effort removed",
    "slide22": "What changes when this leaves the sample data",
    "slide2": "Agenda",
    "slide3": "Team introduction",
    "slide5": "Idea Overview",
    "slide7": "Architecture and Solution",
    "slide9": "Video Demo",
    "slide11": "Test Case and Results",
    "slide13": "Benefits and Impacts",
    "slide15": "Thank you",
    "slide16": "Together, we build for boundless impact",
    "slide17": "Copyright and confidentiality notice",
}


def s_scale(sl):
    sl.head("Scale-up", "What changes when this leaves the sample data")
    g = cols(2, gap=200000)
    rows = [CARD_Y, CARD_Y + GRID_H + GRID_GAP]
    bodies = [
        ("Real feeds",
         ["Swap the sample generator and the sample weather provider for the "
          "retailer's sales, stock and a live forecast feed. The feature, model "
          "and planning code does not change."]),
        ("More of the estate",
         ["Regions, stores and products are dimensions in Unity Catalog, so a "
          "larger estate is more data through the same six-task job \u2014 not "
          "a rewrite."]),
        ("Deploy the app",
         ["The app bundle is written and the workspace is wired. Deployment is "
          "currently blocked by this network's upload filter on one file, not by "
          "the application."]),
        ("Watch it",
         ["The daily job already retries and emails the owner on failure; "
          "go-live adds alerting on forecast drift and on recommendation volume "
          "per run."]),
    ]
    for i, (headline, bl) in enumerate(bodies):
        x, w = g[i % 2]
        card(sl, x, rows[i // 2], w, GRID_H, headline, bl)
    sl.note("Honest status, for Q&A: the pipeline, model, API and app are "
            "verified running against the real workspace. The hosted Databricks "
            "App has not been deployed \u2014 that needs a security decision, "
            "not more code.")
    return sl


def s_thanks(sl):
    """Fills the template's contact placeholder on the Thank-you layout.

    No explicit xfrm: the placeholder inherits position and styling from
    slideLayout43, exactly as the template intends.
    """
    sid = sl.nid()
    body = txbody([
        p_(run("Adarsh Ajay  ·  308638@ust.com", sz=1400, b=True, c=INK),
           lnSpc=100000, after=400),
        p_(run("StormSense — weather-aware inventory planning, every morning "
               "at 6:00 AM", sz=1100, c=BODY), lnSpc=100000),
    ])
    head = (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Contact"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        '<p:nvPr><p:ph type="body" sz="quarter" idx="10"/></p:nvPr>'
        '</p:nvSpPr><p:spPr/>'
    )
    sl.add(head + body + "</p:sp>")
    return sl


# =============================================================== assembly ===
# (mode, part name, builder, layout, speaker notes)
SLIDES = [
    ("edit",  "slide1",  None,           None,            None),
    ("edit",  "slide2",  None,           None,            None),
    ("keep",  "slide3",  None,           None,            None),
    ("write", "slide4",  s_team,         "slideLayout39", NOTE["slide4"]),
    ("keep",  "slide5",  None,           None,            None),
    ("write", "slide6",  s_problem,      "slideLayout39", NOTE["slide6"]),
    ("write", "slide18", s_solution,     "slideLayout39", NOTE["slide18"]),
    ("write", "slide19", s_novelty,      "slideLayout39", NOTE["slide19"]),
    ("keep",  "slide7",  None,           None,            None),
    ("write", "slide8",  s_architecture, "slideLayout39", NOTE["slide8"]),
    ("write", "slide20", s_databricks,   "slideLayout39", NOTE["slide20"]),
    ("keep",  "slide9",  None,           None,            None),
    ("write", "slide10", s_video,        "slideLayout39", NOTE["slide10"]),
    ("keep",  "slide11", None,           None,            None),
    ("write", "slide12", s_tests,        "slideLayout39", NOTE["slide12"]),
    ("write", "slide21", s_results,      "slideLayout39", NOTE["slide21"]),
    ("keep",  "slide13", None,           None,            None),
    ("write", "slide14", s_impact,       "slideLayout39", NOTE["slide14"]),
    ("write", "slide22", s_scale,        "slideLayout39", NOTE["slide22"]),
    ("write", "slide15", s_thanks,       "slideLayout43", NOTE["slide15"]),
    ("keep",  "slide16", None,           None,            None),
    ("keep",  "slide17", None,           None,            None),
]

NS = "http://schemas.openxmlformats.org/package/2006/relationships"
RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
CT_SLIDE = ("application/vnd.openxmlformats-officedocument.presentationml."
            "slide+xml")
CT_NOTES = ("application/vnd.openxmlformats-officedocument.presentationml."
            "notesSlide+xml")


def rels_xml(entries):
    body = "".join(
        f'<Relationship Id="{i}" Type="{RT}{t}" Target="{tg}"/>'
        for i, t, tg in entries
    )
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            f'<Relationships xmlns="{NS}">{body}</Relationships>')


def build():
    for path, label in ((TPL, "template"), (POSTER, "poster"), (VIDEO, "video")):
        if not os.path.exists(path):
            raise SystemExit(f"missing {label}: {path}")

    with zipfile.ZipFile(TPL) as z:
        parts = {n: z.read(n) for n in z.namelist()}

    # existing slide part name -> relationship id
    slide_rid = {}
    for m in re.finditer(
        r'<Relationship Id="([^"]+)" Type="([^"]+)" Target="([^"]+)"',
        parts["ppt/_rels/presentation.xml.rels"].decode(),
    ):
        if m.group(2) == RT + "slide":
            slide_rid[m.group(3).split("/")[-1][:-4]] = m.group(1)

    next_rid = 31
    notes_no = 6
    ct_extra = []
    order = []
    media_added = False

    for mode, name, builder, layout, notes in SLIDES:
        part = f"ppt/slides/{name}.xml"
        order.append(name)

        if mode == "keep":
            continue
        if mode == "edit":
            xml = parts[part].decode()
            for find, repl in EDITS[name]:
                if find not in xml:
                    raise SystemExit(f"{name}: edit target not found -> {find}")
                xml = xml.replace(find, repl)
            parts[part] = xml.encode()
            continue

        sl = Slide()
        builder(sl)
        parts[part] = sl.xml().encode()
        if name not in slide_rid:
            slide_rid[name] = f"rId{next_rid}"
            next_rid += 1
            ct_extra.append((part, CT_SLIDE))

        entries = [("rId1", "slideLayout", f"../slideLayouts/{layout}.xml")]
        if notes:
            nfile = f"notesSlide{notes_no}.xml"
            notes_no += 1
            npart = f"ppt/notesSlides/{nfile}"
            parts[npart] = notes_slide(notes).encode()
            parts[f"ppt/notesSlides/_rels/{nfile}.rels"] = rels_xml([
                ("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"),
                ("rId2", "slide", f"../slides/{name}.xml"),
            ]).encode()
            ct_extra.append((npart, CT_NOTES))
            entries.append(("rId2", "notesSlide", f"../notesSlides/{nfile}"))

        if name == "slide10":
            parts["ppt/media/demo-video.mp4"] = open(VIDEO, "rb").read()
            parts["ppt/media/demo-poster.png"] = open(POSTER, "rb").read()
            entries += [
                ("rId3", "video", "../media/demo-video.mp4"),
                ("rId4", "image", "../media/demo-poster.png"),
                ("rId5", "media", "../media/demo-video.mp4"),
            ]
            media_added = True

        parts[f"ppt/slides/_rels/{name}.xml.rels"] = rels_xml(entries).encode()

    # ---- [Content_Types].xml ----
    ct = parts["[Content_Types].xml"].decode()
    extra = ""
    if media_added and 'Extension="mp4"' not in ct:
        extra += '<Default Extension="mp4" ContentType="video/mp4"/>'
    for part, ctype in ct_extra:
        if f'PartName="/{part}"' in ct:
            raise SystemExit(f"content type already declared: {part}")
        extra += f'<Override PartName="/{part}" ContentType="{ctype}"/>'
    parts["[Content_Types].xml"] = ct.replace("</Types>", extra + "</Types>").encode()

    # ---- presentation.xml + its rels ----
    sld_ids = "".join(
        f'<p:sldId id="{300 + i}" r:id="{slide_rid[n]}"/>'
        for i, n in enumerate(order)
    )
    pres = parts["ppt/presentation.xml"].decode()
    pres, hits = re.subn(r"<p:sldIdLst>.*?</p:sldIdLst>",
                         f"<p:sldIdLst>{sld_ids}</p:sldIdLst>", pres, flags=re.S)
    if hits != 1:
        raise SystemExit(f"expected one sldIdLst, found {hits}")
    parts["ppt/presentation.xml"] = pres.encode()

    prels = parts["ppt/_rels/presentation.xml.rels"].decode()
    prels, _ = re.subn(
        r'<Relationship Id="[^"]+" Type="[^"]*?/slide" Target="[^"]+"/>',
        "", prels)
    prels = prels.replace("</Relationships>", "".join(
        f'<Relationship Id="{slide_rid[n]}" Type="{RT}slide" '
        f'Target="slides/{n}.xml"/>' for n in order) + "</Relationships>")
    parts["ppt/_rels/presentation.xml.rels"] = prels.encode()

    # ---- doc properties ----
    app = parts["docProps/app.xml"].decode()
    n = len(order)
    app = app.replace("<Slides>17</Slides>", f"<Slides>{n}</Slides>")
    app = app.replace(
        "<vt:lpstr>Slide Titles</vt:lpstr></vt:variant><vt:variant><vt:i4>17</vt:i4>",
        f"<vt:lpstr>Slide Titles</vt:lpstr></vt:variant><vt:variant><vt:i4>{n}</vt:i4>",
    )
    m = re.search(r'<TitlesOfParts><vt:vector size="(\d+)" baseType="lpstr">'
                  r"(.*?)</vt:vector></TitlesOfParts>", app, re.S)
    if not m:
        raise SystemExit("could not find TitlesOfParts in app.xml")
    items = re.findall(r"<vt:lpstr>(.*?)</vt:lpstr>", m.group(2), re.S)
    prefix = items[: len(items) - 17]
    titles = [TITLES.get(x, "PowerPoint Presentation") for x in order]
    vec = "".join(f"<vt:lpstr>{esc(t)}</vt:lpstr>" for t in prefix + titles)
    app = app[: m.start()] + (
        f'<TitlesOfParts><vt:vector size="{len(prefix) + n}" baseType="lpstr">'
        f"{vec}</vt:vector></TitlesOfParts>"
    ) + app[m.end():]
    parts["docProps/app.xml"] = app.encode()

    core = parts["docProps/core.xml"].decode()
    core = core.replace("<dc:title>DevOps Assessment</dc:title>",
                        "<dc:title>StormSense \u2014 weather-aware inventory "
                        "planning (Databricks Hackathon)</dc:title>")
    parts["docProps/core.xml"] = core.encode()

    # ---- write ----
    names = ["[Content_Types].xml"] + [x for x in parts if x != "[Content_Types].xml"]
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for x in names:
            z.writestr(x, parts[x])
    print(f"wrote {OUT}  ({len(order)} slides, {os.path.getsize(OUT) / 1e6:.1f} MB)")
    return OUT


if __name__ == "__main__":
    build()
