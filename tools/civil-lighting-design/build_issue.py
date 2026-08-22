"""
Civil Lighting Design — issue HTML/text generator.

Builds the complete sheet-design email for one issue: north arrow, masthead
+ STA line, a corridor schematic, general notes, sectioned stories as ruled
schedule tables with matchline dividers between them, title block, and
footer.

Why this exists instead of a Buttondown custom_email_template: Buttondown's
canonical template-variable reference (docs.buttondown.com/template-variables,
also mirrored at odds-and-ends/template-variables) lists email.subject,
email.publish_date, email.secondary_id, unsubscribe_url, etc. -- and no
variable representing an issue's body content. Their documented mechanism
for a fully custom design is different: "All HTML is technically valid
Markdown, so if you ever want to just completely override Buttondown's
styles and provide your own email template, you're welcome to do so"
(docs.buttondown.com/advanced-features/css) -- i.e. paste the complete HTML
directly as the issue's body. So this script assembles that complete HTML
locally (date, issue number, sections -- all computed here in Python, not
resolved by Buttondown), and the OUTPUT gets pasted or POSTed as the `body`
field of a Buttondown email. No newsletter-level wrapper template involved.

The one Buttondown-side variable left untouched in the output is
{{ unsubscribe_url }}, which IS documented as usable directly inside email
body content, substituted per-subscriber when Buttondown sends the email.

Why the masthead, STA line, matchline dividers, title block, north arrow,
and corridor schematic are PNGs, not styled HTML text: email clients don't
reliably load custom @font-face fonts, so any font-family set in CSS
silently falls back to a web-safe font. That's acceptable for body copy
and table cells, but it means the elements that are supposed to carry the
"civil engineering plan sheet" identity were never actually rendering in
the drafting-style lettering they were designed with -- see sheet_assets.py
for the full reasoning and the rasterization itself. This script calls
into sheet_assets at build time to (re)generate the per-issue masthead+STA
and title-block images (their content changes every issue), and references
the pre-generated, fixed assets (matchlines, north arrow, corridor
schematic -- generated once via `python sheet_assets.py`).

Why stories render as ruled schedule tables instead of headline+paragraph:
matching the reference DelDOT sheet's typeface and title block wasn't
enough to make this read as a plan sheet, because the dominant visual
content on a real sheet is dense, tabulated schedules (CURB SCHEDULE,
UTILITY TEST HOLE SCHEDULE, etc.) -- not prose in generous whitespace.
Structuring each section as a bordered NO./ITEM/SUMMARY table is a
structurally honest match to that (real content, genuinely tabulated),
not decoration.

What's deliberately NOT replicated: a literal plan-view drawing with real
parcels/utilities/coordinates (we have no such data -- faking it would be
fabricated precision, not homage) and a numeric scale bar (our SCALE field
honestly reads NTS, and a scale bar contradicts NTS on a real drawing --
see sheet_assets.generate_titleblock's docstring). The corridor schematic
and north arrow are included because they don't assert any specific false
fact -- see their docstrings in sheet_assets.py.

Usage: edit ISSUE below (or import build_email_html/build_email_text and
call them from another script with real content), then:
    python build_issue.py
Writes issue-preview.html and issue-preview.txt next to this script, and
regenerates the per-issue masthead/title-block PNGs under
static/images/civil-lighting-design/.
"""

from datetime import date
from pathlib import Path

import sheet_assets

HERE = Path(__file__).parent

HAIRLINE = "#c9d0d8"
INK = "#1a1a2e"
ACCENT_TEXT = "#2A6F9B"
BODY_TEXT = "#4a5568"
MUTED_TEXT = "#718096"
ACCENT = "#4ea3dc"
BODY_FONT_STACK = "'Overpass',Arial,Helvetica,sans-serif"
# Structural/index text (captions, column headers) gets its own stack,
# distinct from reading prose -- the same label/content split the
# rasterized elements draw with Overpass Mono vs. Overpass, just carried
# into live HTML text via the closest web-safe analog (a monospace
# fallback reads more "technical label" than a sans fallback would).
LABEL_FONT_STACK = "'Overpass Mono',ui-monospace,'Courier New',Courier,monospace"

