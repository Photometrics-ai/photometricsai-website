"""
Civil Lighting Design — issue HTML/text generator.

Builds the complete sheet-design email for one issue: masthead, STA line,
an optional intro, sectioned stories with matchline dividers, title block,
and footer.

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

Usage: edit ISSUE below (or import build_email_html/build_email_text and
call them from another script with real content), then:
    python build_issue.py
Writes issue-preview.html and issue-preview.txt next to this script, using
the same Lorem Ipsum content as cld-email-mockup-v3.png as a self-check
that this script reproduces the approved mockup.
"""

from datetime import date
from pathlib import Path

HERE = Path(__file__).parent

HAIRLINE = "#c9d0d8"
INK = "#1a1a2e"
ACCENT_TEXT = "#2A6F9B"
BODY_TEXT = "#4a5568"
MUTED_TEXT = "#718096"
ACCENT = "#4ea3dc"

MASTHEAD_URL = "https://photometrics.ai/images/civil-lighting-design/masthead.png"
EVARILABS_URL = "https://evarilabs.com"


def _matchline(section_name):
    return f"""
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:32px 0 8px;">
          <tr><td style="border-top:1px dashed {HAIRLINE};font-size:0;line-height:0;">&nbsp;</td></tr>
          </table>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px;">
          <tr><td align="center" style="font-family:'Courier New',Courier,monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{MUTED_TEXT};">
            MATCH LINE &mdash; {section_name.upper()}
          </td></tr>
          </table>"""


def _story(headline, body_html):
    return f"""
          <h2 style="font-family:'Work Sans',Arial,Helvetica,sans-serif;font-weight:700;font-size:18px;line-height:1.4;color:{ACCENT_TEXT};margin:0 0 8px;">{headline}</h2>
          <p style="font-family:'Work Sans',Arial,Helvetica,sans-serif;font-size:16px;line-height:1.7;color:{BODY_TEXT};margin:0 0 24px;">{body_html}</p>"""


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


def _side_tick_cell():
    return f"""<div style="width:7px;height:2px;line-height:2px;font-size:0;background-color:{INK};">&nbsp;</div>"""


def build_body_content(intro_html, sections):
    """sections: list of {"name": str, "stories": [{"headline": str, "body": str}]}"""
    parts = []
    if intro_html:
        parts.append(
            f'<p style="font-family:\'Work Sans\',Arial,Helvetica,sans-serif;font-size:16px;'
            f'line-height:1.7;color:{BODY_TEXT};margin:0 0 24px;">{intro_html}</p>'
        )
    for section in sections:
        parts.append(_matchline(section["name"]))
        for story in section["stories"]:
            parts.append(_story(story["headline"], story["body"]))
    return "".join(parts)


def build_email_html(issue_number, publish_date, intro_html, sections):
    issue_str = f"{issue_number:02d}"
    sta_date = publish_date.strftime("%B %Y").upper()
    tb_date = publish_date.strftime("%m/%d/%y")
    body_content = build_body_content(intro_html, sections)

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
  <td width="7" valign="middle" align="center">{_side_tick_cell()}</td>
  <td align="center">

