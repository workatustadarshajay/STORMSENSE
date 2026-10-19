"""StormSense end-to-end deck, built on the Databricks hackathon template.

Rebuild with: python deck/build_end_to_end.py  (writes stormsense_end_to_end.pptx in the project root)

Sections: problem, solution, return on investment, technical architecture, demo and proof, roadmap and the ask.
Every app figure is sample data and is labelled as such on the slide where it appears.
"""
from __future__ import annotations

import copy

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Pt

TEMPLATE = "/home/308638@USTDEV.COM/Projects/STORMSENSE/Databricks Hackathon_Idea #_Idea Title_Presenter Name.pptx"
OUT = "/home/308638@USTDEV.COM/Projects/STORMSENSE/stormsense_end_to_end.pptx"
S = str(Path(__file__).resolve().parent / "assets" / "end-to-end")
SHOTS = "/home/308638@USTDEV.COM/Projects/STORMSENSE/docs/screenshots"

INK = RGBColor(0x10, 0x1B, 0x2B)
TEAL = RGBColor(0x14, 0x6F, 0x6B)
GLOW = RGBColor(0x73, 0xD6, 0xCD)
SIGNAL = RGBColor(0xB3, 0x32, 0x1F)
MUTED = RGBColor(0x53, 0x63, 0x6F)
LINE = RGBColor(0xD5, 0xDE, 0xDC)

# ---- sample figures (from the app's sample API and the backtest) ----
EVENTS = [
    ("Hurricane Marlow", "14-18 Sep", 4, 171310, 2658),
    ("Severe Storm Delta", "17-19 Apr", 3, 46887, 335),
    ("Atmospheric River Kestrel", "9-12 Jan", 3, 42409, 0),
    ("Tropical Storm Ines", "24-26 Aug", 3, 34351, 7095),
    ("Heat Dome Ridge", "6-10 Jul", 3, 7197, 2049),
]
LOST = sum(e[3] for e in EVENTS)
PROT = sum(e[4] for e in EVENTS)
assert LOST == 302154 and PROT == 12137
IMPACT = dict(protected=50180, margin=15054, trucking=6460, net=8594, co2=584)

prs = Presentation(TEMPLATE)
T = list(prs.slides)
L = {layout.name: layout for layout in prs.slide_layouts}
W = prs.slide_width

order: list = []


# ---- helpers -------------------------------------------------------------------------------------
def ph(slide, idx):
    return slide.placeholders[idx]


def set_runs(tf, items, size=None, color=None, align=None, space_after=6):
    """items: str | (text, level) | (text, level, bold). Clears the frame first."""
    tf.clear()
    tf.word_wrap = True
    for i, item in enumerate(items):
        text, level, bold = (item, 0, None) if isinstance(item, str) else (tuple(item) + (None,))[:3]
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        p.space_after = Pt(space_after)
        if align is not None:
            p.alignment = align
        r = p.add_run()
        r.text = text
        if bold is not None:
            r.font.bold = bold
        if size:
            r.font.size = Pt(size - 2 * level)
        if color is not None:
            r.font.color.rgb = color


def fill(slide, idx, items, size=None, **kw):
    set_runs(ph(slide, idx).text_frame, items, size=size, **kw)


def title(slide, text, size=None):
    t = slide.shapes.title
    t.text = text
    if size:
        for p in t.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(size)


def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def new(layout_name, title_text=None, notes_text=""):
    s = prs.slides.add_slide(L[layout_name])
    if title_text is not None and s.shapes.title is not None:
        title(s, title_text)
    if notes_text:
        note(s, notes_text)
    if layout_name == "Photo and Statement":
        # The layout's text area is shallow; give the bullets the full content height so nothing overflows.
        ph(s, 14).height = Emu(4251960)
    order.append(s)
    return s


def textbox(slide, left, top, width, height, items, size=14, color=None, align=None, bold=None):
    tb = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    set_runs(tb.text_frame, [(t, 0, bold) if isinstance(t, str) else t for t in items], size=size, color=color, align=align, space_after=4)
    return tb


def footnote(slide, text):
    return textbox(slide, 365760, 6217920, 11457432, 420000, [text], size=11, color=MUTED)