EVARILABS_URL = "https://evarilabs.com"

# Sections whose stories are Photometrics.ai's own writing render in plain
# (roman) type -- like "proposed work" on a real sheet. Everything else is
# treated as reporting on something that already exists elsewhere, and
# gets an italicized source note in the summary cell -- the same
# distinction real plan sheets draw between proposed work (upright) and
# existing conditions (italic).
ORIGINAL_SECTION = "From Photometrics.ai"


def _matchline(section_name, matchline_assets):
    info = matchline_assets[section_name]
    return f"""
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:28px 0 20px;">
          <tr><td align="center">
            <img src="{info['url']}" width="{info['display_w']}" alt="Match line &mdash; {section_name}" style="display:block;width:100%;max-width:{info['display_w']}px;height:auto;margin:0 auto;">
          </td></tr>
          </table>"""


def _section_schedule(section_name, stories):
    """A ruled NO./ITEM/SUMMARY table. Deliberately NOT styled like the
    title block: the title block is the one box on the sheet meant to
    read as heavy/definitive, so schedule tables use a uniform, lighter
    grid weight throughout (same weight outer border as internal
    dividers, no shaded caption bar) and put their caption as plain label
    text sitting above the table -- matching how captions actually sit on
    the reference sheet, and avoiding every section reading as its own
    little title block."""
    rows = []
    last = len(stories) - 1
    for i, story in enumerate(stories):
        summary = story["body"]
        if story.get("source") and section_name != ORIGINAL_SECTION:
            summary += f' <span style="font-style:italic;color:{MUTED_TEXT};">&mdash; {story["source"]}</span>'
        bottom = "" if i == last else f"border-bottom:1px solid {HAIRLINE};"
        rows.append(f"""
          <tr>
            <td valign="top" style="width:32px;padding:10px 8px;{bottom}font-family:{LABEL_FONT_STACK};font-size:12px;color:{MUTED_TEXT};">{i + 1:02d}</td>
            <td valign="top" style="width:160px;padding:10px 8px;{bottom}border-left:1px solid {HAIRLINE};font-family:{BODY_FONT_STACK};font-weight:700;font-size:14px;color:{ACCENT_TEXT};line-height:1.4;">{story['headline']}</td>
            <td valign="top" style="padding:10px 8px;{bottom}border-left:1px solid {HAIRLINE};font-family:{BODY_FONT_STACK};font-size:13px;color:{BODY_TEXT};line-height:1.55;">{summary}</td>
          </tr>""")
    return f"""
          <p style="margin:0 0 6px;font-family:{LABEL_FONT_STACK};font-weight:600;font-size:12px;letter-spacing:1.5px;color:{INK};">{section_name.upper()} SCHEDULE</p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;border:1px solid {INK};">
          <tr>
            <td style="width:32px;padding:6px 8px;border-bottom:1px solid {INK};font-family:{LABEL_FONT_STACK};font-weight:600;font-size:10px;letter-spacing:1px;color:{MUTED_TEXT};">NO.</td>
            <td style="width:160px;padding:6px 8px;border-bottom:1px solid {INK};border-left:1px solid {HAIRLINE};font-family:{LABEL_FONT_STACK};font-weight:600;font-size:10px;letter-spacing:1px;color:{MUTED_TEXT};">ITEM</td>
            <td style="padding:6px 8px;border-bottom:1px solid {INK};border-left:1px solid {HAIRLINE};font-family:{LABEL_FONT_STACK};font-weight:600;font-size:10px;letter-spacing:1px;color:{MUTED_TEXT};">SUMMARY</td>
          </tr>
          {''.join(rows)}
          </table>"""


def _general_notes(intro_html):
    return f"""
          <p style="margin:0 0 6px;font-family:{LABEL_FONT_STACK};font-weight:600;font-size:12px;letter-spacing:1.5px;color:{INK};">GENERAL NOTES</p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;border:1px solid {INK};margin:0 0 28px;">
          <tr>
            <td style="padding:14px 12px;font-family:{BODY_FONT_STACK};font-size:14px;line-height:1.65;color:{BODY_TEXT};">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
                <td valign="top" style="width:22px;font-family:{LABEL_FONT_STACK};font-weight:600;color:{MUTED_TEXT};">1.</td>
                <td valign="top">{intro_html}</td>
              </tr></table>
            </td>
          </tr>
          </table>"""


