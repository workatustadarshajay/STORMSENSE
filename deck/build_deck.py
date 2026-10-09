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
    picture,
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
        self.images = []   # (relationship id, file path) for pictures on this slide

    def nid(self):
        self._id += 1
        return self._id

    def add(self, xml):
        self.shapes.append(xml)
        return self

    def image(self, path, x, y, cx, cy, descr=""):
        rid = f"rId{10 + len(self.images)}"
        self.images.append((rid, path))
        return self.add(picture(self.nid(), os.path.basename(path), x, y, cx, cy, rid, descr))

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
         ["16 governed Delta tables in Unity Catalog, 12 serverless notebooks, "
          "a declarative pipeline of nine data-quality gates, a model served "
          "behind the champion alias, three jobs, a Lakeview dashboard and a "
          "Genie Ask space \u2014 every asset created from code."]),
        ("Application layer",
         ["A FastAPI gatekeeper with bound-parameter SQL, roles, audited "
          "approvals and OpenAPI-generated types, behind a React 18 / TypeScript "
          "planner app \u2014 phone-first, with the what-if simulator and the "
          "three-agent storm desk."]),
        ("Proof and governance",
         ["18 library tests, 70 API and agent tests, 36 web unit tests and 27 "
          "browser tests, plus a nine-check live smoke script run against the "
          "real workspace."]),
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
        "A scheduled job pulls the live forecast, runs nine data-quality gates, "
        "rebuilds leak-free features, scores with the champion, finds gaps, "
        "learns from yesterday's rejections and writes ranked transfers \u2014 "
        "idempotent, so re-running changes nothing it should not.",
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
        ("Trust is a gate the model has to pass",
         ["It reaches champion only by beating \u201csame as last week\u201d and "
          "the trailing 28-day average on data held out of training \u2014 and a "
          "declarative pipeline drops or fails bad rows before a feature is "
          "built."]),
        ("It can rehearse a storm that hasn't happened",
         ["The what-if simulator drives the served forecaster through a "
          "planner's own scenario \u2014 strength, timing, region \u2014 and time "
          "travel compares what the last run planned with what the live "
          "forecast now says."]),
        ("Every rejection makes the next ranking better",
         ["A rejected move stores its reason; routes that keep being rejected "
          "are ranked lower, with a note that says why. Learning never invents "
          "or removes a move."]),
    ]
    for i, (headline, bl) in enumerate(bodies):
        x, w = g[i % 2]
        card(sl, x, rows[i // 2], w, GRID_H, headline, bl)
    sl.note("The unit of decision is what is new: a per-store, per-product gap "
            "over the weather horizon, resolved to a move a planner can approve. "
            "Rehearsing the storm and learning from rejections are what no "
            "off-the-shelf dashboard gives you.")
    return sl


def s_architecture(sl):
    sl.head("Architecture and solution", "Three layers, one decision")
    grid = cols(3, gap=228600)
    bodies = [
        ("Databricks", "Data and forecasting",
         ["16 Delta tables in Unity Catalog",
          "Nine data-quality gates before any feature is built",
          "Leak-free features over a 7-day horizon",
          "Promoted and served through the champion alias"]),
        ("FastAPI gatekeeper", "The only path to the data",
         ["Bound-parameter SQL only",
          "Roles, guarded and idempotent approvals",
          "Every attempt written to an audit trail"]),
        ("React app", "Where the planner works",
         ["Today, Transfers, What-if, Storm desk, Ask, History",
          "Plain-language loading, empty and error states",
          "Phone-first and accessibility-tested"]),
    ]
    for (x, w), (headline, sub, bl) in zip(grid, bodies):
        card(sl, x, CARD_Y, w, 2300000, headline, bl, subtitle=sub)
    sl.add(rect(sl.nid(), "chain rule", M, 4080000, CW, 9525, LINE))
    sl.text(M, 4130000, CW, 250000,
            [p_(run("The 6:00 AM daily cycle", sz=1150, b=True, c=INK),
                lnSpc=100000)])
    chain(sl, 4400000, 1, [
        ("Weather", "live NWS days"),
        ("Quality", "9 gates, no bad rows"),
        ("Features", "lagged, no leakage"),
        ("Score", "champion alias"),
        ("Gaps", "short vs surplus"),
        ("Learn", "route penalties"),
        ("Transfers", "ranked and merged"),
        ("Verify", "idempotency check"),
    ], gap=140000, box_h=840000)
    sl.note("The browser never talks to Databricks. The API holds the service "
            "principal, so credentials never reach the client, and every "
            "statement it runs is parameterised. The quality gate drops bad "
            "rows before a feature is built.",
            rule_y=5300000, y=5360000)
    return sl


def s_databricks(sl):
    sl.head("Databricks features", "Every capability does real work")
    rows = [
        ["Databricks capability", "Where it does real work here", "What it buys"],
        ["Unity Catalog",
         "16 Delta tables, the registered model and every grant for the app's "
         "identity in one governed home",
         "One permission model for data, model and app"],
        ["Lakeflow Declarative Pipeline",
         "Three clean views with nine data-quality expectations; both jobs run "
         "it before features",
         "Bad rows drop out or stop the run; clean views only"],
        ["Serverless notebooks and jobs",
         "12 notebooks; the 6:00 AM cycle runs the quality gate, forecast, gaps "
         "and learning with retries and an email on failure",
         "No cluster to size, stop or pay for while idle"],
        ["MLflow and Model Serving",
         "Versioned runs and the champion alias; a scale-to-zero endpoint served "
         "the forecaster and scored 350 live rows",
         "Promote or roll back in one step; bills only while it runs"],
        ["AI/BI (Lakeview) dashboard",
         "Urgent moves, sales protected, forecast accuracy and DBUs per day, "
         "generated from code",
         "One screen the business can open without asking"],
        ["Genie (Ask space)",
         "A read-only space over the governed tables, created from code, "
         "answering the planner's own questions",
         "Open questions without a query editor"],
        ["System tables and tags",
         "Spend per job from system.billing.usage, filtered to the project tag "
         "on all three jobs",
         "Real cost numbers instead of an estimate"],
        ["Declarative Automation Bundles",
         "Tables, jobs, pipeline, dashboard, model, Ask space and app are all "
         "defined as code",
         "The whole environment is reproducible"],
    ]
    sl.add(table(sl.nid(), "Databricks alignment", M, CARD_Y,
                 [2900000, 4860480, 3700000], rows, row_h=440000,
                 header_h=420000))
    sl.note("Also used: least-privilege grants for the app's identity, and "
            "scikit-learn HistGradientBoosting with Poisson loss on the "
            "serverless runtime.", rule_y=5700000, y=5740000)
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
        ("Transfers, as recorded \u2014 ", "13 ranked moves waiting on a decision, 4 "
                              "urgent, about $54k of stock cover, each with its reason."),
        ("Forecast \u2014 ", "seven days of demand per product for one store, "
                             "and what the model got wrong before."),
        ("Ask \u2014 ", "an open question answered in plain language from the "
                        "same governed tables."),
        ("Since this recording \u2014 ", "the what-if simulator and the "
                                          "three-agent storm desk, both built "
                                          "and verified on the workspace."),
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
        ("18", "library tests"),
        ("70", "API and agent tests"),
        ("63", "web tests \u00b7 36 unit + 27 browser"),
        ("9 / 9", "live smoke checks on the workspace"),
    ]):
        tile(sl, x, 4240000, w, 900000, value, label)
    sl.note("14 of the 70 test the storm desk and its crew: a plan may only name "
            "moves its own tools returned. The smoke script also proves Ask answers "
            "10 of 10 sample questions and cannot change data.")
    return sl