def table(slide, rows, left, top, col_w, row_h=420000, size=12, header_fill=INK):
    width = sum(col_w)
    gf = slide.shapes.add_table(len(rows), len(rows[0]), Emu(left), Emu(top), Emu(width), Emu(row_h * len(rows)))
    tbl = gf.table
    for j, w in enumerate(col_w):
        tbl.columns[j].width = Emu(w)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Emu(row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = str(val)
            cell.margin_left = cell.margin_right = Emu(90000)
            cell.margin_top = cell.margin_bottom = Emu(45000)
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(size)
                    r.font.bold = True if i == 0 else None
            if i == 0 and header_fill is not None:
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_fill
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    return tbl


def picture_fit(slide, path, left, top, max_w, max_h):
    from PIL import Image

    w, h = Image.open(path).size
    scale = min(max_w / w, max_h / h)
    pw, pw_h = int(w * scale), int(h * scale)
    return slide.shapes.add_picture(path, Emu(left + (max_w - pw) // 2), Emu(top + (max_h - pw_h) // 2), Emu(pw), Emu(pw_h))


def tile(slide, left, top, width, height, big, small, big_size=28, color=TEAL):
    from pptx.enum.shapes import MSO_SHAPE

    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(left), Emu(top), Emu(width), Emu(height))
    rect.adjustments[0] = 0.08
    rect.fill.background()
    rect.line.color.rgb = LINE
    rect.line.width = Pt(1.25)
    tf = rect.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(140000)
    tf.margin_top = Emu(120000)
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = big
    r.font.bold = True
    r.font.size = Pt(big_size)
    r.font.color.rgb = color
    p2 = tf.add_paragraph()
    p2.space_before = Pt(6)
    r2 = p2.add_run()
    r2.text = small
    r2.font.size = Pt(13)
    r2.font.color.rgb = MUTED
    return rect


def money(x):
    return f"${x:,.0f}"


def style_chart(chart, legend=True, number_format='$#,##0', label_size=11):
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(12)
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.number_format = number_format
    plot.data_labels.number_format_is_linked = False
    plot.data_labels.font.size = Pt(label_size)
    chart.value_axis.tick_labels.number_format = number_format
    chart.value_axis.tick_labels.number_format_is_linked = False
    chart.value_axis.tick_labels.font.size = Pt(11)
    chart.value_axis.has_major_gridlines = True
    chart.value_axis.major_gridlines.format.line.color.rgb = LINE
    chart.category_axis.tick_labels.font.size = Pt(12)


def color_series(chart, colors):
    for series, rgb in zip(chart.series, colors):
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = rgb


def section(slide, number, heading, body=None):
    ph(slide, 14).text_frame.text = number
    title(slide, heading)
    if body:
        if any(p.placeholder_format.idx == 13 for p in slide.placeholders):
            fill(slide, 13, [body])
        else:
            textbox(slide, 1828800, 4114800, 9994392, 1200000, [body], size=20, color=MUTED)


# ---- 1. Title ------------------------------------------------------------------------------------
s = T[0]
ph(s, 0).text_frame.text = "StormSense"
ph(s, 1).text_frame.text = "Move stock before the storm, not after."
ph(s, 11).text_frame.text = "Adarsh Ajay  |  UST  |  Databricks Hackathon, October 2026"
note(s, "Open with the one line: StormSense moves stock before the storm, not after. Then the order: the problem, the solution, "
        "the return, how it is built, the demo, and what we ask for.")
order.append(s)

# ---- 2. Agenda -----------------------------------------------------------------------------------
s = T[1]
for idx, text in [(14, "The problem"), (16, "The solution"), (18, "Return on investment"),
                  (20, "Technical architecture"), (22, "Demo and proof"), (24, "Roadmap and the ask")]:
    ph(s, idx).text_frame.text = text
note(s, "Six parts. The four that matter most are the problem, the solution, the return and the architecture.")
order.append(s)

# ================================================================================================
# 01 THE PROBLEM
# ================================================================================================
s = T[2]
section(s, "01", "The problem", "Weather moves demand in days. Stock moves in weeks. Planners find out too late.")
note(s, "Set the scene: a storm is coming, and the right stock is in the wrong store.")
order.append(s)

s = new("Big Statement", notes_text="Make it concrete. One store, one Thursday, one product. The gap is time, not weather.")
fill(s, 1, [
    ("It is Thursday. A tropical storm reaches Florida on Sunday.", 0, True),
    ("Orlando will sell about 56 generators this week and has 19. Jacksonville has spare stock 125 miles away.", 0),
    ("Nobody knows in time. By Saturday the shelf is empty and the customer has driven to a competitor.", 0),
], size=28, space_after=18)
footnote(s, "Sample data. Figures are from the sample plan the app shows.")

s = new("Two Content", "Weather moves demand faster than inventory moves",
        "Both problems happen on the same morning: some stores run short while others hold too much. The cheapest fix is to move what is already in the network.")
fill(s, 1, [
    ("What happens before a storm", 0, True),
    ("Generators, tarps, pumps and plywood sell out in the stores in the storm's path, within days", 1),
    ("Heat does the same for coolers and pumps, in a different region, the same week", 1),
    ("Stores one region away hold more than they can sell", 1),
    ("Planners read spreadsheets after the warning, phone neighbours and decide on instinct", 1),
    ("Nothing is recorded, so nobody learns for next season", 1),
], size=16)
fill(s, 2, [
    ("One morning, in numbers (sample data)", 0, True),
    ("10 stores across Florida, Texas and California; 5 weather-sensitive products", 1),
    ("50 store-product positions: 11 short, 16 surplus, 23 balanced, all on the same day", 1),
    ("7 urgent moves waiting; 5 stores running low; a heat alert for Thursday", 1),
    ("12 months of daily history, with named storm and heat events", 1),
], size=16)

s = new("Title Only", "What a storm costs when stock is in the wrong place",
        "Each pair of bars is one past event. The first is sales lost if nothing moved; the second is what planned moves could have protected. "
        "The protected bar is an upper bound, because the backtest uses what really sold. The gap is the money on the table.")
cd = CategoryChartData()
cd.categories = [e[0] for e in EVENTS]
cd.add_series("Sales lost if nothing moved", [e[3] for e in EVENTS])
cd.add_series("Protected by planned moves (upper bound)", [e[4] for e in EVENTS])
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Emu(365760), Emu(1450000), Emu(11457432), Emu(4500000), cd).chart
style_chart(ch)
color_series(ch, [SIGNAL, TEAL])
footnote(s, f"Sample history, five events: {money(LOST)} lost, {money(PROT)} protected ({PROT / LOST:.0%}). Lost sales = units sold beyond "
            "the stock on hand at the start of the event, at list price. An upper bound, from a backtest on what really sold.")

s = new("Title Only", "The industry loses this everywhere",
        "Outside figures, for scale only. They differ in year, scope and method, so they are not comparable with each other or with our sample. "
        "Check each one before quoting it.")
table(s, [
    ["Figure", "Scope", "Source"],
    ["$93 billion a year lost to out-of-stocks", "US retailers, 2008 survey of 124 retailers (85,000+ stores)", "RIS News / IHL Group"],
    ["France: €851 million missed sales at a 4.4% out-of-stock rate; UK: about £1 billion at 4.0%", "Grocery, 2022", "NielsenIQ, via ESM Magazine"],
    ["About $300 billion in markdowns, about 12% of non-grocery sales", "US non-grocery retail, 2018, modelled", "Coresight Research and Celect"],
    ["3.7% to 4% of sales lost to out-of-stocks", "661 outlets, 29 countries, 2002", "Gruen, Corsten and Bharadwaj"],
], left=365760, top=1500000, col_w=[4400000, 4000000, 3057432], row_h=640000, size=13)
footnote(s, "Weather-driven losses are not measured at national level in any source found. StormSense addresses the share of these losses "
            "caused by stock sitting in the wrong store before a storm or heat wave.")

s = new("Title Only", "Today's process, and what changes",
        "The left column is a typical manual process, not a measurement of any one retailer. The right column is what the app does today on sample data.")
table(s, [
    ["Step", "Typical manual process", "With StormSense"],
    ["Spot shortages", "Spreadsheets per store, after the warning", "Seven-day forecast per store and product, every morning at 6:00 AM"],
    ["Find stock to move", "Phone calls between stores", "Nearest store with spare stock, inside the distance limit, pack sizes respected"],
    ["Decide", "Instinct and email approvals", "Each move shows its reason, the sales it protects and the forecast confidence"],
    ["Record", "Notes scattered across people", "Audit trail: who, what and when. Repeat approvals are refused"],
    ["Learn", "Nothing carries to next season", "Rejection reasons re-rank routes; past storms are replayed in a recovery view"],
    ["Timing", "Hours before the storm, if at all", "Moves are ready from the morning run; a warning can trigger an extra run"],
], left=365760, top=1450000, col_w=[2100000, 4000000, 5357432], row_h=620000, size=13)

# ================================================================================================
# 02 THE SOLUTION
# ================================================================================================
s = T[4]
section(s, "02", "The solution", "Predict demand per store. Propose the moves. A planner decides. Every decision is recorded.")
note(s, "The system does the arithmetic. The planner stays in control.")
order.append(s)

s = new("Three Content", "The idea in three steps", "Pause after each step word. The audience should be able to repeat all three.")
fill(s, 1, [("1. Predict", 0, True), ("Forecast seven days of demand for every store and product, from the weather coming and the sales history.", 0),
            ("Features use only what was known on the day, so the model never sees the future.", 0)], size=17, space_after=12)
fill(s, 2, [("2. Move", 0, True), ("Find the stores that will run short and the nearby stores with spare stock. Propose the transfer before the storm.", 0),
            ("Nearest source first, inside a distance limit, in pack sizes a truck can carry.", 0)], size=17, space_after=12)
fill(s, 13, [("3. Decide", 0, True), ("A planner sees the reason, the sales protected and the confidence, and approves or rejects each move.", 0),
             ("Every decision and every repeat attempt is recorded.", 0)], size=17, space_after=12)

s = new("Photo and Statement", "The morning view", "Point at the three numbers and the one button. This is the planner's to-do list for today.")
ph(s, 16).insert_picture(f"{S}/app-today.png")
fill(s, 14, [
    ("Today answers one question", 0, True),
    ("Which stores run short this week, and what should move first", 1),
    ("Urgent moves, stores running low, the next weather alert", 1),
    ("A morning briefing written from the figures, so nothing is made up", 1),
    ("What changed since the planner's last visit", 1),
    ("One button: Review transfers", 1),
], size=15)
footnote(s, "Sample data. The label stays on screen until real feeds are connected.")

s = new("Photo and Statement", "Every move is a sentence a planner can act on", "Read one reason aloud: the storm, what the store will sell, what it has.")
ph(s, 16).insert_picture(f"{S}/app-transfers.png")
fill(s, 14, [
    ("Transfers", 0, True),
    ("Move 54 1000W generators from Jacksonville to Orlando: the storm, the forecast and the stock on hand, in one line", 1),
    ("Sales protected, distance, confidence and estimated CO₂ on every card", 1),
    ("Select, approve or reject in one step; a repeat approval returns already handled", 1),
    ("Still short after these moves: a safety order if demand runs high", 1),
    ("Lowest CO₂ first, shared truck loads, CSV and print", 1),
], size=15)

s = new("Four Content", "Everything the app does today", "Four groups. Plan, decide, ask and simulate, learn. Name one item in each group and move on.")
fill(s, 1, [("Plan", 0, True), "Today: the morning view and briefing", "Transfers: every move with its reason", "Stores: weather strip and forecast per product",
            "Best sellers by weather", "History: who decided what, when"], size=14)
fill(s, 2, [("Decide", 0, True), "Approve or reject, with audit", "Storm response: the whole plan, one decision", "Price markdowns on slow surplus",
            "Shared truck loads", "Safety orders when demand runs high"], size=14)
fill(s, 13, [("Ask and simulate", 0, True), "Ask: one sentence and a table, read-only", "What if a storm comes: scored by the same forecaster",
             "Storm desk: three read-only agents draft a plan", "Storm cover: a parametric trigger, simulated"], size=14)
fill(s, 14, [("Learn and connect", 0, True), "Rejection reasons re-rank routes", "Past storm recovery view", "Upload your own feeds (CSV, Excel, JSON)",
             "MCP server for AI assistants", "Business impact: protected, margin, trucking, net"], size=14)

s = new("Title and Content", "Honest by design", "These are the rules that make the numbers trustworthy. Say them before anyone asks.")
fill(s, 1, [
    "The system proposes. A planner approves or rejects every move. Nothing moves on its own.",
    "Sample data is labelled on every screen until real feeds replace the sample tables.",
    "Protected sales are an upper bound, and the slide says so wherever they appear.",
    "The forecaster is promoted only if it beats two simple baselines on the latest four weeks.",
    "Ask and the storm desk can only read. Nothing they return is executed.",
    "Every approval, rejection and repeat attempt is written to an audit table.",
], size=17)

# ================================================================================================
# 03 RETURN ON INVESTMENT
# ================================================================================================
s = T[6]
section(s, "03", "Return on investment", "Where the money is, what the current plan is worth, and how to earn more.")
note(s, "Lead with net, not revenue. Name the assumptions.")
order.append(s)

s = new("Title Only", "What the current plan is worth", "Net is the number to quote. Margin and trucking are assumptions, and a store can set its own margin.")
cd = CategoryChartData()
cd.categories = ["Protected sales", "Margin at 30%", "Trucking", "Net"]
cd.add_series("Sample plan", [IMPACT["protected"], IMPACT["margin"], -IMPACT["trucking"], IMPACT["net"]])
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Emu(365760), Emu(1450000), Emu(6900000), Emu(4500000), cd).chart
style_chart(ch, legend=False)
color_series(ch, [TEAL])
pts = ch.plots[0].series[0].points
for i, rgb in enumerate([TEAL, TEAL, SIGNAL, INK]):
    pts[i].format.fill.solid()
    pts[i].format.fill.fore_color.rgb = rgb