{_tick_row()}

    <table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" style="width:640px;max-width:640px;background-color:#ffffff;border:3px solid {INK};">
    <tr><td style="padding:10px;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid {HAIRLINE};">
      <tr><td style="padding:40px 40px 8px;">

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td align="center">
          <img src="{MASTHEAD_URL}" width="480" alt="Civil Lighting Design" style="display:block;width:100%;max-width:480px;height:auto;margin:0 auto;">
        </td></tr>
        <tr><td align="center" style="padding-top:14px;">
          <span style="font-family:'Courier New',Courier,monospace;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:{ACCENT_TEXT};">
            STA {issue_str}+00 &middot; {sta_date}
          </span>
        </td></tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="height:32px;line-height:32px;font-size:0;">&nbsp;</td></tr></table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td>{body_content}
        </td></tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="height:16px;line-height:16px;font-size:0;">&nbsp;</td></tr></table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid {HAIRLINE};">
        <tr>
          <td width="34%" valign="top" style="padding:16px 12px;font-family:'Courier New',Courier,monospace;font-size:12px;letter-spacing:1px;text-transform:uppercase;color:{BODY_TEXT};line-height:1.9;">
            <div style="font-weight:bold;color:{INK};font-size:13px;">CIVIL LIGHTING DESIGN</div>
            <div><a href="{EVARILABS_URL}" style="color:{BODY_TEXT};text-decoration:none;">PUBLISHED BY EVARILABS</a></div>
          </td>
          <td width="33%" valign="top" style="padding:16px 12px 16px;border-left:1px solid {HAIRLINE};font-family:'Courier New',Courier,monospace;font-size:12px;letter-spacing:1px;text-transform:uppercase;color:{BODY_TEXT};">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td style="padding:4px 0;">ISSUE</td><td align="right" style="padding:4px 0;font-weight:bold;color:{INK};">{issue_str}</td></tr>
            <tr><td style="padding:4px 0;border-top:1px solid {HAIRLINE};">DATE</td><td align="right" style="padding:4px 0;border-top:1px solid {HAIRLINE};font-weight:bold;color:{INK};">{tb_date}</td></tr>
            <tr><td style="padding:4px 0;border-top:1px solid {HAIRLINE};">SHEET</td><td align="right" style="padding:4px 0;border-top:1px solid {HAIRLINE};font-weight:bold;color:{INK};">1 OF 1</td></tr>
            </table>
          </td>
          <td width="33%" valign="top" style="padding:16px 12px;border-left:1px solid {HAIRLINE};font-family:'Courier New',Courier,monospace;font-size:12px;letter-spacing:1px;text-transform:uppercase;color:{BODY_TEXT};">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td style="padding:4px 0;">DRAWN</td><td align="right" style="padding:4px 0;font-weight:bold;color:{INK};">AI</td></tr>
            <tr><td style="padding:4px 0;border-top:1px solid {HAIRLINE};">CHECKED</td><td align="right" style="padding:4px 0;border-top:1px solid {HAIRLINE};font-weight:bold;color:{INK};">AI</td></tr>
            <tr><td style="padding:4px 0;border-top:1px solid {HAIRLINE};">SCALE</td><td align="right" style="padding:4px 0;border-top:1px solid {HAIRLINE};font-weight:bold;color:{INK};">NTS</td></tr>
            </table>
          </td>
        </tr>
        </table>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:24px;">
        <tr><td align="center" style="font-family:'Work Sans',Arial,Helvetica,sans-serif;font-size:13px;">
          <a href="{{{{ unsubscribe_url }}}}" style="color:{ACCENT};text-decoration:none;">Unsubscribe</a>
        </td></tr>
        </table>

      </td></tr>
      </table>

    </td></tr>
    </table>

{_tick_row()}

  </td>
  <td width="7" valign="middle" align="center">{_side_tick_cell()}</td>
</tr>
</table>

</td>
</tr>
</table>

</body>
</html>
"""


def build_email_text(issue_number, publish_date, intro_text, sections):
    issue_str = f"{issue_number:02d}"
    tb_date = publish_date.strftime("%m/%d/%y")

    lines = [
        "CIVIL LIGHTING DESIGN",
        f"STA {issue_str}+00 - {publish_date.strftime('%B %Y').upper()}",
        "",
        "-" * 60,
        "",
    ]
    if intro_text:
        lines += [intro_text, ""]
    for section in sections:
        lines += [f"MATCH LINE -- {section['name'].upper()}", ""]
        for story in section["stories"]:
            lines += [story["headline"].upper(), story["body"], ""]
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


# Demo content — matches cld-email-mockup-v3.png exactly, as a self-check
# that this script reproduces the approved mockup.
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