def s_results(sl):
    sl.head("Results", "Measured, not asserted")
    big_bars(sl, M, CARD_Y, 5760000, 2900000,
             [("Champion model (v3)", 0.391, GOOD),
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
        ("9 / 9", "quality gates passed", "zero rows failed an expectation"),
        ("11 \u2192 9", "stores in shortage", "stale forecast vs live week"),
        ("652 \u2192 184", "units short", "the live week is calmer"),
    ]
    for i, (v, l, s) in enumerate(stats):
        tile(sl, sx + (i % 2) * (sw + 200000), CARD_Y + (i // 2) * (1350000 + 200000),
             sw, 1350000, v, l, source=s)
    sl.note("Champion v3 was retrained on regenerated history and still beats "
            "both naive baselines by a wide margin. Every figure is read from "
            "the workspace, not estimated; the app keeps its sample-data label.")
    return sl


def s_impact(sl):
    sl.head("Business impact", "Revenue protected, effort removed")
    grid = cols(2, gap=200000)
    bodies = [
        ("Revenue impact",
         ["Using live weather, the plan cut the units expected to run short "
          "across the network from 652 to 184, about 72%, with the same stock "
          "and the same sales data.",
          "The current plan has 11 ranked moves protecting about $26.6k of "
          "sales. By hand it would be 50 store \u00d7 product positions checked "
          "against a 7-day forecast.",
          "Sales protected is the forecast's estimate on sample sales data. It is "
          "gross revenue, not profit."]),
        ("Cost effectiveness",
         ["The cycle runs unattended at 6:00 AM on serverless compute that stops "
          "when the job ends \u2014 no cluster kept warm between runs.",
          "Every job is tagged by project and a cost view over Databricks "
          "system tables reports spend per run \u2014 built and tagged now, "
          "filled in as billing lands.",
          "Every asset is defined in code and created by one command, so there "
          "is no hand-built environment to maintain or drift."]),
    ]
    for (x, w), (headline, bl) in zip(grid, bodies):
        card(sl, x, CARD_Y, w, CARD_H, headline, bl)
    sl.note("Revenue and cost statements are limited to what the running system "
            "actually outputs. The cost view is built and tagged but billing "
            "lands hours late, so no dollar cost is claimed here yet.")
    return sl


# ------------------------------------------------------- speaker notes -------
NOTE = {
 "slide4": [
  "WHO: Adarsh Ajay, owner and builder of the whole stack.",
  "SAY: everything in this deck was run, not just written: the notebooks, the pipeline, the jobs, the tests and the smoke script.",
  "ROADMAP OF THE TALK: the problem, the idea, the architecture, a video, the test evidence, then the business case and what is open.",
  "IF ASKED WHO TO TRUST: the numbers in this deck come from the test runs and the live workspace, and each one has a source named on its slide.",
 ],
 "slide6": [
  "OPEN WITH: a planner's morning question. Which stores run short this week, and what moves where before the storm?",
  "THE SCALE: 10 stores and 5 products, so 50 store-product positions to decide each morning.",
  "THE TWO WEATHER DRIVERS: a storm pulls generators, plywood and tarps forward; a heat wave lifts coolers and pumps. They can hit two regions in one week, in opposite directions.",
  "THE CONSTRAINT: the window is a few days. Doing 50 positions by hand does not fit inside it.",
  "IF ASKED WHY NOT A DASHBOARD: a dashboard shows the gap. StormSense turns the gap into an approvable move.",
 ],
 "slide18": [
  "WALK THE CHAIN LEFT TO RIGHT: weather in, ranked decision out.",
  "WEATHER: observed history and the seven-day forecast. Live from the US National Weather Service in the daily job.",
  "FORECAST: one model for all stores and products, trained on features that only use information available at the time (sales are lagged seven days).",
  "GAPS: projected stock against the safety level, per store and product.",
  "TRANSFERS: the nearest spare stock, in whole packs, ranked by urgency and sales protected.",
  "PLANNER DECIDES: approve or reject on a phone. Only pending rows change.",
  "IF ASKED WHAT IS BEHIND EACH BOX: nine data-quality expectations, a champion model that must beat two simple baselines, and a learning step that ranks down routes planners keep rejecting.",
 ],
 "slide19": [
  "ANSWER THE QUESTION BEFORE IT IS ASKED: this is not another dashboard.",
  "WHAT IS NEW: the unit of decision. A gap per store and product over the weather horizon, resolved to a move a planner can approve.",
  "BE HONEST: the techniques are standard (gradient boosting, nearest-source matching). The framing, the constraints and the trust gates are the contribution.",
  "TRUST GATES: a model reaches champion only if it beats 'same as last week' and the trailing 28-day average on held-out data.",
  "SINCE THE LAST REVIEW: a what-if simulator rehearses a storm; a feedback loop lowers the rank of any route planners keep rejecting.",
  "IF ASKED WHAT LEARNING CAN BREAK: it never adds or removes a move. It only changes the order of options.",
 ],
 "slide8": [
  "THE RULE: three layers, one decision. The browser never talks to Databricks.",
  "DATABRICKS: 16 governed tables in Unity Catalog, the model registry, the jobs, the pipeline and the Ask space.",
  "FASTAPI: the only path to the data. Bound-parameter SQL, roles, and an audit row for every approval attempt, including refused ones.",
  "REACT: where the planner works. Today, Transfers, What if, Storm desk, Ask and History.",
  "THE DAILY CYCLE, 6:00 AM: weather, features, quality gate, forecast, gaps, learning, recommendations, verification. Every step can be re-run safely.",
  "IF ASKED WHAT HAPPENS ON FAILURE: each task retries twice, and a failed run emails the account that deployed it.",
 ],
 "slide20": [
  "THIS IS THE SLIDE FOR JUDGES WHO ASK ABOUT DATABRICKS ALIGNMENT. Go row by row.",
  "UNITY CATALOG: one governed home for tables, the model and the app's grants.",
  "LAKEFLOW PIPELINE: three clean views and nine quality expectations, run before the features each morning.",
  "SERVERLESS JOBS: 12 notebooks, with no cluster to size or pay for while idle.",
  "MLFLOW AND MODEL SERVING: versioned runs, the champion alias, and a scale-to-zero endpoint that scored 350 live rows.",
  "DASHBOARD AND GENIE: a generated dashboard, and a read-only Ask space the planner can question in plain words.",
  "SYSTEM TABLES: spend per job, filtered to the project tag on all three jobs.",
  "IF ASKED WHAT IS MISSING: Lakehouse Monitoring, real billing figures (the cost view is empty until billing lands), and the app deployment, which is blocked by the company network filter.",
 ],
 "slide23": [
  "THE PLANNER'S QUESTION: before a storm, what would it cost us, and how much stock would have to move?",
  "THE LIVE CHECK: a Florida storm of strength 80 over two days. 516 extra units. About $15,600 of sales at risk if no stock moves. 197 units to move to cover it.",
  "HOW TO READ IT: the simulator changes only the forecast inputs for the storm days. It writes nothing.",
  "THE CREW: three agents with separate jobs. A forecaster drafts, a risk checker tests each proposed move against the stock figures, and a summary writer writes the plan.",
  "THE RULE THAT MATTERS: a plan can name only moves its own tools returned. Any other sentence is dropped.",
  "THE LIVE RUN: 51 seconds, and every transfer it cited came from a tool result.",
  "IF ASKED WHETHER IT CAN ACT: it is read-only. It can suggest moves but cannot approve or change anything.",
 ],
 "slide24": [
  "THE LOOP IN ONE BREATH: a planner says why a move was wrong, and the next plan ranks that route lower.",
  "THE REASONS: no truck free, store closed, already covered, route too slow, or other. A reason is required.",
  "THE DECAY: a rejection's weight halves every 14 days, and it stops counting after 60 days. The penalty is capped at 4.0.",
  "THE LIVE EXAMPLE: a rejection on Jacksonville to Orlando pumps gave the route a penalty of 2.0. The next run sourced Orlando's pumps from Miami instead.",
  "THE CARBON ESTIMATE: about 0.9 kg CO2 per loaded truck-mile, and a truck carries about 200 units. The figure appears on every move.",
  "BE PLAIN ABOUT IT: the carbon figure is an estimate, not a measurement. It is shown to planners but does not yet choose the source. The nearest source still wins.",
  "IF ASKED WHAT LEARNING CAN BREAK: it only reorders options a planner can already see.",
 ],
 "slide25": [
  "THE POINT FOR A JUDGE: StormSense is not a closed app. Any MCP-capable assistant can read the plan, ask questions and run a what-if.",
  "THE MCP SERVER: ten tools. Eight read the plan, two approve or reject. Each one calls the same API as the app, so roles and rate limits apply.",
  "THE BUILT-IN CLIENT: a workspace model reads the tool list and decides which checks to run. It is read-only unless writes are enabled, and it needs no separate model key.",
  "THE WRITES ARE NARROW: approve and reject only, with the same role checks and audit trail as the app.",
  "THE DOCUMENTATION: a planner guide, setup pages and an API reference generated from the API's own description, so it always matches the code.",
  "THE DIAGRAMS: five interactive views, from the whole system to deployment.",
  "IF ASKED WHERE IT RUNS: the MCP server runs beside the API. It is not yet deployed; that waits on the same network decision as the app.",
 ],
 "slide26": [
  "QUALITY FIRST: nine expectations stop bad rows before any feature is built. An impossible temperature stops the run outright.",
  "LATEST RUN: zero rows failed an expectation.",
  "LIVE WEATHER: the US National Weather Service, grouped by each store's own time zone, so an evening storm in Florida lands on the right day.",
  "THE DAILY JOB ON THE LIVE FEED: ran end to end on serverless compute, and all seven tasks succeeded.",
  "THIS WEEK: the live forecast has no storm or heat alert. That is exactly why the what-if simulator exists.",
  "COST: a view over system billing, filtered to the project tag on all three jobs. It has no rows yet, because billing data lags by hours. Quote DBUs after a run, not dollars.",
  "DASHBOARD: six live datasets. Its layout has not yet been checked in a browser, so say so if asked.",
 ],
 "slide10": [
  "PLAY THE 63-SECOND VIDEO. It tells the whole story: the problem, the flow, then the application.",
  "WHILE IT PLAYS, WATCH FOR: Today, the Transfers list, the store forecast, and Ask.",
  "THE VIDEO PREDATES TWO THINGS: the what-if simulator and the three-agent storm desk. Both are built and checked, and they are shown on the decision-tools slide.",
  "IF THE VIDEO WON'T PLAY: the same screens can be shown live from the running app.",
 ],
 "slide12": [
  "TEST CASES ARE THE ARGUMENT. Each card is a claim someone could challenge, so each has a test behind it.",
  "THE MODEL MUST EARN ITS PLACE: promotion to champion is tested against two baselines on the last 28 days, held out of training.",
  "AN APPROVAL CANNOT DOUBLE-APPLY: only pending rows change, and a repeat is told it was already handled. Browser tests approve the same transfer twice.",
  "THE VOCABULARY IS ENFORCED: a test fails the build if a technical term appears in the planner interface.",
  "THE NUMBERS: 18 library tests, 70 API and agent tests, and 63 web tests (36 unit and 27 browser).",
  "THE LIVE CHECK: 9 of 9 smoke checks on the real workspace. Ask answered 10 of 10 sample questions and changed no data.",
  "THE CREW'S TESTS: 14 of the 70. A plan may name only moves its tools returned.",
  "OFFER A LIVE PROBE: try approving the same transfer twice in two browsers.",
 ],
 "slide21": [
  "READ THE CHART ONCE: champion v3 at 0.391 WAPE, against 0.571 for the trailing 28-day average and 0.667 for same-as-last-week. Lower is better.",
  "THE GREY BARS are the simple methods the business effectively uses today.",
  "WHAT WAPE MEANS: total absolute error divided by total actual units. It is the headline figure; MAPE is not used because it breaks at zero.",
  "THE LIVE WEATHER EFFECT: the time-travel comparison. Before the live weather, 11 stores ran short, 652 units in total. After it, 9 stores, 184 units.",
  "THE QUALITY GATES: all nine expectations passed on every row.",
  "BE PLAIN: sales and stock figures are still generated sample data. The app labels this on every screen.",
 ],
 "slide14": [
  "SPLIT THE SLIDE IN TWO: revenue on the left, cost on the right.",
  "THE ROI LINE: using live weather, the plan cut the units expected to run short from 652 to 184 across the network, about 72%, with the same stock and the same sales data.",
  "THE CURRENT PLAN: 11 ranked moves protecting about $26.6k of sales. That is gross revenue, not profit.",
  "WHERE 652 TO 184 COMES FROM: the time-travel check on the what-if page, which compares the plan saved before the live weather with the plan now (11 stores short, down to 9).",
  "REVENUE, IN WORDS: stock reaches the store the forecast says will sell it, inside the window the weather creates.",
  "COST: serverless compute that stops when the job ends, everything defined as code, and every job tagged so spend can be read per run.",
  "DO NOT INVENT AN ROI: the cost view exists, but billing lands hours late. The honest figures today are the run's DBU usage and the sales each move protects.",
  "IF ASKED FOR A PILOT NUMBER: none has been measured on a customer's data yet. That needs a pilot retailer's feed.",
 ],
 "slide22": [
  "THE ARCHITECTURE SURVIVES THE SAMPLE DATA LEAVING. Live National Weather Service data is already in the daily job.",
  "THE ONE BLOCKER: the hosted app is not deployed, because this network filters one upload. The code is written and the workspace is wired.",
  "WHAT CHANGES WITH REAL FEEDS: more stores, real sales and stock, and go-live alerting.",
  "NEXT ON THE MODEL: Lakehouse Monitoring on the forecasts, so accuracy is watched over time.",
 ],
 "slide27": [
  "CLOSE ON WHAT IS OPEN. Two things would move the project most: the app deployment and a pilot retailer's feed.",
  "BLOCKED: the company web filter stops the upload of one service file. Options are IT approval, a CI deploy with a service identity, or a Git folder in the workspace.",
  "DECISIONS NEEDED: pick a pilot segment, remove the stale October 7 forecast rows (with approval), and confirm one generator move approved without a note.",
  "NEXT FEATURES, IN ORDER OF SCORING VALUE: a storm trigger that drafts moves from warnings (business impact), and evaluation of the crew (alignment).",
  "ASK FOR THE DECISIONS, NOT FOR APPROVAL OF THE WHOLE ROADMAP.",
 ],
 "slide15": [
  "THANK THE PANEL. State the one-line pitch: weather in, a ranked decision out, every morning at 6:00 AM.",
  "THEN INVITE QUESTIONS. Keep the contact line on screen: Adarsh Ajay, 308638@ust.com.",
 ],
 "slide28": [
  "WHAT THIS IS: the running prototype, not a mock-up. These screens are captured from the app connected to the live Databricks workspace.",
  "THE MORNING VIEW: one headline, three numbers, one action. A planner starts here.",
  "THE NUMBER TO QUOTE: the urgent move protects about $2,300 in sales, read from the live plan.",
  "IF ASKED WHY IT SHOWS A SAMPLE LABEL: the sales and stock are generated sample data, so the app says so on every screen.",
 ],
 "slide29": [
  "EACH MOVE IS A SENTENCE: product, quantity, from and to. A planner can approve it without opening a spreadsheet.",
  "THE REASON IS PLAIN: why the move is needed, with the forecast's confidence.",
  "THE CARBON FIGURE IS AN ESTIMATE: about 0.9 kg CO2 per loaded truck-mile. It is labelled as an estimate on the card.",
  "DO NOT APPROVE LIVE on the screenshot. Approvals are recorded in the audit trail, and the demo should use a test transfer.",
 ],
 "slide30": [
  "THE PLANNER'S FIRST QUESTION: what would a storm cost us if we did nothing?",
  "THE SCREEN SHOWS THE COST FIRST: the cost card, then normal week against storm week, then the stock to move.",
  "THE SAMPLE RUN ON THIS SCREEN: strength 70 over a weekend, about $30,600 of sales at risk, and 349 units of stock to move.",
  "IF ASKED WHETHER IT CHANGES DATA: no. It is a simulation only.",
 ],
 "slide31": [
  "ASK: an open question answered in one sentence, read-only.",
  "HISTORY: every approval and rejection, who made it, and when. This is the accountability view.",
  "STORM DESK: the crew's plan starts from a goal in plain words. The plan can name only moves its tools returned. The screenshot shows the empty form, because a run calls the model.",
  "IF ASKED WHAT THE PROTOTYPE DOES NOT DO YET: the hosted app is not deployed, so these screens run locally against the workspace.",
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
    "slide23": "Test a storm before it arrives, and have a crew check the plan",
    "slide24": "Every rejection teaches the next plan, and every move shows its carbon",
    "slide25": "Open to any assistant, through one standard",
    "slide26": "Quality gates, real weather, and cost you can see",
    "slide27": "What is blocked, what needs a decision, and what comes next",
    "slide28": "The morning view: what needs attention",
    "slide29": "Decide each move in seconds",
    "slide30": "Test a storm before it arrives",
    "slide31": "Ask, review and plan in plain words",
}


def s_scale(sl):
    sl.head("Scale-up", "What changes when this leaves the sample data")
    g = cols(2, gap=200000)
    rows = [CARD_Y, CARD_Y + GRID_H + GRID_GAP]
    bodies = [
        ("Real feeds",
         ["The daily job already runs on the live National Weather Service "
          "forecast by default; only the sales and stock feeds are still "
          "sample. Swapping the generator for the retailer's feeds leaves the "
          "feature, model and planning code unchanged."]),
        ("More of the estate",
         ["Regions, stores and products are dimensions in Unity Catalog, so a "
          "larger estate is more data through the same job \u2014 not a "
          "rewrite."]),
        ("Deploy the app",
         ["The app bundle is written and the workspace is wired. Deployment is "
          "currently blocked by this network's upload filter on one file, not by "
          "the application."]),
        ("Watch it",
         ["The daily job already retries and emails the owner on failure. Next "
          "is Lakehouse Monitoring on forecast accuracy and drift, plus alerting "
          "on recommendation volume per run."]),
    ]
    for i, (headline, bl) in enumerate(bodies):
        x, w = g[i % 2]
        card(sl, x, rows[i // 2], w, GRID_H, headline, bl)
    sl.note("Honest status, for Q&A: the pipeline, model, API, dashboard, "
            "serving endpoint and app code are built against the real workspace, "
            "and the daily job runs end to end on live weather. The hosted "
            "Databricks App is not deployed \u2014 that needs a security decision, "
            "not more code. Lakehouse Monitoring is the named next step.")
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


def s_decision_tools(sl):
    sl.head("Decision tools", "Test a storm before it arrives, and have a crew check the plan")
    g = cols(2, gap=200000)
    card(sl, g[0][0], CARD_Y, g[0][1], 2450000, "What-if storm simulator", [
        ("Choose the storm: ", "how strong it is, when it hits, how long it lasts, and the region."),
        ("See the cost first: ", "extra units, sales lost if no stock moves, and the stock that would need to move."),
        ("Compare with the plan: ", "the storm week is set against the normal week and against the last saved plan."),
    ])
    card(sl, g[1][0], CARD_Y, g[1][1], 2450000, "Storm desk crew", [
        ("Three agents, three jobs: ", "a forecaster drafts the plan, a risk checker tests each move against stock, and a summary writer writes it up."),
        ("Only real moves: ", "a plan may name only transfers its own tools returned. Any other sentence is dropped."),
        ("Read-only: ", "it can suggest moves but never approves or changes anything."),
    ])
    tiles = cols(3)
    for (x, w), (value, label, source) in zip(tiles, [
        ("516", "extra units in a test storm", "Florida, strength 80, two days"),
        ("$15.6k", "sales at risk if no stock moves", "same test storm, live data"),
        ("197", "units of stock to move to cover it", "same test storm, live data"),
    ]):
        tile(sl, x, 4240000, w, 900000, value, label, source)
    sl.note("Simulator figures are estimates to plan with. The crew's plan in the "
            "live check took 51 seconds and cited only transfers its tools returned.")
    return sl


def s_learning_carbon(sl):
    sl.head("Learning and carbon", "Every rejection teaches the next plan, and every move shows its carbon")
    g = cols(2, gap=200000)
    card(sl, g[0][0], CARD_Y, g[0][1], 2450000, "Feedback loop", [
        ("A reason is required: ", "no truck free, store closed, already covered, route too slow, or other."),
        ("Recent decisions weigh more: ", "the weight halves every 14 days and stops counting after 60."),
        ("Learning ranks, never removes: ", "a rejected route is offered lower, with the reason shown. No move is added or dropped."),
    ])
    card(sl, g[1][0], CARD_Y, g[1][1], 2450000, "Carbon per move", [
        ("Shown on every move: ", "an estimate of kg CO₂ next to the distance."),
        ("How it is estimated: ", "a loaded truck emits about 0.9 kg CO₂ per mile, and a truck carries about 200 units."),
        ("Not yet used to choose: ", "the nearest source still wins. Carbon is shown, not optimised."),
    ])
    tiles = cols(3)
    for (x, w), (value, label, source) in zip(tiles, [
        ("14 days", "half-life of a rejection", "its weight halves each time"),
        ("2.0", "route penalty after one rejection", "live check, Jacksonville to Orlando"),
        ("Miami", "new source for Orlando's pumps", "the next plan, after the penalty"),
    ]):
        tile(sl, x, 4240000, w, 900000, value, label, source)
    sl.note("The loop only reorders options a planner can already see. The carbon "
            "figure is an estimate and is labelled as one everywhere it appears.")
    return sl


def s_connect(sl):
    sl.head("Integrations", "Open to any assistant, through one standard")
    g = cols(3, gap=200000)
    card(sl, g[0][0], CARD_Y, g[0][1], 2450000, "MCP server", [
        ("Ten tools: ", "eight read the plan and two approve or reject. Each calls the same API as the app."),
        ("Same rules: ", "roles, rate limits and the audit trail all apply. Writes need a planner account."),
        ("Standard protocol: ", "Streamable HTTP, so any MCP-capable client can connect."),
    ])
    card(sl, g[1][0], CARD_Y, g[1][1], 2450000, "Built-in client agent", [
        ("Chooses its own checks: ", "a workspace model reads the tool list and decides what to look at."),
        ("Read-only by default: ", "approve and reject stay hidden unless enabled."),
        ("No extra key: ", "it uses the workspace sign-in, and the model runs in the workspace."),
    ])
    card(sl, g[2][0], CARD_Y, g[2][1], 2450000, "Published documentation", [
        ("Documentation site: ", "planner guide, setup, design notes and a generated API reference."),
        ("Architecture diagrams: ", "five interactive views, from the whole system to deployment."),
        ("Rebuilt on each push: ", "the sites are published from the main branch on GitHub Pages."),
    ])
    tiles = cols(3)
    for (x, w), (value, label, source) in zip(tiles, [
        ("10", "MCP tools", "each one checked by tests"),
        ("6", "server tests", "run against a stand-in API"),
        ("3", "public pages", "landing, documentation, diagrams"),
    ]):
        tile(sl, x, 4240000, w, 900000, value, label, source)
    sl.note("Any system that speaks MCP can use StormSense without a new integration, "
            "under the same permissions as the app.")
    return sl


def s_operations(sl):
    sl.head("Operations", "Quality gates, real weather, and cost you can see")
    g = cols(3, gap=200000)
    card(sl, g[0][0], CARD_Y, g[0][1], 3300000, "Data quality gates", [
        ("Nine expectations: ", "bad sales, stock, rain or wind rows are dropped, and an impossible temperature stops the run."),
        ("Latest run: ", "zero rows failed an expectation."),
        ("Where it runs: ", "a declarative pipeline, before the features are built each morning."),
    ])
    card(sl, g[1][0], CARD_Y, g[1][1], 3300000, "Live weather in the daily job", [
        ("Live forecast: ", "the US National Weather Service, grouped by each store's own time zone."),
        ("Verified: ", "the daily job ran end to end on serverless compute, and all seven tasks succeeded."),
        ("This week: ", "no storm or heat alert appears in the live forecast, so storms are tested with the what-if."),
    ])
    card(sl, g[2][0], CARD_Y, g[2][1], 3300000, "Cost and dashboard", [
        ("Cost view: ", "built on system billing, filtered to the project tag on all three jobs."),
        ("Still empty: ", "billing data lags by hours, so the cost view has no rows yet."),
        ("Dashboard: ", "six live datasets. Its layout has not yet been checked in a browser."),
    ])
    sl.note("Each claim here is one the running system produced. Where something is "
            "still waiting for data, the slide says so.")
    return sl


def s_roadmap(sl):
    sl.head("Roadmap", "What is blocked, what needs a decision, and what comes next")
    g = cols(3, gap=200000)
    card(sl, g[0][0], CARD_Y, g[0][1], 3300000, "Blocked", [
        ("Planner app deployment: ", "the company web filter blocks the upload of one service file."),
        ("Options: ", "IT approval, a CI deploy with a service identity, or a Git folder in the workspace."),
        ("Until then: ", "the app runs locally against the live workspace."),
    ])
    card(sl, g[1][0], CARD_Y, g[1][1], 3300000, "Decisions needed", [
        ("Pilot retailer: ", "choose a regional grocer or hardware chain for a live sales feed."),
        ("Data clean-up: ", "remove the stale October 7 forecast rows, with approval."),
        ("One approval to confirm: ", "a Tampa generator move was approved with no note."),
    ])
    card(sl, g[2][0], CARD_Y, g[2][1], 3300000, "Next features", [
        ("Storm trigger: ", "draft moves from weather warnings automatically; planners still approve."),
        ("Joint optimisation: ", "solve all moves together for cost, sales and carbon."),
        ("Evaluation and precedents: ", "score the crew against approved answers, and find similar past decisions."),
    ])
    sl.note("Be direct about what is blocked. Every other item has a working version "
            "that was checked on the workspace.")
    return sl


SHOTS = os.path.join(HERE, "assets", "shots")
SHOT_W, SHOT_H = 6400000, 4000000          # 16:10 screenshots, left column
SIDE_X = M + SHOT_W + 228600
SIDE_W = CW - SHOT_W - 228600


def _shot_slide(sl, eyebrow, title, image, descr, heading, bullets):
    sl.head(eyebrow, title)
    sl.image(os.path.join(SHOTS, image), M, CARD_Y, SHOT_W, SHOT_H, descr)
    card(sl, SIDE_X, CARD_Y, SIDE_W, SHOT_H, heading, bullets)
    return sl


def s_proto_today(sl):
    return _shot_slide(
        sl, "Prototype walkthrough · 1 of 4", "The morning view: what needs attention",
        "today.png", "StormSense Today screen: urgent transfers, stores running low, and the weather alert",
        "Today", [
            ("One headline: ", "the most urgent move, and the sales it protects."),
            ("Three numbers: ", "urgent moves, stores running low, and the next weather alert."),
            ("One action: ", "Review transfers opens the day's decisions."),
            ("Stamp of freshness: ", "the screen says which day's stock it reads."),
        ])


def s_proto_transfers(sl):
    return _shot_slide(
        sl, "Prototype walkthrough · 2 of 4", "Decide each move in seconds",
        "transfers.png", "StormSense Transfers screen: urgent and weekly moves, each with its reason",
        "Transfers", [
            ("Each move reads as a sentence: ", "the product, the quantity and the two stores."),
            ("The reason: ", "why it is needed, and how sure the forecast is."),
            ("Sales protected: ", "what would be lost without the move."),
            ("Carbon: ", "an estimate of kg CO₂ next to the distance."),
        ])


def s_proto_whatif(sl):
    return _shot_slide(
        sl, "Prototype walkthrough · 3 of 4", "Test a storm before it arrives",
        "what-if.png", "StormSense what-if screen: the cost of a storm if no stock moves, and the stock to move",
        "What if a storm comes?", [
            ("Set the storm: ", "its strength, when it hits, how long it lasts, and the region."),
            ("Cost first: ", "the sales lost if nothing moves, in dollars."),
            ("Compare: ", "the normal week against the storm week."),
            ("Action: ", "the stock that would need to move to cover it."),
        ])


def s_proto_more(sl):
    sl.head("Prototype walkthrough · 4 of 4", "Ask, review and plan in plain words")
    g = cols(3, gap=200000)
    w = g[0][1]
    h = int(w / 1.6)
    items = [
        ("ask.png", "Ask", "Ask a question in plain words and get one sentence back. It only reads."),
        ("history.png", "History", "Every approval and rejection, with the person, the time and any note."),
        ("storm-desk.png", "Storm desk", "Describe a goal. The crew checks the data and writes a plan that names only real moves."),
    ]
    for (x, cw), (image, heading, text) in zip(g, items):
        sl.image(os.path.join(SHOTS, image), x, CARD_Y, cw, h, heading + " screen")
        card(sl, x, CARD_Y + h + 150000, cw, 5150000 - (CARD_Y + h + 150000), heading, [text])
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
    ("write", "slide23", s_decision_tools, "slideLayout39", NOTE["slide23"]),
    ("write", "slide24", s_learning_carbon, "slideLayout39", NOTE["slide24"]),
    ("write", "slide25", s_connect,      "slideLayout39", NOTE["slide25"]),
    ("write", "slide26", s_operations,   "slideLayout39", NOTE["slide26"]),
    ("keep",  "slide9",  None,           None,            None),
    ("write", "slide10", s_video,        "slideLayout39", NOTE["slide10"]),
    ("write", "slide28", s_proto_today,     "slideLayout39", NOTE["slide28"]),
    ("write", "slide29", s_proto_transfers, "slideLayout39", NOTE["slide29"]),
    ("write", "slide30", s_proto_whatif,    "slideLayout39", NOTE["slide30"]),
    ("write", "slide31", s_proto_more,      "slideLayout39", NOTE["slide31"]),
    ("keep",  "slide11", None,           None,            None),
    ("write", "slide12", s_tests,        "slideLayout39", NOTE["slide12"]),
    ("write", "slide21", s_results,      "slideLayout39", NOTE["slide21"]),
    ("keep",  "slide13", None,           None,            None),
    ("write", "slide14", s_impact,       "slideLayout39", NOTE["slide14"]),
    ("write", "slide22", s_scale,        "slideLayout39", NOTE["slide22"]),
    ("write", "slide27", s_roadmap,     "slideLayout39", NOTE["slide27"]),
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

        for rid, path in sl.images:
            fname = "shot-" + os.path.basename(path)
            parts[f"ppt/media/{fname}"] = open(path, "rb").read()
            entries.append((rid, "image", f"../media/{fname}"))

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