x0, w, gap = 7500000, 2080000, 160000
tile(s, x0, 1450000, w, 1350000, money(IMPACT["protected"]), "protected sales, gross revenue")
tile(s, x0 + w + gap, 1450000, w, 1350000, money(IMPACT["net"]), "net: margin less trucking", color=INK)
tile(s, x0, 2960000, w, 1350000, "16 moves", "14 pending, 2 approved, 1 rejected")
tile(s, x0 + w + gap, 2960000, w, 1350000, f"{IMPACT['co2']} kg", "estimated CO₂ for the moves")
tile(s, x0, 4470000, 2 * w + gap, 1350000, "$2,000 more", "by sharing trucks on 7 routes: 14 trips become 9, 720 kg CO₂ saved")
footnote(s, "Sample data. Margin 30% unless a store sets its own. Trucking $2.50 a mile, one trip a move. CO₂ about 0.9 kg per loaded truck-mile. "
            "Protected sales use the forecast, not what really sold.")

s = new("Title Only", "Where the gap is: five past events", "Read the total row first. About $302,000 lost, about 4% protected. Heat events protect the most, "
                                                          "about 28%, so that is where to start.")
rows = [["Event", "Dates (2026)", "Stores", "Sales lost if nothing moved", "Protected by moves", "Share protected"]]
for name, dates, stores, lost, prot in EVENTS:
    rows.append([name, dates, stores, money(lost), money(prot), f"{prot / lost:.1%}"])