def build_body_content(intro_html, sections, matchline_assets):
    """sections: list of {"name": str, "stories": [{"headline", "body", "source"?}]}"""
    parts = []
    if intro_html:
        parts.append(_general_notes(intro_html))
    for section in sections:
        parts.append(_matchline(section["name"], matchline_assets))
        parts.append(_section_schedule(section["name"], section["stories"]))
    return "".join(parts)


def build_email_html(issue_number, publish_date, intro_html, sections):
    issue_str = f"{issue_number:02d}"

    masthead = sheet_assets.generate_masthead_sta(issue_number, publish_date)
    titleblock = sheet_assets.generate_titleblock(issue_number, publish_date)
    matchline_assets = sheet_assets.generate_all_matchlines()
    north = sheet_assets.generate_north_arrow()
    corridor = sheet_assets.generate_corridor_schematic()

    body_content = build_body_content(intro_html, sections, matchline_assets)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Civil Lighting Design &mdash; Issue {issue_str}</title>
<style type="text/css">
  body, table, td {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
  body {{ margin: 0; padding: 0; background-color: #f8f9fa; }}
  table {{ border-collapse: collapse; }}
  img {{ border: 0; outline: none; text-decoration: none; }}
  a {{ color: {ACCENT}; }}
</style>
</head>
<body style="margin:0;padding:0;background-color:#f8f9fa;">

<div style="display:none;font-size:1px;color:#f8f9fa;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
  Civil Lighting Design &mdash; Issue {issue_str}
</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f8f9fa;">
<tr>
<td align="center" style="padding:24px 12px;">

<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr>
  <td width="7" valign="middle" align="center"><div style="width:7px;height:2px;line-height:2px;font-size:0;background-color:{INK};">&nbsp;</div></td>
  <td align="center">

{_tick_row()}

    <table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" style="width:640px;max-width:640px;background-color:#ffffff;border:3px solid {INK};">
    <tr><td style="padding:10px;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid {HAIRLINE};">
      <tr><td style="padding:32px 40px 8px;">

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td align="right">
          <img src="{north['url']}" width="{north['display_w']}" alt="North arrow" style="display:block;width:{north['display_w']}px;height:{north['display_h']}px;">
        </td></tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:-8px;">
        <tr><td align="center">
          <img src="{masthead['url']}" width="{masthead['display_w']}" alt="Civil Lighting Design &mdash; STA {issue_str}+00" style="display:block;width:100%;max-width:{masthead['display_w']}px;height:auto;margin:0 auto;">
        </td></tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;">
        <tr><td align="center">
          <img src="{corridor['url']}" width="{corridor['display_w']}" alt="Target Lighting Layer corridor schematic" style="display:block;width:100%;max-width:{corridor['display_w']}px;height:auto;margin:0 auto;">
        </td></tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="height:20px;line-height:20px;font-size:0;">&nbsp;</td></tr></table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td>{body_content}
        </td></tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="height:8px;line-height:8px;font-size:0;">&nbsp;</td></tr></table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td align="center">
          <img src="{titleblock['url']}" width="{titleblock['display_w']}" alt="Title block: Civil Lighting Design, published by EvariLabs. Issue {issue_str}, dated {publish_date.strftime('%m/%d/%y')}, sheet 1 of 1. Drawn AI, checked AI, scale NTS." style="display:block;width:100%;max-width:{titleblock['display_w']}px;height:auto;margin:0 auto;">
        </td></tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">
        <tr><td align="center" style="font-family:{BODY_FONT_STACK};font-size:13px;color:{MUTED_TEXT};">
          <a href="{EVARILABS_URL}" style="color:{MUTED_TEXT};">Published by EvariLabs</a>
          &nbsp;&middot;&nbsp;
          <a href="{{{{ unsubscribe_url }}}}" style="color:{ACCENT};text-decoration:none;">Unsubscribe</a>
        </td></tr>
        </table>

      </td></tr>
      </table>

    </td></tr>
    </table>

{_tick_row()}

  </td>
  <td width="7" valign="middle" align="center"><div style="width:7px;height:2px;line-height:2px;font-size:0;background-color:{INK};">&nbsp;</div></td>
</tr>
</table>

</td>
</tr>
</table>

</body>
</html>
"""


def _tick_row():
    return f"""
    <table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" style="width:640px;max-width:640px;">
    <tr>
      <td width="316" style="font-size:0;line-height:0;">&nbsp;</td>
      <td width="7" height="7" align="center" style="font-size:0;line-height:0;">
        <div style="width:2px;height:7px;line-height:7px;font-size:0;background-color:{INK};margin:0 auto;">&nbsp;</div>
      </td>
      <td width="316" style="font-size:0;line-height:0;">&nbsp;</td>
    </tr>
    </table>"""


def build_email_text(issue_number, publish_date, intro_text, sections):
    issue_str = f"{issue_number:02d}"
    tb_date = publish_date.strftime("%m/%d/%y")

    lines = [
        "CIVIL LIGHTING DESIGN",
        f"STA {issue_str}+00 - {publish_date.strftime('%B %Y').upper()}",
        "",
        "TARGET LIGHTING LAYER -- CORRIDOR SCHEMATIC",
        "",
        "-" * 60,
        "",
    ]
    if intro_text:
        lines += ["GENERAL NOTES", "", f"1. {intro_text}", ""]
    for section in sections:
        lines += [f"MATCH LINE -- {section['name'].upper()}", "", f"{section['name'].upper()} SCHEDULE", ""]
        for i, story in enumerate(section["stories"]):
            lines += [f"{i + 1:02d}. {story['headline'].upper()}", f"    {story['body']}"]
            if story.get("source") and section["name"] != ORIGINAL_SECTION:
                lines += [f"    -- {story['source']}"]
            lines += [""]
    lines += [
        "-" * 60,
        "",
        "Published by EvariLABS",
        f"Issue {issue_str} | Date {tb_date} | Sheet 1 of 1",
        "Drawn: AI | Checked: AI | Scale: NTS",
        "",
        "Unsubscribe: {{ unsubscribe_url }}",
    ]
    return "\n".join(lines)


# Demo content -- lorem ipsum, used as a build self-check. Two stories now
# carry a "source" to demonstrate the existing/proposed (italic/roman)
# distinction described above.
ISSUE = {
    "issue_number": 1,
    "publish_date": date(2026, 8, 19),
    "intro": (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
        "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
        "veniam, quis nostrud exercitation ullamco laboris."
    ),
    "sections": [
        {
            "name": "From Photometrics.ai",
            "stories": [
                {
                    "headline": "Lorem ipsum dolor sit amet consectetur",
                    "body": "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
                },
            ],
        },
        {
            "name": "Around the Industry",
            "stories": [
                {
                    "headline": "Ut enim ad minim veniam quis nostrud",
                    "body": "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
                    "source": "Example Trade Publication",
                },
                {
                    "headline": "Excepteur sint occaecat cupidatat",
                    "body": "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
                },
            ],
        },
        {
            "name": "Standards and Committees",
            "stories": [
                {
                    "headline": "Sed ut perspiciatis unde omnis iste",
                    "body": "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
                    "source": "Example Standards Body",
                },
            ],
        },
    ],
}


def main():
    html = build_email_html(
        ISSUE["issue_number"], ISSUE["publish_date"], ISSUE["intro"], ISSUE["sections"]
    )
    text = build_email_text(
        ISSUE["issue_number"], ISSUE["publish_date"], ISSUE["intro"], ISSUE["sections"]
    )

    html_path = HERE / "issue-preview.html"
    text_path = HERE / "issue-preview.txt"
    html_path.write_text(html, encoding="utf-8")
    text_path.write_text(text, encoding="utf-8")
    print(f"Wrote {html_path}")
    print(f"Wrote {text_path}")


if __name__ == "__main__":
    main()
