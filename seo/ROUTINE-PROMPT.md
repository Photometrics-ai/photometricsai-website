# SEO Routine (bi-weekly, "SEO Morning")

As of 2026-10-02 the routine is a user-level skill: `~/.claude/skills/site-seo-routine/SKILL.md`.
Run it once per site, from inside that site's own repo. Use one Claude Code session per site; they
can run side by side.

| Site | Repo | Browser add-on |
|---|---|---|
| photometrics.ai | `C:\Users\aisaa\Projects\photometricsai-website` | yes: `seo/browser-checks.md` (Glyphex, Ahrefs, Ubersuggest, SERP) |
| evarilux.com | `C:\Users\aisaa\Projects\Evariluxdotcom\NewMigration\evarilux-claude-migration` | no |
| evarilabs.com | `C:\Users\aisaa\Projects\evarilabsdotcom` | no |

Per session:

```
cd "<repo path>"
claude
/site-seo-routine
```

Each repo's `seo/site.yaml` holds that site's domain, GSC/GA4 IDs, page rotation, geo/audit cadence
and quirks. Reports go to that repo's `seo/reports/YYYY-MM-DD.md` and get committed there.

To add a site: follow "Wiring a new site" in the skill, then add a row above and to the calendar event.

Pre-2026-10-02 runs used a single long prompt pasted from this file, covering photometrics.ai and
evarilux.com in one session. See git history for that version.