rows.append(["Total", "", "", money(LOST), money(PROT), f"{PROT / LOST:.1%}"])
table(s, rows, left=365760, top=1450000, col_w=[3100000, 1500000, 900000, 2500000, 1900000, 1557432], row_h=520000, size=13)
footnote(s, "Sample data. The backtest moves stock from the nearest store with spare stock inside the distance limit. It ignores pack sizes and truck limits, "
            "so it slightly overstates protection. An upper bound.")

s = new("Title Only", "Six levers to earn more", "Options one and two can start this quarter with what we already have. Three needs a pilot. "
                                                "Four needs more modelling. Six waits for real feeds.")
table(s, [
    ["Lever", "Evidence today (sample data)", "Effort", "Status"],
    ["1. Share trucks on a route", "$2,000 across 7 routes; 14 trips become 9; 720 kg CO₂", "Low", "Built: Shared truck loads"],
    ["2. Mark down slow surplus", "Los Angeles: 30 generators at 10% off clear in 14 days, about $260 more than holding", "Low", "Built: Price markdowns"],
    ["3. Move on the warning", "Storm trigger reads NWS warnings every 15 minutes", "Low to switch on", "Built, paused"],
    ["4. Protect more lost sales", "Backtest protects 4%, an upper bound", "Medium", "Pack and truck limits, wider sourcing"],
    ["5. Learn from decisions", "Rejection reasons re-rank routes in the next run", "Low", "Built; effect not yet measured"],
    ["6. More stores and products", "10 stores and 5 products in the sample", "Depends on feeds", "Planned"],
], left=365760, top=1450000, col_w=[2700000, 4700000, 1500000, 2557432], row_h=560000, size=12)

