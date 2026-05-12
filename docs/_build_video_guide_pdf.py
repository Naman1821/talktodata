"""
Generate the Talk_To_Data_Video_Production_Guide.pdf on the user's Desktop.

This is a one-shot helper: edit CONTENT below and re-run to rebuild the PDF.
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUT = Path(__file__).resolve().parent / "Talk_To_Data_Video_Production_Guide.pdf"


# ---------- Styles ----------

styles = getSampleStyleSheet()

H1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=27,
    spaceBefore=14,
    spaceAfter=12,
    textColor=colors.HexColor("#0f172a"),
)
H2 = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=21,
    spaceBefore=14,
    spaceAfter=8,
    textColor=colors.HexColor("#1e3a8a"),
)
H3 = ParagraphStyle(
    "H3",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=12.5,
    leading=16,
    spaceBefore=10,
    spaceAfter=6,
    textColor=colors.HexColor("#0ea5e9"),
)
BODY = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=10.5,
    leading=15,
    spaceAfter=6,
    alignment=TA_LEFT,
    textColor=colors.HexColor("#111827"),
)
BULLET = ParagraphStyle(
    "Bullet",
    parent=BODY,
    leftIndent=14,
    bulletIndent=2,
    spaceAfter=3,
)
CODE = ParagraphStyle(
    "Code",
    parent=BODY,
    fontName="Courier",
    fontSize=9.5,
    leading=12.5,
    leftIndent=10,
    rightIndent=10,
    textColor=colors.HexColor("#0b1220"),
    backColor=colors.HexColor("#f1f5f9"),
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=8,
)
NOTE = ParagraphStyle(
    "Note",
    parent=BODY,
    fontName="Helvetica-Oblique",
    fontSize=10,
    leftIndent=10,
    rightIndent=10,
    textColor=colors.HexColor("#0f172a"),
    backColor=colors.HexColor("#fef9c3"),
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=8,
)
DIALOG_NAME = ParagraphStyle(
    "DialogName",
    parent=BODY,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor("#0ea5e9"),
    spaceBefore=4,
    spaceAfter=2,
)
DIALOG_LINE = ParagraphStyle(
    "DialogLine",
    parent=BODY,
    leftIndent=14,
    fontSize=10.5,
    leading=15,
    textColor=colors.HexColor("#111827"),
    spaceAfter=6,
)
SCREEN_CUE = ParagraphStyle(
    "ScreenCue",
    parent=BODY,
    fontName="Helvetica-Oblique",
    fontSize=9.5,
    leftIndent=14,
    textColor=colors.HexColor("#7c2d12"),
    backColor=colors.HexColor("#ffedd5"),
    borderPadding=4,
    spaceBefore=2,
    spaceAfter=8,
)
TIME_BAND = ParagraphStyle(
    "TimeBand",
    parent=BODY,
    fontName="Helvetica-Bold",
    fontSize=11,
    textColor=colors.white,
    backColor=colors.HexColor("#0f172a"),
    borderPadding=4,
    spaceBefore=10,
    spaceAfter=6,
)


# ---------- Helpers ----------


def p(text: str, style=BODY):
    return Paragraph(text, style)


def bullet(text: str):
    return Paragraph(f"• {text}", BULLET)


def num(n: int, text: str):
    return Paragraph(f"<b>{n}.</b> {text}", BULLET)


def code(text: str):
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )
    return Paragraph(safe, CODE)


def note(text: str):
    return Paragraph("<b>Note:</b> " + text, NOTE)


def hr():
    return HRFlowable(
        width="100%",
        thickness=0.6,
        color=colors.HexColor("#cbd5e1"),
        spaceBefore=6,
        spaceAfter=10,
    )


def time_band(label: str):
    return Paragraph(label, TIME_BAND)


def speaker(name: str, line: str, mood: str | None = None):
    head = name + (f"  <i>({mood})</i>" if mood else "")
    return [Paragraph(head, DIALOG_NAME), Paragraph(line, DIALOG_LINE)]


def cue(text: str):
    return Paragraph("[ON SCREEN] " + text, SCREEN_CUE)


def two_col_table(rows: list[tuple[str, str]], col_widths=(4.5 * cm, 11.5 * cm)):
    data = [
        [Paragraph("<b>" + a + "</b>", BODY), Paragraph(b, BODY)] for a, b in rows
    ]
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


# ---------- Page decorations ----------


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(2 * cm, 1.2 * cm, "Talk to Data — 5-Minute Submission Video Guide")
    canvas.drawRightString(
        A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}"
    )
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.line(2 * cm, 1.55 * cm, A4[0] - 2 * cm, 1.55 * cm)
    canvas.restoreState()


# ---------- CONTENT ----------

# Convenience names — change anywhere if needed.
F1 = "PRESENTER 1"
F2 = "PRESENTER 2"
BOTH = "BOTH"

flowables: list = []


def add(*items):
    for item in items:
        if isinstance(item, list):
            for sub in item:
                flowables.append(sub)
        else:
            flowables.append(item)


# ===== Cover page =====

add(
    Spacer(1, 4 * cm),
    p(
        "<para align='center'><font size='28'><b>Talk to Data</b></font></para>",
        ParagraphStyle("CoverTitle", parent=BODY, alignment=1, fontSize=28, leading=36),
    ),
    Spacer(1, 0.3 * cm),
    p(
        "<para align='center'><font size='14'>5-Minute Submission Video — Complete Production Guide</font></para>",
        ParagraphStyle("CoverSub", parent=BODY, alignment=1, fontSize=14, leading=20, textColor=colors.HexColor("#475569")),
    ),
    Spacer(1, 1.2 * cm),
    p(
        "<para align='center'>From zero recording experience to a polished, engaging final video.<br/>"
        "Step-by-step. Word-for-word script. Editing checklist. Done in one weekend.</para>",
        ParagraphStyle("CoverDesc", parent=BODY, alignment=1, fontSize=11, leading=16, textColor=colors.HexColor("#334155")),
    ),
    Spacer(1, 4 * cm),
    p(
        "<para align='center'><b>Project:</b> NatWest Code for Purpose — Theme 1<br/>"
        "<b>Presenters:</b> Presenter 1 and Presenter 2 (replace names in lower thirds)<br/>"
        "<b>Target length:</b> 4:50 (under 5:00)<br/>"
        "<b>Format:</b> Webcam side-by-side + Screen recording PiP</para>",
        ParagraphStyle("CoverFoot", parent=BODY, alignment=1, fontSize=11, leading=18),
    ),
    PageBreak(),
)

# ===== Section 0 — How to use =====

add(
    p("Section 0 — How to use this guide", H1),
    hr(),
    p(
        "This guide walks you and your friend through the entire process of producing a 5-minute "
        "submission video for the project — from the moment you set up the room to the moment you "
        "click Submit. It is intentionally exhaustive: read it once end-to-end, then keep it open "
        "during the shoot.",
    ),
    p(
        "Roles used everywhere in this guide:",
    ),
    bullet("<b>Presenter 1</b> — primary narrator and demo driver."),
    bullet("<b>Presenter 2</b> — co-host, problem framer, and tech-stack speaker."),
    bullet("<b>BOTH</b> — speaking together (intro hook and outro)."),
    p(
        "Total time you should plan for:",
    ),
    bullet("Pre-production setup: 1.5 hours"),
    bullet("Recording (with retakes): 1.5–2 hours"),
    bullet("Editing: 2–3 hours"),
    bullet("QC + export + upload: 30 minutes"),
    p("So roughly half a day if you're focused. Less if you've recorded videos before."),
    note(
        "If you only have one camera, record the two of you sitting side-by-side on a single webcam. "
        "If you have two laptops/cameras, use both — the editing tutorial covers both layouts."
    ),
    PageBreak(),
)

# ===== Section 1 — Equipment & Software =====

add(
    p("Section 1 — Equipment & Software Checklist", H1),
    hr(),
    p("Hardware", H2),
    bullet("1 or 2 laptops (one runs Streamlit + screen recording; another can be a second webcam)."),
    bullet("Phone tripod (only if you're using your phone as a second webcam)."),
    bullet("Earphones with inline mic, OR a USB mic — anything is better than the laptop's built-in mic."),
    bullet("A quiet room — close the door, switch fans/AC off if loud."),
    bullet("A simple background — plain wall, bookshelf, or curtain. Avoid moving objects behind you."),
    bullet("A lamp or ring light positioned in front of your face (not behind)."),
    p("Software (all free)", H2),
    bullet("<b>OBS Studio</b> — recording. Captures screen + webcam(s) + mic in one go. obsproject.com"),
    bullet("<b>DaVinci Resolve</b> — editing. Pro-grade, free. blackmagicdesign.com"),
    bullet("<b>CapCut for Mac</b> — easier editor if Resolve feels heavy. capcut.com"),
    bullet("<b>Cursor or VS Code</b> — to show the code on screen during the demo."),
    bullet("<b>Chrome / Brave</b> — to run the Streamlit app and show slides."),
    bullet("<b>Google Slides or Keynote</b> — for two simple slides (title card + tech stack)."),
    p("Royalty-free assets (for music and minor SFX)", H2),
    bullet("Music: pixabay.com/music or YouTube Audio Library — search 'corporate inspiring' or 'soft background'."),
    bullet("SFX (whoosh / click / pop): pixabay.com/sound-effects — pick gentle, short ones."),
    bullet("Stock B-roll (optional): mixkit.co or pexels.com/videos."),
    p("Phone-as-a-webcam options (if you don't have a second camera)", H2),
    bullet("Mac: use macOS Continuity Camera (System Settings → General → AirDrop & Handoff)."),
    bullet("Cross-platform: install <b>Camo</b> or <b>iVCam</b> on phone + companion app on laptop."),
    PageBreak(),
)

# ===== Section 2 — Pre-production setup =====

add(
    p("Section 2 — Pre-Production Setup (90 minutes)", H1),
    hr(),
    p("2.1 Workspace setup", H2),
    bullet("Clean the desk — only the laptop, mic, and a small water bottle visible."),
    bullet("Sit so the light source (window or lamp) is in front of you, slightly to one side at 45°."),
    bullet("Both presenters: solid-coloured shirts. Avoid stripes, logos, and pure white (overexposes)."),
    bullet("Decide framing: head + shoulders, eyes about 1/3 down from the top of the frame."),
    bullet("If sitting side-by-side, leave a small gap between shoulders so each face is fully visible."),
    p("2.2 Computer prep", H2),
    bullet("Close every app you don't need — Slack, WhatsApp Web, mail, Spotify, etc."),
    bullet("Mac: System Settings → Focus → enable Do Not Disturb. iPhones too."),
    bullet("Set browser to Full Screen, hide bookmarks bar (View → Hide Bookmarks Bar)."),
    bullet("Hide desktop icons: Mac — Finder Settings → General → uncheck 'Show items'. Or use a clean Desktop wallpaper."),
    bullet("Increase Terminal/Cursor font size to 16–18pt so it's readable on video."),
    bullet("Pick a single light/dark theme — don't switch between them on camera."),
    p("2.3 Streamlit and project prep", H2),
    code(
        "cd /Users/naman/Desktop/Talk-to-Data-main\n"
        "source .venv/bin/activate\n"
        "streamlit run src/talk_to_data/app.py"
    ),
    bullet("Open http://localhost:8501 in your browser, full-screen the window."),
    bullet("Pre-paste your Gemini API key in the right-hand panel and click Save key."),
    bullet("Have <b>data/sample_hackathon.csv</b> ready in Finder (drag-zone visible)."),
    bullet("Have a small sample PDF ready (2–3 pages, any topic) — also visible in Finder."),
    bullet(
        "Open Cursor (or VS Code) on the project folder. Open these files in this exact tab order:"
    ),
    bullet("&nbsp;&nbsp;&nbsp;1. README.md"),
    bullet("&nbsp;&nbsp;&nbsp;2. src/talk_to_data/app.py"),
    bullet("&nbsp;&nbsp;&nbsp;3. src/talk_to_data/views.py"),
    bullet("&nbsp;&nbsp;&nbsp;4. src/talk_to_data/analytics.py"),
    bullet("&nbsp;&nbsp;&nbsp;5. src/talk_to_data/llm_layer.py"),
    bullet("&nbsp;&nbsp;&nbsp;6. src/talk_to_data/pgvector_store.py"),
    p("2.4 Slides to prepare (only 2 needed)", H2),
    bullet(
        "<b>Slide A — Title card:</b> 'Talk to Data — Theme 1' with both presenters' names below. "
        "Background: deep navy gradient (#0f172a → #1e3a8a)."
    ),
    bullet(
        "<b>Slide B — Tech stack:</b> 6 small logo tiles — Python, Streamlit, Pandas, Gemini, "
        "Postgres+pgvector, Docker."
    ),
    bullet("Open both in a separate browser window, presenter view ON, ready to F5 / Cmd+Enter."),
    p("2.5 OBS Studio setup", H2),
    p(
        "Open OBS, run Auto-Configuration Wizard once, choose <b>Optimise for recording</b>. "
        "Then create one scene with three sources visible:",
    ),
    num(1, "Scene name: <b>Main Demo</b>."),
    num(2, "Add Source → <b>Display Capture</b>. Pick the screen with Streamlit/Cursor."),
    num(3, "Add Source → <b>Video Capture Device</b> for Friend 1's webcam. Resize and place bottom-left."),
    num(4, "Add Source → <b>Video Capture Device</b> for Friend 2's webcam. Resize and place bottom-right."),
    num(5, "Add Source → <b>Audio Input Capture</b>. Pick your USB / earphone mic. Test levels (peaks at -12 to -6 dB)."),
    p("Optional second scene: <b>Both Faces</b> — both webcams large, no screen capture. Use this for intros and outros."),
    p("OBS settings to tweak (Settings menu)", H3),
    bullet("Output → Recording → Format <b>MP4</b> (or MKV if you'll remux later), Quality High, encoder Apple VT H.264 (Mac) or NVENC."),
    bullet("Video → Base canvas 1920×1080, Output 1920×1080, FPS 30."),
    bullet("Audio → Sample rate 48 kHz, Channels Stereo."),
    bullet("Hotkeys → set <b>Cmd+R</b> for Start/Stop Recording so you don't have to click."),
    p("2.6 Practice run", H2),
    bullet("Read the entire script aloud once — time it. Aim for 4:45–4:55."),
    bullet("Do a 30-second test recording. Play it back. Check audio is clear and webcam is sharp."),
    bullet("Adjust lamp / mic / fonts as needed. Re-test."),
    PageBreak(),
)

# ===== Section 3 — Speaking pattern =====

add(
    p("Section 3 — Role Assignment & Speaking Pattern", H1),
    hr(),
    p(
        "The 5 minutes are divided into 9 blocks. Two presenters keep energy alive by handing off, "
        "with one moment of dual energy at the start and the very end."
    ),
    Spacer(1, 0.2 * cm),
    two_col_table(
        [
            ("0:00 – 0:15  Hook intro", "BOTH (alternating one line each)"),
            ("0:15 – 0:45  Problem", "Friend 2 (sets the stage, slightly serious tone)"),
            ("0:45 – 1:15  Solution overview", "Friend 1 (confident, owns the story)"),
            ("1:15 – 1:50  Tech stack", "Friend 2 (technical credibility)"),
            ("1:50 – 2:30  Demo: CSV upload + first question", "Friend 1 (Friend 2 chips in once)"),
            ("2:30 – 3:05  Demo: second CSV question", "Friend 2 leads, Friend 1 narrates clicks"),
            ("3:05 – 3:35  Demo: PDF + AI Q&A", "Friend 2 (clean handoff)"),
            ("3:35 – 4:10  Code walkthrough (brief)", "Friend 1 (engineering pride)"),
            ("4:10 – 4:40  Why this stands out", "BOTH (alternate sentences)"),
            ("4:40 – 5:00  Outro + thanks", "BOTH (smile, slight wave)"),
        ]
    ),
    Spacer(1, 0.4 * cm),
    note(
        "Tone reminder: intro and outro are warm and energetic. Problem block is calmer and serious. "
        "Demo is curious / discovering tone. Code peek is proud / quietly confident."
    ),
    PageBreak(),
)

# ===== Section 4 — FULL SCRIPT =====

add(
    p("Section 4 — The Full 5-Minute Script (word for word)", H1),
    hr(),
    p(
        "Total target: ~720 words (≈ 4:48 at 150 words per minute). Speakers are marked clearly — "
        "follow the order. On-screen cues tell you what should be visible during each line."
    ),
)

# 0:00 – 0:15
add(
    time_band("0:00 – 0:15  •  Hook intro  •  Both faces on camera"),
    cue("Scene: Both Faces (no screen capture). Title card overlay 'Talk to Data — Theme 1' with both names appears for 3 seconds, then fades out."),
    *speaker(F1, "Hi everyone! I'm <b>[Friend 1's full name]</b>…", mood="smile, energetic"),
    *speaker(F2, "…and I'm <b>[Friend 2's full name]</b>.", mood="energetic"),
    *speaker(F1, "And we're here with our submission for NatWest Code for Purpose, Theme 1 — meet <b>Talk to Data</b>."),
    *speaker(F2, "A tool that turns your spreadsheets and PDFs into instant, trustworthy answers — no SQL, no data team."),
)

# 0:15 – 0:45
add(
    time_band("0:15 – 0:45  •  Problem  •  Friend 2 leads, slight serious tone"),
    cue("Cut to a simple slide listing 3 pain points: 'Excel limits', 'BI takes weeks', 'Generic AI hallucinates numbers'. Friend 2's webcam tile in bottom-right."),
    *speaker(F2, (
        "Every day, business teams sit on heaps of data — sales reports, branch CSVs, policy PDFs. "
        "But to answer a simple question like <i>'why did revenue dip last week?'</i> they have to "
        "wait for a data team or fight Excel for hours."
    )),
    *speaker(F2, (
        "Generic AI chatbots feel tempting — but they hallucinate numbers. For a bank, that's a "
        "non-starter. So we asked: can we build a tool a non-technical user can trust <i>in seconds</i>?"
    )),
)

# 0:45 – 1:15
add(
    time_band("0:45 – 1:15  •  Solution overview  •  Friend 1 leads, confident"),
    cue("Slide cuts to two side-by-side boxes labelled 'Pandas (numbers)' and 'Gemini (words, optional)'. Friend 1's webcam tile in bottom-right."),
    *speaker(F1, (
        "That's where <b>Talk to Data</b> comes in. The user just uploads a CSV or PDF, types a "
        "question in plain English, and gets a verified answer with the numbers, charts, sources, "
        "and assumptions — all in one screen."
    )),
    *speaker(F1, (
        "Here's the key idea: <b>all numbers are computed locally with pandas. AI only writes the "
        "summary on top — and only from the verified result.</b> That means the user can always "
        "trust the table, even if AI is off."
    )),
)

# 1:15 – 1:50
add(
    time_band("1:15 – 1:50  •  Tech stack  •  Friend 2"),
    cue("Tech stack slide: 6 logo tiles (Python, Streamlit, Pandas, Gemini, Postgres+pgvector, Docker). Friend 2 webcam tile bottom-right."),
    *speaker(F2, (
        "Under the hood, we use <b>Python and Streamlit</b> for a beautiful, instant web UI. "
        "<b>Pandas and NumPy</b> crunch the numbers locally. <b>pypdf</b> extracts PDF text."
    )),
    *speaker(F2, (
        "For optional AI, we use <b>Google Gemini's free tier</b> — and we auto-pick the best model "
        "the user's API key can access, so demos don't break on hardcoded model IDs. Finally, "
        "<b>Postgres with pgvector</b> powers semantic search over PDFs — all running together in "
        "<b>Docker</b> with one command."
    )),
)

# 1:50 – 2:30
add(
    time_band("1:50 – 2:30  •  Demo — CSV upload + first question  •  Friend 1 driving"),
    cue("Switch to Main Demo scene: full screen of browser at localhost:8501. Both webcams as small PiP tiles in bottom corners."),
    *speaker(F1, "Let's see it live."),
    cue("Drag and drop data/sample_hackathon.csv onto the upload area."),
    *speaker(F1, (
        "This is the app running locally. I'll upload our sample CSV — branch sales data. "
        "Notice — we instantly see the row count, the inferred metric column, and the category "
        "dimension. The app figures the schema out for you."
    )),
    cue("Click in the question box, type 'Why did revenue change last month?', click Generate Insight."),
    *speaker(F2, "Now let's ask a real business question — <i>'Why did revenue change last month?'</i>"),
    *speaker(F1, (
        "And in under a second — there it is. A change-driver analysis showing which categories "
        "pulled revenue up, which pulled it down, with percentages, the source columns, and the "
        "assumptions clearly listed."
    )),
)

# 2:30 – 3:05
add(
    time_band("2:30 – 3:05  •  Demo — verified + AI summary  •  Friend 2 leads, Friend 1 narrates clicks"),
    cue("Scroll down to show the green 'AI explanation (Gemini, grounded)' card. Then scroll back up, change the question to 'North vs South', click Generate Insight."),
    *speaker(F2, (
        "And below — Gemini gives us a plain-English summary using <b>only those verified numbers</b>. "
        "So even our manager can read this without knowing what a percentile is."
    )),
    *speaker(F1, "Let's try a comparison — <i>'North vs South'</i>."),
    *speaker(F2, (
        "Our query parser detects the <i>'X vs Y'</i> pattern, runs an entity comparison, shows a "
        "bar chart, and the 10%-gap rule flags whether the difference is practically significant."
    )),
)

# 3:05 – 3:35
add(
    time_band("3:05 – 3:35  •  Demo — PDF + AI Q&A  •  Friend 2 leads"),
    cue("Click the (×) on the file uploader, drag a sample PDF onto it. Scroll to the AI Q&A tab, type a question, click Ask AI."),
    *speaker(F1, "Now the PDF side. I'll upload a sample report."),
    *speaker(F2, (
        "For PDFs, we have three answer modes. Offline keyword search — works even without internet. "
        "AI Q&A — answers strictly from the document text, never outside knowledge. And if Postgres "
        "is running, semantic search over chunked embeddings — powered by Gemini's "
        "<i>text-embedding-004</i>, stored as 768-dimension vectors in pgvector."
    )),
    cue("Briefly show one AI answer popping up — read the first sentence aloud as proof."),
)

# 3:35 – 4:10
add(
    time_band("3:35 – 4:10  •  Code peek  •  Friend 1 leads, quietly proud"),
    cue("Cmd+Tab to Cursor. Show the file tree expanded for src/talk_to_data/. Then open analytics.py for 3 seconds. Then open llm_layer.py and highlight the system prompt lines."),
    *speaker(F1, (
        "A quick peek at the code. After our cleanup, the entire app lives in one folder — "
        "<b>src/talk_to_data/</b>. <i>app.py</i> is the Streamlit entry. <i>views.py</i> is pure UI. "
        "<i>analytics.py</i> has every pandas function — like <i>change_drivers</i>, which "
        "decomposes period-over-period contribution by category."
    )),
    *speaker(F1, (
        "And <i>llm_layer.py</i> is where the AI lives — but notice the system prompt: "
        "<b>'use only facts and numbers from the JSON, no outside knowledge'</b>. That single line "
        "is our trust contract."
    )),
)

# 4:10 – 4:40
add(
    time_band("4:10 – 4:40  •  Why this stands out  •  Both alternate"),
    cue("Cut back to Both Faces scene. No screen capture for this 30 seconds."),
    *speaker(F2, (
        "What makes this different? <b>Graceful degradation</b>. No API key — verified results still "
        "work. No internet — PDF line search still works. No database — all CSV analytics still "
        "work. Trust is the default; AI is the bonus."
    )),
    *speaker(F1, (
        "Plus we have <b>transparent UX</b> — sources, assumptions, and routing confidence are shown "
        "<i>before</i> any AI text. And every insight is exportable as a JSON audit trail."
    )),
)

# 4:40 – 5:00
add(
    time_band("4:40 – 5:00  •  Outro  •  BOTH"),
    cue("End-screen lower-third with both names + project name + GitHub URL. Soft music swell up, then fade."),
    *speaker(BOTH, "Thank you for watching!", mood="smile, slight wave"),
    *speaker(F1, "I'm <b>[Friend 1's full name]</b>…"),
    *speaker(F2, "…and I'm <b>[Friend 2's full name]</b>."),
    *speaker(F1, "This was <b>Talk to Data</b> — clarity, trust, and speed by design."),
)

add(
    Spacer(1, 0.3 * cm),
    note(
        "Word count: ≈ 720 words across all spoken lines — leaves ~10 seconds of breathing room "
        "for pauses, reactions, and music tails. If you go over 5 minutes, the first cut is the "
        "second tech-stack sentence; second cut is the second CSV demo question."
    ),
    PageBreak(),
)

# ===== Section 5 — Recording day =====

add(
    p("Section 5 — Recording Day, Step by Step", H1),
    hr(),
    p("5.1 The 60-minute pre-shoot checklist", H2),
    bullet("Both presenters: water bottle filled, washroom done, throat cleared."),
    bullet("Phones: Do Not Disturb on, face-down on the desk."),
    bullet("Laptop: notifications silenced, Slack/WhatsApp closed, Wi-Fi stable."),
    bullet("OBS: open the 'Main Demo' scene; run 30-sec test, confirm green VU bars on mic."),
    bullet("Streamlit: running in browser, sample CSV pre-loaded once just to confirm it works, then refresh to clear it."),
    bullet("Cursor: project open, tabs in the documented order."),
    bullet("Slides: open in another browser window, presenter view enabled, F5 ready."),
    bullet("Sample PDF: visible in Finder window so you can drag it instantly."),
    bullet("OBS hotkey for record: confirmed working (test record / stop)."),
    bullet("Lamp on, hair tidied, shirts smooth — look at yourself in the webcam preview once."),

    p("5.2 The recording sequence (do these in this order!)", H2),
    p("Take 1 — Slides only screen recording (≈ 30 sec)", H3),
    bullet("OBS scene: Main Demo, but you'll only show the slides."),
    bullet("Record yourself flipping from title card → tech stack slide → blank. No audio needed; you'll voice-over later."),
    bullet("Stop recording. Save with name 'Take_01_Slides.mp4'."),

    p("Take 2 — Live demo screen recording (≈ 90 sec)", H3),
    bullet("OBS scene: Main Demo. Friend 1 drives the mouse and narrates softly so you have a reference timing track."),
    bullet("Friend 2 stays silent during this take — only screen + Friend 1's voice."),
    bullet("Hit OBS record. Then in the browser: drag CSV → ask Q1 → scroll to AI answer → ask 'North vs South' → upload PDF → run AI Q&A → stop recording."),
    bullet("Don't worry about your narration being perfect; we'll re-record voice in Take 3."),
    bullet("Save as 'Take_02_Demo.mp4'."),

    p("Take 3 — Webcam + voice (full script, ≈ 5 min)", H3),
    bullet("OBS scene: Both Faces (or Main Demo if you want PiP webcams already composed)."),
    bullet("Both presenters in frame, OBS recording. Read the full script from Section 4 in order."),
    bullet("If you make a mistake, don't stop. Pause for 2 seconds, restart that line. Editing will fix it."),
    bullet("Do at least 2 full passes — pick the best later."),
    bullet("Save as 'Take_03_Webcam_Pass1.mp4', 'Take_03_Webcam_Pass2.mp4', etc."),

    p("Take 4 — B-roll / reaction shots (optional, ≈ 30 sec)", H3),
    bullet("Both presenters smiling, nodding, looking at screen, light laughter — 5-second clips each."),
    bullet("These are sprinkled in editing during the demo to add life."),
    bullet("Save as 'Take_04_Broll.mp4'."),

    p("5.3 Common issues and quick fixes during recording", H2),
    bullet("<b>Echo / hollow audio</b> → Use earphones with a mic; or move closer to the mic; or hang a folded blanket behind you."),
    bullet("<b>Webcam grainy</b> → Add light directly in front of the face. Bump exposure in OBS source settings."),
    bullet("<b>OBS dropping frames</b> → Lower output to 1280×720 30fps; or change encoder to Apple VT (Mac)."),
    bullet("<b>Streamlit feels slow</b> → Restart `streamlit run …`; close extra browser tabs."),
    bullet("<b>You forget a line</b> → Pause, take a breath, repeat the previous sentence and continue."),
    PageBreak(),
)

# ===== Section 6 — Editing =====

add(
    p("Section 6 — Editing Tutorial (DaVinci Resolve, free)", H1),
    hr(),
    p(
        "If DaVinci feels heavy, the same idea works in CapCut for Mac — every step has an equivalent there. "
        "We use Resolve in the example because it produces a more polished result and is free."
    ),
    p("6.1 First-time setup", H2),
    num(1, "Download DaVinci Resolve from blackmagicdesign.com (free version)."),
    num(2, "Install. First launch may take a minute."),
    num(3, "<b>Project Manager</b> → New Project → name 'Talk to Data Submission'."),
    num(4, "<b>File → Project Settings</b> → Master Settings → Timeline resolution 1920×1080, frame rate 30."),

    p("6.2 Import all the takes", H2),
    num(1, "Open the <b>Media</b> tab (bottom strip)."),
    num(2, "Drag your 4 OBS files into the Media Pool."),
    num(3, "Right-click in Media Pool → New Bin. Create five bins:"),
    bullet("01 Webcam — Take_03_Webcam_Pass1, Pass2…"),
    bullet("02 Demo — Take_02_Demo"),
    bullet("03 Slides — Take_01_Slides"),
    bullet("04 BRoll — Take_04_Broll"),
    bullet("05 Music — your background music + any SFX"),

    p("6.3 Build the timeline (the core workflow)", H2),
    num(1, "Open the <b>Edit</b> tab."),
    num(2, "Drag the best webcam take to <b>V1</b> (Video track 1) and <b>A1</b> (Audio 1)."),
    num(3, "Right-click the clip in V1 → Decompose Compound Clip if it's grouped — make sure video and audio split."),
    num(4, "Watch through it. Mark the <b>start of demo</b> (where Friend 1 says 'Let's see it live')."),
    num(5, "Drag the demo screen recording onto <b>V2</b> (Video 2), aligned at that point."),
    num(6, "Drag the slides screen recording onto V2 too, placed at 0:15–1:50 area where the script needs slides."),

    p("6.4 Picture-in-picture during demo", H2),
    num(1, "Click the demo clip on V2. Open <b>Inspector</b> (right side)."),
    num(2, "Demo clip stays full screen. The webcam below it is hidden during this segment <b>except</b> for a small PiP tile."),
    num(3, "Method A (recommended): cut the webcam clip to take just a 200×200-pixel tile."),
    num(4, "Method B: keep the webcam clip on V1 full size, then place the demo on V2 with these Inspector → Transform values: <i>Zoom X 0.78, Zoom Y 0.78, Position X 110, Y -100</i> — this leaves a strip on the left where the webcam shows through."),
    num(5, "For a cleaner effect, use a fresh PiP layer: copy webcam clip up to V3, scale to Zoom 0.22, Position X 720, Y -380. Add a 4-pixel white border via Effects → ResolveFX Stylize → Stroke."),

    p("6.5 Cut out filler and silence", H2),
    bullet("Press <b>B</b> to enter Blade mode. Click on every 'um', long pause, or repeated take to slice."),
    bullet("Press <b>A</b> to return to Selection mode. Select the bad slice → press Backspace."),
    bullet("Hold <b>Shift+Backspace</b> to ripple-delete (closes the gap)."),
    bullet("Aim for snappy cuts; never leave more than 0.7 sec of silence."),

    p("6.6 Crossfades and transitions", H2),
    num(1, "Between major blocks (intro → problem, problem → solution, etc.) add a <b>Cross Dissolve</b> of 6–10 frames."),
    num(2, "From the Effects library, drag <b>Cross Dissolve</b> onto each cut."),
    num(3, "Don't overuse fancy transitions — they look amateur. 90% of cuts should be straight cuts."),

    p("6.7 Audio polish", H2),
    num(1, "Click the audio clip → Inspector → <b>Equalizer</b>: enable High-pass at 80 Hz to kill rumble."),
    num(2, "Add <b>Compressor</b>: ratio 3:1, threshold around -18 dB."),
    num(3, "Add <b>Voice Isolation</b> (Studio version) or use 'Noise Reduction' in the Fairlight tab if there's hiss."),
    num(4, "Drag background music onto <b>A3</b>. Lower its volume to about <b>-25 dB</b> in Inspector."),
    num(5, "Right-click the music clip → Smart Filter → 'Side-Chain to A1' so music ducks under your voice automatically."),
    num(6, "Add 1-second fade-in at the start, 2-second fade-out at the end of the music."),

    p("6.8 Lower thirds (names)", H2),
    num(1, "Effects library → Titles → drag <b>Lower Third</b> onto track V4 above everything."),
    num(2, "Edit text in Inspector: 'Friend 1's Name — Project Lead' (or 'Co-Presenter')."),
    num(3, "Show for 3–5 seconds the first time each presenter speaks (around 0:03 and 0:18)."),
    num(4, "Use a consistent font (e.g. Inter, Helvetica Neue) and the project's blue (#0ea5e9) accent."),

    p("6.9 Title card and end card", H2),
    num(1, "Open Fusion tab (advanced) OR simply use Effects → Titles → 'Text+'."),
    num(2, "Title card (first 3 seconds): 'Talk to Data — Theme 1' big, both names below in smaller font."),
    num(3, "End card (last 5 seconds): 'Thank you' + project name + GitHub URL."),
    num(4, "Background: solid #0f172a navy with a subtle radial gradient toward #1e3a8a."),

    p("6.10 Captions / subtitles (optional but strongly recommended)", H2),
    num(1, "Right-click on the timeline ruler → <b>Create Subtitles from Audio</b>."),
    num(2, "Resolve transcribes — review every line and fix any wrong words."),
    num(3, "Style: white text, black outline 2 px, font size 36, position bottom-third."),
    num(4, "Captions massively help non-native English viewers and people who watch on mute."),

    p("6.11 Color correction (quick pass)", H2),
    num(1, "Open the <b>Color</b> tab."),
    num(2, "Select all webcam clips. Use the Color Wheels: lift Lift slightly toward warm, push Gain slightly toward cool — keeps skin tones natural."),
    num(3, "Add a small Saturation boost (about +5)."),
    num(4, "If clips were handheld, apply Stabiliser (Color tab → Stabilization → Smooth)."),

    p("6.12 Final QC inside the editor", H2),
    bullet("Watch the entire video without pausing. Note timestamps of any issue."),
    bullet("Fix issues. Watch again."),
    bullet("Length must be under 5:00. Sweet spot: 4:45–4:55."),
    bullet("Listen with earphones — confirm no clipping (no red on the audio meter)."),
    bullet("Confirm both presenters' faces are well-lit and audio is balanced between speakers."),

    p("6.13 Export the final file", H2),
    num(1, "Open the <b>Deliver</b> tab."),
    num(2, "Preset: <b>YouTube 1080p</b>."),
    num(3, "Format: MP4. Codec: H.264. Audio: AAC 192 kbps, 48 kHz."),
    num(4, "Quality: Restrict to ~12,000 kbps."),
    num(5, "Filename: <b>Talk_to_Data_Submission_Final.mp4</b>."),
    num(6, "Add to Render Queue → Start Render. Wait until 100%."),
    PageBreak(),
)

# ===== Section 7 — QC =====

add(
    p("Section 7 — Final Quality Gate", H1),
    hr(),
    p("Open the exported file and tick every box before submitting."),
    bullet("[ ] Audio: clear, no clipping (no red meter), music quietly behind the voice."),
    bullet("[ ] Video: stable, colour consistent, both faces visible during intro/outro."),
    bullet("[ ] Text: zero spelling mistakes in titles, lower thirds, and captions."),
    bullet("[ ] Length: between 4:30 and 5:00. Aim for 4:48–4:55."),
    bullet("[ ] Both names visible at intro, outro, and at least one lower third in the middle."),
    bullet("[ ] Demo screen text is readable (zoom in on a phone to test — if you can read it, judges can)."),
    bullet("[ ] No accidental personal info on screen — no other browser tabs, no notification popups, no exposed Gemini key."),
    bullet("[ ] File size under 500 MB ideally — fits most upload limits comfortably."),
    bullet("[ ] Watched once with earphones, once with laptop speakers — both sound fine."),
    PageBreak(),
)

# ===== Section 8 — Submission =====

add(
    p("Section 8 — Submission", H1),
    hr(),
    p(
        "Most hackathons want a YouTube/Drive link. If they want a direct upload, the MP4 you exported "
        "is ready. Steps if it's a YouTube link:"
    ),
    num(1, "Sign in to youtube.com → Create → Upload Video."),
    num(2, "Title: 'Talk to Data — NatWest Code for Purpose Theme 1 Submission'."),
    num(3, "Description: 1-line summary, names, GitHub link."),
    num(4, "Visibility: <b>Unlisted</b> (anyone with the link can watch, but it doesn't appear in search)."),
    num(5, "After upload completes, copy the link, open it in <b>incognito</b> to confirm it works without your account."),
    num(6, "Submit the link via the hackathon portal."),
    note(
        "Keep your final MP4 + project ZIP in two places (your laptop + Google Drive) so you can re-upload if anything fails."
    ),
    PageBreak(),
)

# ===== Section 9 — Backup plans =====

add(
    p("Section 9 — Backup Plans (when something goes wrong)", H1),
    hr(),
    p("If the video runs over 5 minutes", H2),
    bullet("Cut the second tech-stack sentence (the one starting 'For optional AI…')."),
    bullet("Cut the second CSV demo example ('North vs South' segment)."),
    bullet("Tighten the outro by removing the line repetition of names."),
    p("If the video runs under 4:20", H2),
    bullet("Add a 10-second 'What's next' slide before the outro: scaling, audit logs, more connectors."),
    bullet("Slow down the demo a touch — let one verified result sit on screen for 3 extra seconds."),
    p("If the audio quality is bad", H2),
    bullet("Re-record only the audio against the existing video (audio replacement). It's quicker than re-shooting."),
    bullet("In Resolve, mute the original audio track, drag the new audio onto A2, sync visually with mouth movement."),
    p("If a demo step glitches mid-recording", H2),
    bullet("Take a screenshot of the same screen later, place it on V2 for those few seconds, voice over it."),
    p("If you both look stiff", H2),
    bullet("Re-record the intro and outro standing up — energy travels through your body to your voice."),
    bullet("Have a friend off-camera making faces; both presenters react to them just before recording starts."),
    PageBreak(),
)

# ===== Section 10 — Engagement tips =====

add(
    p("Section 10 — Tips That Make the Video Engaging", H1),
    hr(),
    bullet("Smile during intro and outro. People mirror what they see."),
    bullet("Use hand gestures within frame — keeps the eye moving without moving the camera."),
    bullet("Vary pitch on key words: 'Trust', 'verified', 'instant', 'first', 'only'."),
    bullet("Look at the camera lens, not the screen, when you're speaking to the audience."),
    bullet("Pause briefly (0.5 s) after a key claim — gives it weight."),
    bullet("React on camera to your co-host: nods, brief 'yeah', light smile."),
    bullet("Cut to demo footage early — judges trust what they can see working."),
    bullet("Keep on-screen captions minimal: 4–6 words max per line."),
    bullet("End with a clear value line, not a thank-you alone — 'Talk to Data — clarity, trust, speed.'"),
    bullet("Don't apologise on camera. Don't say 'this might not work'. Confidence sells."),
    PageBreak(),
)

# ===== Appendix A — Code segments to highlight =====

add(
    p("Appendix A — Exactly Which Code to Show on Screen", H1),
    hr(),
    p(
        "When Friend 1 switches from the demo to the editor, here are the exact files and the exact "
        "lines to highlight. Keep each visible on screen for ~3–4 seconds — long enough to read but "
        "not long enough to read every line."
    ),
    p("A1. Folder tree (open the Cursor sidebar)", H2),
    bullet("Show <b>src/talk_to_data/</b> expanded so all 12 files are visible."),
    bullet("Mention: 'one folder, one entry, one place to look'."),
    p("A2. analytics.py — the change_drivers function", H2),
    bullet("Open <b>src/talk_to_data/analytics.py</b>. Scroll to <b>def change_drivers</b>."),
    bullet("Highlight the line that computes <i>contribution_pct</i> — this is your 'why did revenue change' answer."),
    p("A3. llm_layer.py — the trust contract", H2),
    bullet("Open <b>src/talk_to_data/llm_layer.py</b>. Scroll to <b>CSV_ENRICH_SYSTEM</b>."),
    bullet(
        "Highlight: <i>'Use ONLY facts and numbers from the JSON. No outside knowledge.'</i> — this "
        "is the line you read aloud."
    ),
    p("A4. pgvector_store.py — the schema (optional, only if time permits)", H2),
    bullet("Show <b>_DDL_TABLE</b> — the pdf_chunks table with vector(768) column."),
    bullet("One sentence: 'Same Gemini embedding stored in Postgres for semantic search.'"),
    PageBreak(),
)

# ===== Appendix B — Word counts =====

add(
    p("Appendix B — Word-count budget per block", H1),
    hr(),
    p("Use this if you want to time-trim or expand any block."),
    Spacer(1, 0.2 * cm),
    two_col_table(
        [
            ("Hook intro (0:00–0:15)", "≈ 35 words"),
            ("Problem (0:15–0:45)", "≈ 75 words"),
            ("Solution overview (0:45–1:15)", "≈ 70 words"),
            ("Tech stack (1:15–1:50)", "≈ 80 words"),
            ("Demo + commentary (1:50–3:35)", "≈ 240 words"),
            ("Code peek (3:35–4:10)", "≈ 90 words"),
            ("Why it stands out (4:10–4:40)", "≈ 70 words"),
            ("Outro (4:40–5:00)", "≈ 35 words"),
            ("TOTAL target", "≈ 695–720 words (≈ 4:48 spoken)"),
        ]
    ),
    PageBreak(),
)

# ===== Appendix C — One-page cheat sheet =====

add(
    p("Appendix C — Day-of cheat sheet (print this!)", H1),
    hr(),
    p("BEFORE you press record", H2),
    bullet("DND on, all notifications closed, browser fullscreen."),
    bullet("Streamlit running, sample CSV + sample PDF in Finder."),
    bullet("Cursor tabs ordered: README, app, views, analytics, llm_layer, pgvector_store."),
    bullet("Slides ready: title card + tech stack."),
    bullet("OBS scenes set: 'Both Faces' and 'Main Demo'. Hotkey Cmd+R configured."),
    bullet("Mic peaks at -12 to -6 dB. Lamp on. Water near you."),
    p("DURING recording", H2),
    bullet("Take 1: Slides only — record the slide flips."),
    bullet("Take 2: Demo — Friend 1 narrates clicks (rough audio)."),
    bullet("Take 3: Webcam — full script, both faces, 2 passes."),
    bullet("Take 4 (optional): B-roll — smiles, nods, reactions."),
    p("AFTER recording, in DaVinci", H2),
    bullet("Import 4 takes into bins. Build timeline V1=webcam, V2=screen, V3=PiP, V4=titles, A3=music."),
    bullet("Cut filler. Add cross dissolves at major joins. Add lower thirds for names."),
    bullet("Audio: HP filter, compressor, music ducked to -25 dB with 1s fade-in / 2s fade-out."),
    bullet("Captions: auto-transcribe, fix words, white text + black outline."),
    bullet("Title card 3 sec, end card 5 sec. Watch end-to-end. Length 4:48–4:55."),
    bullet("Deliver: MP4 H.264 1080p, AAC 192k, ~12 Mbps. Filename Talk_to_Data_Submission_Final.mp4."),
    p("FINAL", H2),
    bullet("Watch once with earphones, once on speaker. Re-export if needed."),
    bullet("Upload to YouTube as Unlisted. Test link in incognito. Submit."),
    bullet("Backup the MP4 + project ZIP to Drive."),
    Spacer(1, 0.5 * cm),
    note(
        "You will not get this perfect on the first take. That's normal. The script + this cheat sheet "
        "is what makes the second and third takes look easy. Trust the process — and have fun."
    ),
)


# ---------- Build ----------

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    leftMargin=2 * cm,
    rightMargin=2 * cm,
    topMargin=2 * cm,
    bottomMargin=2 * cm,
    title="Talk to Data — 5-Minute Submission Video Guide",
    author="Naman1821",
)

doc.build(flowables, onFirstPage=on_page, onLaterPages=on_page)
print(f"Wrote {OUT}  ({os.path.getsize(OUT)/1024:.1f} KB, ~{doc.page} pages)")