s = new("Title Only", "What it could mean per $1 billion of annual sales", "This is a model with stated assumptions, not a measurement. "
                                                                           "The protection rate is the number a pilot would test.")
table(s, [
    ["Protection rate", "Sales recovered", "Gross profit saved", "Basis"],
    ["4%", "about $96,000", "about $29,000", "Our backtest across all storms (upper bound)"],
    ["10%", "about $240,000", "about $72,000", "Assumed middle case"],
    ["28%", "about $672,000", "about $202,000", "Our heat-event case (upper bound)"],
], left=365760, top=1450000, col_w=[1800000, 2300000, 2400000, 4957432], row_h=560000, size=14)
textbox(s, 365760, 3900000, 11457432, 1900000, [
    ("How the model works", 0, True),
    ("Gross profit saved = sales × lost-sales rate × weather-sensitive share × share recoverable by moving stock × protection rate × margin", 0),
    ("Assumptions to replace with a retailer's own figures: lost-sales rate 4% (a proxy from out-of-stock rates), weather-sensitive share 20%, "
     "share recoverable by moving stock 30%, margin 30%.", 0),
], size=14, color=MUTED)
footnote(s, "The app's own running cost on Databricks has not been measured yet and is not in these figures.")

s = new("Photo and Statement", "A new product idea: storm cover, simulated", "This is a concept for the pitch. The trigger and the cap are illustrative, and a real product needs an insurer.")
ph(s, 16).insert_picture(f"{S}/app-cover.png")
fill(s, 14, [
    ("Parametric cover on the same forecast", 0, True),
    ("Triggers when at least two stores in a region reach 39 mph wind or 3 inches of rain on the same day", 1),
    ("Payout: the region's projected lost sales, capped at $100,000", 1),
    ("On today's sample forecast: Florida would trigger, about $42,600; Texas and California would not", 1),
    ("A simulation, not a quote and not a contract. Terms would be agreed with an insurer", 1),
    ("Evidence tables and Delta Sharing with the insurer are the next step", 1),
], size=14)

s = new("Title and Content", "How we would prove it: a pilot", "A pilot turns a model into a measurement. Say the control group out loud.")
fill(s, 1, [
    "Pick two or three stores and one product family in one region, for example generators in Florida.",
    "Keep comparable stores as a control, with no change to how they plan.",
    "Run the planner workflow for two storm seasons, or replay the storms in the backtest where possible.",
    "Measure protected sales, stock-outs, approval rate and the time from warning to decision.",
    "Widen only if the pilot beats the control on both sales and stock-outs.",
    "Price the rollout on the measured result, not on the model.",
], size=17)

# ================================================================================================
# 04 TECHNICAL ARCHITECTURE
# ================================================================================================
s = T[8]
section(s, "04", "Technical architecture", "One app process, a lakehouse behind it, and the browser never sees a table, a query or a credential.")
note(s, "Judges score Databricks usage here. Name the services as you point at the boxes.")
order.append(s)

s = new("Title Only", "High-level architecture: the whole application on one page",
        "Planners reach the web app and the API through one process. The API is the only part that talks to the workspace. The daily job, the forecaster, "
        "the Ask space and the storm trigger live in the workspace. The ingestion client and the MCP server are the two other doors in.")
picture_fit(s, f"{S}/high-level-crop.png", 365760, 1350000, 11457432, 4650000)
footnote(s, "Interactive version: workatustadarshajay.github.io/STORMSENSE/architecture/")

s = new("Three Content", "The application", "Three parts, one codebase. The web app never calls Databricks. The API runs as the app's own service principal.")
fill(s, 1, [("Web app", 0, True), "React 18 and TypeScript, Vite, Tailwind CSS 4", "Landing page and planner screens; routes load on demand",
            "Phone-first: Today, Transfers, Stores, Ask, History", "Types generated from the API's OpenAPI contract", "68 unit tests, Playwright browser tests"], size=14)
fill(s, 2, [("API", 0, True), "FastAPI, one process serves the web app and the API", "Sign-in from the workspace; roles viewer, planner, admin",
            "Fixed, parameterised SQL through a serverless warehouse", "Guarded approvals that touch only pending rows; audit on every attempt",
            "Sample-data mode runs the whole app with no workspace", "182 backend and data tests"], size=14)
fill(s, 13, [("Integrations", 0, True), "Ingestion client: upload stores, products, sales and stock as CSV, Excel or JSON rows",
             "MCP server: the plan, Ask, what-if and approvals as tools for any AI assistant, under the same rules",
             "Databricks App definition and two Asset Bundles deploy everything from code", "Documentation and architecture sites built in CI"], size=14)

s = new("Title Only", "Daily data flow: from feeds to transfers", "Five stages: feeds, prepare, forecast, decide, serve. The forecaster is trained and checked, "
                                                                 "then scores seven days per pair. Shortage and surplus become transfers, pending until a planner decides.")
picture_fit(s, f"{S}/arch-daily-pipeline-crop.png", 365760, 1350000, 11457432, 4700000)
footnote(s, "Features are lagged by the seven-day horizon, so there are no look-ahead leaks. Validation is the last four weeks, never a random split.")

s = new("Title Only", "Databricks: data and pipelines", "Everything is governed in Unity Catalog and created from code with Asset Bundles. "
                                                       "Serverless compute means no clusters to manage.")
table(s, [
    ["Service", "What it does in StormSense", "Where"],
    ["Unity Catalog", "Governs the stormsense schema and the registered forecaster with its champion alias", "databricks/ bundle; 04_train_register"],
    ["Delta tables", "About 15 tables: stores, products, sales, stock, weather, features, predictions, gaps, transfers, audit, feedback, route preferences", "stormsense_core.tables"],
    ["Lakeflow pipeline", "Data-quality gates: constraint violations drop bad rows before features are built", "pipelines/data_quality.sql"],
    ["Jobs", "Daily 6:00 AM cycle; build job; storm trigger every 15 minutes (paused); demo alert job", "resources/jobs.yml"],
    ["Serverless compute", "Notebooks and the pipeline run serverless; no classic clusters", "Job and pipeline definitions"],
    ["Asset Bundles", "Two bundles deploy data, jobs, the forecaster, the Ask space and the app from code", "databricks.yml, backend/databricks.yml"],
], left=365760, top=1450000, col_w=[2000000, 6700000, 2757432], row_h=600000, size=12)

s = new("Title Only", "Databricks: AI, serving and the app", "The forecaster lives in MLflow and Unity Catalog and is served from an endpoint. Genie powers Ask. "
                                                            "The app is defined as a Databricks App; it is not deployed yet, so the demo runs locally against the workspace.")
table(s, [
    ["Service", "What it does in StormSense", "Where"],
    ["MLflow", "Tracks each forecaster run: Poisson loss, validation window, features, metrics", "/Shared/stormsense-demand-forecast"],
    ["Model Serving", "stormsense-forecaster (scale to zero) scores the what-if simulator; a serving chat model drives the storm desk", "whatif.py, agent.py"],
    ["Serverless SQL warehouse", "Every planner screen reads through fixed, parameterised statements; approvals are guarded updates", "dbx.py, sources/databricks.py"],
    ["Genie", "The Ask space answers planner questions over eight tables, read-only", "StormSense Ask space"],
    ["Databricks Apps", "One process, own service principal, linked to the warehouse and the Ask space. Defined, not yet deployed", "backend/app.yaml"],
    ["AI/BI dashboard", "StormSense overview: protected sales, stores at risk, forecast accuracy. Deployed, not yet visually checked", "dashboards/"],
    ["Databricks SDK", "SQL, Genie and serving calls from the API, with retries and a warming-up state", "sources/databricks.py"],
], left=365760, top=1450000, col_w=[2200000, 6500000, 2757432], row_h=560000, size=12)
footnote(s, "Not used: Agent Bricks, AutoML, classic clusters, personal access tokens.")

s = new("Title Only", "The daily job, task by task", "Runs at 6:00 AM Eastern on serverless compute. Each task is safe to re-run and retries twice. "
                                                    "A failed run emails the account that deployed it.")
table(s, [
    ["#", "Task", "What it does", "Guarantee"],
    ["1", "Refresh weather", "Ten-day National Weather Service forecast per store", "Fails rather than serve stale weather"],
    ["2", "Data quality", "Lakeflow pipeline drops rows that break the rules", "Bad rows never reach features"],
    ["3", "Features", "Lags, calendar and weather features per store and product", "Only what was known on the day"],
    ["4", "Score", "Champion forecaster writes seven days per pair", "Re-running a day replaces that day only"],
    ["5", "Gaps", "Projected stock, days of cover, first day each store runs low", "Approved moves count as stock arriving or leaving"],
    ["6", "Learn from feedback", "Rejection reasons become route penalties", "Penalties re-rank; they never add or remove moves"],
    ["7", "Recommendations", "Nearest-source matching proposes transfers", "MERGE refreshes pending rows only"],
    ["8", "Verify", "Checks counts, baselines and invariants", "Fails loudly"],
], left=365760, top=1400000, col_w=[500000, 2300000, 4900000, 3757432], row_h=500000, size=12)

s = new("Title Only", "The forecaster has to earn its place", "On sample data the forecaster's weighted error is about 0.40, against 0.67 for same as last week and "
                                                             "0.57 for the 28-day average. It is promoted to champion only if it beats both.")
cd = CategoryChartData()
cd.categories = ["Same as last week", "28-day average", "StormSense forecaster"]
cd.add_series("Weighted error (lower is better)", [0.67, 0.57, 0.40])
ch = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Emu(365760), Emu(1450000), Emu(6400000), Emu(4500000), cd).chart
style_chart(ch, legend=False, number_format='0.00')
pts = ch.plots[0].series[0].points
for i, rgb in enumerate([MUTED, MUTED, TEAL]):
    pts[i].format.fill.solid()
    pts[i].format.fill.fore_color.rgb = rgb
textbox(s, 7000000, 1450000, 4823192, 4500000, [
    ("How it is trained", 0, True),
    ("Gradient-boosted regression with Poisson loss (scikit-learn), already on serverless compute", 0),
    ("Time split: the last 28 days are held out, never a random split", 0),
    ("Lag features equal the sales exactly seven days earlier; the target is in no feature", 0),
    ("Prediction intervals come from validation windows", 0),
    ("Tracked in MLflow; registered in Unity Catalog with the alias champion only if it beats both baselines", 0),
    ("Everything downstream loads by alias, never by version", 0),
], size=14)
footnote(s, "Sample data. Counts per store and day are small, so part of the error is irreducible noise.")

s = new("Title Only", "Approving a transfer: safe by construction", "The API looks up the role, updates only rows still pending, stamps the request id, "
                                                                     "and writes audit rows for both the approved and the skipped. A second planner is told already handled.")
picture_fit(s, f"{S}/arch-approve-transfer-crop.png", 365760, 1350000, 11457432, 4700000)

s = new("Title and Content", "Security model", "The short version for a security reviewer: the browser never sees a credential, a table name or a query.")
fill(s, 1, [
    "Sign-in: Databricks Apps signs people in with their workspace account; roles viewer, planner and admin live in the app_users table.",
    "Service principal: the app runs as its own principal with read access to the tables and write access only to transfers and the audit trail.",
    "SQL: every statement is a constant string with bound parameters; a static test fails the build if request data ever reaches SQL text.",
    "Approvals: UPDATE only rows still PENDING, stamped with the request id, so repeats are reported, never applied twice.",
    "Browser: strict content security policy, no framing, same-origin only, a custom header on every change, request size limit, rate limit on Ask.",
    "Uploads are off unless switched on; the Ask space and the storm desk can only read, and nothing they return is executed.",
], size=15)

s = new("Title Only", "Deployed from code, end to end", "Sign in, deploy the data bundle, run the build job, verify, create the Ask space, deploy the app, grant least privilege, "
                                                        "smoke test with ten questions on real data. Nothing is assembled by hand in the workspace.")
picture_fit(s, f"{S}/arch-deploy-crop.png", 365760, 1350000, 11457432, 4700000)
footnote(s, "make deploy runs the whole path. The Databricks App step is defined and ready; it has not been run in production yet.")

s = new("Title Only", "Transfer lifecycle: only pending can change", "A recommendation is saved as pending and ends approved, rejected or withdrawn. "
                                                                     "Decided rows are never overwritten by the next run.")
picture_fit(s, f"{S}/arch-transfer-lifecycle-crop.png", 365760, 1350000, 11457432, 4700000)

# ================================================================================================
# 05 DEMO AND PROOF
# ================================================================================================
s = T[10]
section(s, "05", "Demo and proof", "Five screens in three minutes, on sample data. Then the tests that back it.")
note(s, "Switch to the browser. The app is open on /today with the Sample data label visible.")
order.append(s)

s = new("Title Only", "Demo flow: three minutes, on sample data", "Run from make dev-sample. Approvals reset when the sample server restarts.")
textbox(s, 365760, 1450000, 6300000, 4600000, [
    ("1.  Today: urgent moves, stores running low, the next alert, and what changed since the last visit.", 0),
    ("2.  Transfers: read one reason aloud, approve the first two urgent moves. See the safety orders if demand runs high.", 0),
    ("3.  Stores: Orlando's generators run low on Thursday. Switch the best-seller view from heat to wind.", 0),
    ("4.  Ask: \"Which stores will run out of generators this week?\" One sentence, one table, read-only.", 0),
    ("5.  History: who approved what, when. A second window tries the same approval: already handled by someone else.", 0),
], size=16)
picture_fit(s, f"{SHOTS}/app-transfer-approval-dialog.png", 6900000, 1450000, 4923192, 4600000)

s = new("Photo and Statement", "Ask: plain words in, one sentence out", "Ask runs a live Genie query. It answered all ten sample questions correctly on the workspace data, and it cannot change anything.")
ph(s, 16).insert_picture(f"{S}/app-ask.png")
fill(s, 14, [
    ("Read-only questions", 0, True),
    ("Suggested questions, or type your own", 1),
    ("The answer is one plain sentence; the detail is in a small table", 1),
    ("SQL is never shown, and nothing Ask returns is executed", 1),
    ("Rate-limited per person; technical words are removed from answers", 1),
], size=15)

s = new("Two Content", "Proof: tests, checks and continuous integration", "Numbers come from running the suites in the repository on the day of writing.")
fill(s, 1, [
    ("Automated tests", 0, True),
    ("182 backend and data tests pass (pytest)", 1),
    ("68 frontend unit tests pass (Vitest); typecheck and lint clean", 1),
    ("Browser tests (Playwright) run in CI against the built app, including accessibility checks", 1),
    ("Contract check: generated types, sample data and the data dictionary must match the code", 1),
], size=15)
fill(s, 2, [
    ("What the tests prove", 0, True),
    ("Generators sell 3x or more on storm days; coolers 1.3x or more on hot days", 1),
    ("Time split by date; lag-7 equals sales seven days earlier; the target is in no feature", 1),
    ("The forecaster beats both baselines; at least five pending recommendations", 1),
    ("No request data ever reaches SQL text; banned technical words never reach the UI", 1),
    ("Approvals change only pending rows; a repeat is harmless; a viewer cannot approve", 1),
], size=15)

s = new("Two Content", "Status: what runs today, and what is next to switch on", "Be exact. Running means it has run green in the workspace.")
fill(s, 1, [
    ("Running in the workspace", 0, True),
    ("About 15 Delta tables in Unity Catalog, built by serverless notebooks", 1),
    ("Forecaster registered as champion, beating both baselines", 1),
    ("Daily job at 6:00 AM Eastern with live National Weather Service weather", 1),
    ("The Ask space, created from code over eight tables", 1),
    ("The app, run locally, reading and writing the workspace with an audit trail", 1),
], size=15)
fill(s, 2, [
    ("Defined, not yet switched on", 0, True),
    ("Hosting as a Databricks App: ready, deploys with one command, not yet run in production", 1),
    ("Real sales, stock and weather feeds in place of the sample tables", 1),
    ("The storm trigger job, built and paused", 1),
    ("AI/BI dashboard, deployed but not yet checked visually", 1),
    ("Forecast monitoring and row-level security", 1),
], size=15)

# ================================================================================================
# 06 ROADMAP AND THE ASK
# ================================================================================================
s = T[12]
section(s, "06", "Roadmap and the ask", "What comes next on Databricks, the risks we state openly, and the one thing we ask for.")
note(s, "Three columns of roadmap, the limits, then the ask. Keep the ask to one sentence.")
order.append(s)

s = new("Three Content", "Roadmap", "Each item names the Databricks feature it uses. The first column is configuration and a notebook each.")
fill(s, 1, [("Next 30 days", 0, True), "Deploy the Databricks App", "Lakehouse Monitoring on forecast drift and error",
            "System tables for cost and access", "Row-level security: planners see their own region", "Publish the AI/BI dashboard"], size=14)
fill(s, 2, [("Next quarter", 0, True), "Store-manager assistant with Agent Bricks and Vector Search over storm procedures",
            "Markdown price optimisation with a controlled experiment", "Best sellers and what comes next, per weather",
            "Auto Loader for store feeds", "Pilot in two or three stores against a control"], size=14)
fill(s, 13, [("Later", 0, True), "Lakebase for approvals and the audit trail", "Delta Sharing with an insurer for storm cover evidence",
             "Streaming warnings instead of a 15-minute schedule", "Supplier replenishment drafts", "Thousands of stores: move driver-side pandas to Spark"], size=14)

s = new("Title and Content", "Risks and limits we state openly", "Naming the limits first is the strongest answer to hard questions.")
fill(s, 1, [
    "Sample data throughout: real sales, stock and weather feeds are not connected yet.",
    "Protected sales are gross revenue, not profit; the 30% margin is a default until stores set their own.",
    "The backtest is an upper bound and ignores pack sizes and truck limits.",
    "Forecast error is about 0.40 on sample data; counts per store and day are small, so noise remains.",
    "On the live workspace, the first query can wait minutes while the SQL warehouse starts.",
    "Upload routes have no sign-in; they are off unless STORMSENSE_INGEST_ENABLED=1.",
    "The Databricks App is defined but not deployed; the demo runs locally against the workspace.",
], size=15)

s = new("Big Statement", notes_text="End where you started: the Thursday store. Then the ask. Stop talking after thank you.")
fill(s, 1, [
    ("Stock is already in the network. StormSense moves it to where it sells.", 0, True),
    ("Our ask: test one option, in one region, this season, against control stores.", 0),
    ("We will come back with a measurement, not a model.", 0),
], size=30, space_after=20)

# ---- End, closing, copyright ----------------------------------------------------------------------
s = T[14]
ph(s, 10).text_frame.text = "Thank you"
note(s, "Open for questions.")
order.append(s)
note(T[15], "Template closing slide.")
note(T[16], "Template copyright and confidentiality notice. Keep it as the last slide.")
order.append(T[15])
order.append(T[16])

# ---- keep only the slides in `order`, in that sequence ------------------------------------------------
sldIdLst = prs.slides._sldIdLst
keep = {id(sl.part) for sl in order}
by_part = {}
for sldId in list(sldIdLst):
    by_part[id(prs.part.related_part(sldId.rId))] = sldId
for sldId in list(sldIdLst):
    if id(prs.part.related_part(sldId.rId)) not in keep:
        prs.part.drop_rel(sldId.rId)
        sldIdLst.remove(sldId)
for e in list(sldIdLst):
    sldIdLst.remove(e)
for sl in order:
    sldIdLst.append(by_part[id(sl.part)])

# ---- slide transitions: a quiet fade on every slide, a push on section headers -------------------------
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
SECTION_LAYOUT = "Section Header - Big Number"
for sl in prs.slides:
    sld = sl._element
    for old in sld.findall(f"{{{P}}}transition"):
        sld.remove(old)
    tr = etree.SubElement(sld, f"{{{P}}}transition")
    tr.set("spd", "med")
    if sl.slide_layout.name == SECTION_LAYOUT:
        push = etree.SubElement(tr, f"{{{P}}}push")
        push.set("dir", "l")
    else:
        etree.SubElement(tr, f"{{{P}}}fade")
    # <p:transition> must sit after <p:clrMapOvr> and before <p:timing>/<p:extLst>
    sld.remove(tr)
    anchor = sld.find(f"{{{P}}}clrMapOvr")
    if anchor is None:
        anchor = sld.find(f"{{{P}}}cSld")
    anchor.addnext(tr)

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides))
