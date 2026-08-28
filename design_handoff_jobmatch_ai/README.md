# Handoff: JobMatch AI — desktop application UI

## Overview
JobMatch AI is a **native desktop application** (target: Python 3.11+ / PyQt6) that helps a job seeker
find relevant jobs from their resume. The user drops in a PDF/DOCX resume, the app parses it into an
editable profile, then searches job sources and ranks results with a **match score**. Jobs can be
opened in a detail view (with a dynamically-styled "apply channel" section) and bookmarked to a
**Saved Jobs** list.

This bundle documents 8 mockups covering the full flow:

| ID | Screen |
|----|--------|
| 1a | Resume Upload — empty state |
| 1b | Resume Upload — processing ("Reading your resume…") |
| 1c | Profile Summary — editable, one field in edit mode |
| 1d | Job Search — filter sidebar + results |
| 1e | Results list — card anatomy & states (default / hover / selected+saved / skeleton) |
| 1f | Job Detail — email application channel |
| 1g | Apply section — four channel types (website / email / form / none) |
| 1h | Saved Jobs |

## About the Design Files
`JobMatch AI.dc.html` in this bundle is a **design reference created in HTML** — a prototype showing
intended look, layout and states. It is **not production code to copy**. The task is to **recreate
these designs in PyQt6** (QWidget-based, with a Qt Style Sheet / QSS theme), using the measurements,
colors and typography documented below. Where HTML idioms don't map (flex `gap`, dashed drop zones,
SVG icons), use the Qt equivalents noted in each section.

The HTML mockups are laid out on a zoomable canvas — each window frame is a 1240×780 app window.

## Fidelity
**High fidelity.** Final colors, typography, spacing and states. Recreate pixel-accurately at the
1240×780 reference window size, then let layouts stretch (rules in *Responsive behavior*).

---

## Design Tokens

### Colors
| Token | Hex | Use |
|---|---|---|
| `accent` | `#0F6E6A` | Primary buttons, active nav, progress, selected borders, match ring (good) |
| `accent-hover` | `#0A5350` | Primary button hover/pressed |
| `accent-ink` | `#0B5B58` | Text on accent-tinted surfaces (chips, % labels) |
| `accent-bg` | `#E2EFEE` | Active nav row, skill chips, keyword chips |
| `accent-bg-soft` | `#F7FAFA` | Apply bar (website type), selected list row |
| `accent-border` | `#CFE0DF` | Borders on accent-tinted surfaces |
| `accent-border-strong` | `#B9CDCB` | Hover border on job cards |
| `text` | `#1B2027` | Primary text; also logo-tile fill |
| `text-2` | `#4C545E` | Body copy, secondary buttons label |
| `text-3` | `#6B7481` | Subtitles, meta |
| `text-4` | `#8B939D` | Tertiary meta, status bar |
| `text-5` | `#98A0AA` | Section labels (uppercase) |
| `text-disabled` | `#AAB1BA` | Inactive nav, placeholders, kebab icons |
| `bg-app` | `#FBFBFC` | Content area background |
| `bg-panel` | `#FFFFFF` | Cards, inputs, toolbars |
| `bg-chrome` | `#E9EBEE` | Title bar |
| `bg-sidebar` | `#F5F6F8` | Left nav, filter sidebar, status bar |
| `bg-fill` | `#F2F4F6` | Neutral chips (salary) |
| `bg-skeleton` | `#EFF1F4` / `#F4F6F8` | Skeleton blocks |
| `border` | `#E2E6EA` | Standard 1px dividers/edges |
| `border-input` | `#CFD5DB` | Input, checkbox, secondary-button borders (`#D3D8DE` on buttons) |
| `border-window` | `#CFD4DA` | Window outer border |
| `border-chrome` | `#D3D8DE` | Title bar bottom border |
| `rule` | `#ECEEF1` | Inner card rules, progress track, list-row separators |
| `warn` | `#C07F2C` | Mid match score, "closes in 3 days", "editing" hint |
| `warn-ink` | `#8A6320` | Warn text on tint |
| `warn-bg` | `#FDF6EA` | Warn chip bg |
| `warn-border` | `#F0E0C4` / `#E3CFA4` | Warn chip / dashed low-confidence chip |
| `danger` | `#C0503C` | Expired, "PDF" glyph, missing-requirement ✕ |
| `danger-bg` | `#FDF1EF` |  |
| `danger-border` | `#F3D3CD` |  |
| `ok` | `#3F7A51` | Form-application channel, "Applied" chip |
| `ok-ink` | `#31633F` · `ok-bg` `#F5F9F6` / `#F0F6F1` · `ok-border` `#CFE3D4` / `#D5E6D9` |  |
| `mail` | `#33587F` (icon stroke `#3A5F8A`) · `mail-bg` `#F6F8FB` · `mail-border` `#D3DDE8` | Email channel |
| `status-ok-dot` | `#3F9C58` | "Extraction confidence: high" |

**Company logo tile fills** (initials, white text): Paystack `#1B2027`, Flutterwave `#3A4B6D`,
Kobo360 `#7A5230`, Andela `#5B6A5B`, Moniepoint `#6B4B6B`. Derive per-company from a fixed hash →
palette of these five muted tones.

### Typography
- UI font: **IBM Plex Sans** (400/500/600/700). Numeric/monospace: **IBM Plex Mono** (500/600) for
  match %, salary, filenames, counts. Ship both as bundled TTFs and load with
  `QFontDatabase.addApplicationFont`; fall back to the platform UI font.
- Scale (px, weight):
  - Screen title 21/600, letter-spacing −0.01em (upload hero: 26/600)
  - Job detail title 21/600 · card job title 14.5/600 · list-row title 13.5/600
  - Body 13/400, line-height 1.65 · secondary 12.5/400 (line-height 1.5–1.6)
  - Meta 11.5/400 · micro 11/400 · status bar 10.5/400
  - Section label 10/600, letter-spacing 0.08em, uppercase (sidebar group label 9.5/600, 0.1em)
  - Buttons: primary 13–14/600, secondary 12–12.5/400–600
  - Mono: 11–13/500–600; large salary 15/600

### Spacing / geometry
- Spacing steps used: 3, 5, 7, 9, 11, 14, 16, 20, 22, 26, 30, 40 px.
- Radius: window 7 · card/panel 6–8 · input, small button 4–5 · chip 3 (square) or 14 (pill) ·
  logo tile 5 (46px tile → 6) · avatar/ring circles 50%.
- Borders are always 1px except: selected card left edge 3px, dashed drop zone 2px, focused input 1.5px.
- Shadows: card `0 1px 2px rgba(20,28,38,.05)`; hover card `0 3px 10px rgba(20,28,38,.09)`;
  window `0 8px 24px rgba(20,28,38,.13)`. Focus ring: `0 0 0 3px rgba(15,110,106,.12)` —
  in Qt, emulate with a 1.5px accent border plus a `QGraphicsDropShadowEffect` or simply the border.

---

## Global window shell (all screens)

```
QMainWindow, frameless (Qt.FramelessWindowHint), 1240×780 default, min 1040×680
├── Title bar        height 36, bg #E9EBEE, bottom border 1px #D3D8DE
│    ├── 14×14 accent square (r=3) — app mark            padding-left 12
│    ├── "JobMatch AI"  11.5/600, letter-spacing .02em   gap 10
│    ├── stretch
│    └── window buttons — minimize / maximize / close, 11px glyphs #7A828C, gap 14, padding-right 12
├── (optional) search toolbar — screen 1d only, height 52, bg #FFF, bottom border 1px #E2E6EA
├── Body  (QHBoxLayout, 0 margins)
│    ├── Left nav  width 198 fixed, bg #F5F6F8, right border 1px #E2E6EA, padding 14/10
│    └── Content   bg #FBFBFC
└── Status bar      height 26, bg #F5F6F8, top border 1px #E2E6EA, 10.5px #8B939D, padding-left 12,
                    items separated by "·" with 16px gaps
```

Title bar must be draggable (implement mouse press/move to move the window). Double-click toggles maximize.

### Left nav (workflow stepper)
Four rows: **Resume · Profile · Search · Saved**. Row = 8px/10px padding, radius 5, 12.5px label,
9px gap-column with a 16×16 step marker:
- **future** step: 1px `#CFD5DB` circle, number, label `#AAB1BA`
- **done** step: `#CFE0DF` filled circle, `#0F6E6A` "✓", label `#4C545E`
- **current** step: row bg `#E2EFEE`, label `#0F6E6A`/600, marker filled `#0F6E6A` with white bold number

Group header "WORKFLOW" 9.5/600, 0.1em, `#98A0AA`, padding 4/10/8.
Saved row shows a right-aligned mono count (e.g. `5`).
Nav footer variants: a lock icon + "Runs offline" (11px `#8B939D`, top border) on 1a;
on 1c a white bordered card (radius 6, padding 10) reading `Parsed from / <filename> / Replace resume` (link).

Steps are **gated**: Profile/Search/Saved are only enabled once their prerequisite completed.

---

## Screen 1a — Resume Upload (empty state)

Content area centers a single column (align center, padding 40):
1. 72×72 illustration: a document sheet outline (`#C3CAD2` 1.6px stroke) with three text rules
   (`#D4DAE1`, 2.4px, rounded) and a 32px accent check-badge overlapping bottom-right
   (fill `#E2EFEE`, stroke `#0F6E6A`, check 2.4px `#0F6E6A`). Ship as an SVG asset rendered via
   `QSvgWidget` — do not redraw in QPainter unless needed.
2. Title **"Find jobs that fit your resume"** 26/600, margin 22 top / 8 bottom.
3. Subtitle, 13.5/400 `#6B7481`, max-width 430, centered, line-height 1.55:
   "Drop in your resume and JobMatch reads your skills, titles and experience to score every job it finds."
4. **Drop zone** — 600×216, bg `#FFF`, 2px dashed `#C3CAD2`, radius 8, margin-top 30, contents
   centered with 14px gaps:
   - 30px upload glyph (`#9AA3AD`, 1.7px stroke)
   - "Drag & drop your resume here" 14/400 `#4C545E`
   - divider row: 60px 1px `#E2E6EA` rules either side of "or" (11.5px `#A6ADB6`), 12px gaps
   - **Browse Files…** primary button: bg/border `#0F6E6A`, white 13/600, padding 9/20, radius 5
   - "PDF or DOCX · up to 10 MB" 11px `#98A0AA`
5. Footer line 11.5px `#8B939D`, margin-top 26: `Last used: <mono filename> · reuse` (link, accent).

Status bar: `Ready · No resume loaded`.

**Drop-zone states**
| State | Border | Fill | Notes |
|---|---|---|---|
| idle | 2px dashed `#C3CAD2` | `#FFF` | |
| drag-over | 2px dashed `#0F6E6A` | `#F7FAFA` | glyph + label switch to accent |
| rejected file type | 2px dashed `#C0503C` | `#FDF1EF` | inline msg "Only PDF or DOCX files, please." 12px `#C0503C`, auto-clears after 4s |
| too large (>10 MB) | same as rejected | | msg "That file is over 10 MB." |

Implement with `setAcceptDrops(True)` + `dragEnterEvent/dragLeaveEvent/dropEvent`; Browse opens
`QFileDialog.getOpenFileName(filter="Resumes (*.pdf *.docx)")`.

## Screen 1b — Processing

Same shell; nav stays on step 1. Centered column:
- Title "Reading your resume…" 22/600; sub 13px `#6B7481` "This takes a few seconds. Everything happens on your machine." (margin-top 7)
- Card 600 wide, `#FFF`, 1px `#E2E6EA`, radius 8, padding 22/24, margin-top 28:
  - Row: 34×40 file badge (radius 4, bg `#FDF1EF`, border `#F3D3CD`, mono 9/600 `#C0503C` "PDF" — use `DOC` + blue-grey tint for DOCX), 12px gap; filename 13/600; sub "248 KB · 2 pages" 11.5px `#8B939D`; right-aligned mono 12/600 accent percentage.
  - Progress bar: height 5, radius 3, track `#ECEEF1`, fill `#0F6E6A`, margin-top 16.
  - Step list (margin-top 20, 11px gaps), 12.5px:
    - done → 15px accent check icon, text `#4C545E`
    - active → 15px spinner ring (2px `#CFE0DF` with `#0F6E6A` top arc, rotate 360° / 900ms linear), text `#1B2027`/600
    - pending → 15px 1.5px dashed `#CFD5DB` circle, text `#AAB1BA`
    - Copy: "Extracted text from 2 pages" · "Found sections: Experience, Skills, Education" ·
      "Identifying skills and seniority…" · "Building search keywords"
  - Footer: top rule `#ECEEF1` (padding-top 16), right-aligned secondary **Cancel** button
    (1px `#D3D8DE`, `#FFF`, 12.5px `#4C545E`, padding 7/15, radius 5).

Status bar: `Parsing… · <filename>`.

Parsing runs on a `QThread`/`QRunnable` worker emitting `progress(int, str)`; Cancel requests
interruption and returns to 1a. On failure show the card in an error state: progress fill `#C0503C`,
message "We couldn't read that file." + buttons *Try another file* / *Enter details manually*.

## Screen 1c — Profile Summary

Content padding 30/40.
- Header row: title "Here's what we read" 21/600 + sub 12.5px `#6B7481` "Fix anything that looks off — matching quality depends on it."; right side a confidence pill: `#FFF`, 1px `#E2E6EA`, radius 5, padding 6/11, 11.5px, 7px green dot `#3F9C58` + "Extraction confidence: high" (low → `#C07F2C` dot, "review the fields below").
- **Profile card**: `#FFF`, 1px `#E2E6EA`, radius 8, padding 24/26, margin-top 20.
  - Identity row: 52×52 initials tile (radius 6, `#E2EFEE`, `#0F6E6A`, 18/600) · name 19/600 ·
    "Senior Data Analyst · Lagos, NG" 13px `#6B7481` · right secondary button **Edit all** with 13px pencil icon.
  - 1px `#ECEEF1` rule, 22px margins.
  - 2-column grid, gaps 20/34, four fields — label 10/600 0.08em `#98A0AA`, value 14px, 7px below:
    `CURRENT TITLE` "Senior Data Analyst" · `TARGET TITLE` (edit mode) · `YEARS OF EXPERIENCE`
    "6 years" + `(2019 – present)` 12px `#98A0AA` · `LOCATION` "Lagos, Nigeria · open to remote".
  - **Field edit mode** (shown on Target title): label gains `· editing` in `#C07F2C` 500;
    a `QLineEdit` 1.5px `#0F6E6A`, radius 5, padding 6/9, 13.5px, focus glow, plus an inline accent
    **Save** button (12px, padding 0/13, radius 5). Esc cancels, Enter/Save commits.
  - 1px rule.
  - **KEY SKILLS**: label + "12 detected · click a chip to remove" 11.5px `#AAB1BA`; chips (margin-top 12, wrap, 8px gaps):
    - normal chip: `#E2EFEE` bg, 1px `#CFE0DF`, `#0B5B58`, radius 14, padding 5/12, 12.5px, trailing ✕ `#7FA8A6`
    - low-confidence chip: `#FDF6EA`, 1px **dashed** `#E3CFA4`, `#8A6320`, trailing "low confidence" 10.5px `#B08C4A`
    - add chip: 1px dashed `#CFD5DB`, `#8B939D`, "+ Add skill" → turns into an inline line edit with completer
- Footer row (margin-top 22, 14px gap): **Search Jobs** primary — 14/600, padding 11/26, radius 5,
  with a 15px magnifier icon; then helper text 12px `#8B939D` "Will search 6 boards using 9 keywords from your profile."

Status bar: `Profile ready · Unsaved edit in "Target title"` (mirror real dirty state).

## Screen 1d — Job Search / Filters

**Search toolbar** (height 52, bg `#FFF`, bottom border, padding 0/16, 12px gaps):
- Token field: flex 1, max-width 640, 1px `#CFD5DB`, radius 5, padding 8/11, 15px magnifier `#8B939D`,
  then keyword tokens (`#E2EFEE` bg, `#0B5B58`, radius 3, padding 2/7, 12px, 6px gaps) pre-filled from
  the resume (`analytics engineer`, `dbt`, `SQL`), then a ghost "add keyword…" 13px `#AAB1BA`.
  Backspace on empty input removes the last token; Enter commits a token.
- Primary **Search** button (12.5/600, padding 8/18).
- Right: 11.5px `#8B939D` `Suggested from resume · edit profile` (link → 1c).

**Filter sidebar** — width 252 fixed, bg `#F5F6F8`, right border, padding 16/16/0, scrollable:
- Header row: "Filters" 12.5/600 + "Reset" 11px `#8B939D` (link).
- Group label 10/600 0.08em `#98A0AA`, 16px above / 8–12px below each control; groups separated by a
  1px `#E2E6EA` rule with 16px margins.
- `LOCATION`: text input (1px `#CFD5DB`, `#FFF`, radius 4, padding 7/9, 12.5px) with city completer;
  below, a **Remote only** row: 12.5px `#4C545E` label + toggle 34×19, radius 10, on = `#0F6E6A`
  with a 15px white knob at x=17 (off = `#CFD5DB`, knob x=2), 120ms slide.
- `SALARY RANGE (ANNUAL)`: dual-handle slider — 4px track `#DFE3E8`, accent selected span,
  14px white handles with 2px accent border; below, mono 11.5px `#4C545E` min/max labels (`$45k` / `$130k`).
- `DATE POSTED`: segmented control, 1px `#CFD5DB`, radius 4, `#FFF`, four equal cells 11.5px
  (`24h · 7d · 30d · Any`); selected cell bg `#0F6E6A`, white 600.
- `JOB TYPE`: checkbox column, 9px gaps — checked box 14×14 radius 3 `#0F6E6A` with white 9px ✓ and
  label `#1B2027`; unchecked 1px `#CFD5DB` on `#FFF`, label `#6B7481`. Items: Full-time ✓, Contract ✓,
  Internship, Part-time.
- `EXPERIENCE LEVEL`: multi-select pills, 7px gaps — selected: `#E2EFEE` bg, 1px `#0F6E6A`, `#0B5B58` 600;
  unselected: `#FFF`, 1px `#CFD5DB`, `#6B7481`. Items: Junior, Mid ✓, Senior ✓, Lead.

Filter changes debounce 300ms then re-query; the results header count updates.

**Results header** (height 42, bottom border, padding 0/20): `142 jobs` 12.5/600 +
`· 3 filters applied` `#8B939D`; right: "Sort by" 12px `#6B7481` and a combo box (1px `#CFD5DB`,
`#FFF`, radius 4, padding 5/10, 12px) — options **Match score · Date posted · Salary**.

**Results area**: vertical scroll, padding 14/20, 11px gaps between cards (see 1e for card spec).
The last visible card renders at 55% opacity as a scroll affordance.

Status bar: `142 results · last refreshed 09:41 · 6 sources`.

**Empty / error states** (not drawn — implement to match): empty → centered 13px `#6B7481`
"No jobs matched these filters." + *Clear filters* button; source failure → an inline strip above the
list, bg `#FDF6EA`, 1px `#F0E0C4`, 12px `#8A6320`: "2 of 6 sources didn't respond. Retry".

## Screen 1e — Job card anatomy

Card: `#FFF`, 1px `#E2E6EA`, radius 6, padding 15/17, `QHBoxLayout` 14px gap, items top-aligned.
- 40×40 logo tile, radius 5, company color, white initials 14/600 (use a real logo pixmap when the
  source provides one; initials are the fallback).
- Center column: title 14.5/600 → meta 12.5px `#6B7481` (`Company · Location (Mode) · Type`, 4px above)
  → tag row (9px above, 7px gaps): salary chip mono 11/500 on `#F2F4F6` radius 3 padding 3/7 `#4C545E`
  (absent salary → same chip, text `Salary not listed`, color `#8B939D`); then up to 3 matched-skill
  chips 11px `#E2EFEE`/`#0B5B58`; then an overflow chip `+4` on `#F2F4F6` `#6B7481`.
- Right column (align right, 10px gap): **match ring** then posted date 11px `#8B939D`.

**Match ring**: 46×46 SVG/QPainter — track circle r=19 stroke 4.5 `#E6EAEE`; progress arc same radius,
round cap, rotated −90°, `stroke-dasharray 119.4`, offset `119.4 × (1 − score)`; centered mono 12/600.
Color by score: **≥75 → `#0F6E6A` / `#0B5B58` text**, **50–74 → `#C07F2C` / `#8A6320`**,
**<50 → `#8B939D`**. Detail-view ring is 60×60, r=25, stroke 6, label 14/600.

| State | Spec |
|---|---|
| default | as above |
| hover | border `#B9CDCB`, shadow `0 3px 10px rgba(20,28,38,.09)`; reveals an action row (11px above, 8px gaps): outlined accent **View details** (1px `#0F6E6A`, `#0F6E6A`, 12/600, padding 5/12, radius 4) and **Save** (1px `#D3D8DE`, `#4C545E`, 12px, bookmark outline icon) |
| selected | bg `#F7FAFA`, 1px `#0F6E6A` + 3px accent left edge |
| saved | filled accent bookmark icon (13px) inline after the title, 8px gap |
| viewed | meta tail reads `· viewed yesterday`; title stays full-strength |
| loading | skeleton: 40×40 `#EFF1F4` tile, 180×11 and 260×9 `#EFF1F4`/`#F4F6F8` bars (radius 3, 8px gap), 46px `#EFF1F4` circle; optional 1.2s shimmer |

Cards are keyboard-navigable (↑/↓ move selection, Enter opens detail, `S` toggles save).

## Screen 1f — Job Detail

Body splits into a **results rail** (left) and the detail pane.

**Results rail** — width 300, bg `#F5F6F8`, right border:
- Back row: padding 11/14, bottom border, 12px `#6B7481`, 13px chevron-left icon, "Back to 142 results".
- Compact cards (padding 8, 6px gaps): `#FFF`, radius 5, padding 11/12, 11px gap — 30×30 logo tile
  (radius 4, 11/600), title 12.5/600, sub 11px `#8B939D`, right mono 11/600 score.
  Current item gets a 1px `#0F6E6A` border.

**Detail header** (padding 22/30/18, bottom border 1px `#E2E6EA`, bg `#FFF`):
- 46×46 logo tile (radius 6, 16/600) · title 21/600 (−0.01em) · meta 13px `#6B7481`
  "Company · Location (Mode) · Type · Posted 4 days ago" · right secondary **Save Job** button with
  bookmark icon (filled + label "Saved" when active).
- **Apply bar** directly beneath (margin-top 16) — see 1g for all four variants. Bar geometry is
  constant: radius 6, padding 14/16, 16px gaps, 19px leading icon, label 10/600 0.08em, value line
  mono 12.5–13/500 (5px below), optional secondary button, then the primary action button
  (13/600, padding 9/17–18, radius 5).

**Detail content** (`QHBoxLayout`): main column padding 22/30, scrollable; right meta column width 268,
left border, bg `#FBFBFC`, padding 22/20.

Main column blocks (section heading 13.5/600, 22px above):
- *About the role* — 13px `#4C545E`, line-height 1.65, 8px below heading.
- *Requirements* — rows 10px gap, 12.5px `#4C545E`, each with a 14px leading icon 2px above baseline:
  accent check when the resume satisfies it; `#C0503C` ✕ + text `#8B939D` and a
  "(not on your resume)" suffix when it doesn't.
- *Benefits* — one 12.5px line, 1.65 line-height.

Right meta column:
- `MATCH BREAKDOWN` → 60px ring + two-line 11.5px `#6B7481` verdict ("Strong on skills, / light on tooling").
  Then four bars (12px gaps): label left 11.5px `#4C545E`, mono value right, 4px track `#ECEEF1`
  radius 2, fill accent (`#C07F2C` when the factor is weak): Skills `9/12` 75% · Seniority `Match` 92% ·
  Location `Remote ok` 100% · Tooling `2/5` 40%.
- rule · `COMPANY` → 12.5px `#4C545E` 1.6 line-height (name / industry · size / founded · offices) + a
  12px accent external link `flutterwave.com ↗`.
- rule · `SALARY` → mono 15/600 `$70k – $88k` + 11.5px `#8B939D` "Listed by employer · annual"
  (if missing: `—` and "Not listed by employer").

Status bar: `Job 2 of 142 · Source: company careers page`.

## Screen 1g — Apply channel variants

Choose the variant from the parsed apply target. **The primary button always names the real action.**

| Type | Trigger | Container | Icon | Label | Value | Buttons |
|---|---|---|---|---|---|---|
| A · external posting | `http(s)` URL, not a known form host | bg `#F7FAFA`, border `#CFE0DF` | globe, `#0F6E6A` | `APPLY ON COMPANY SITE` `#0B5B58` | mono URL `#4C545E` | primary accent **Visit Website** + external-link icon → `QDesktopServices.openUrl` |
| B · email | `mailto:` or a bare address | bg `#F6F8FB`, border `#D3DDE8` | envelope, `#3A5F8A` | `APPLY BY EMAIL` `#33587F` | mono address | secondary **Copy** (clipboard, toast "Address copied") + primary `#33587F` **Send Email** with envelope icon → `mailto:` with prefilled subject `Application — <Job title>` |
| C · form link | host in `forms.gle`, `docs.google.com/forms`, `typeform.com`, `airtable.com/shr…` | bg `#F5F9F6`, border `#CFE3D4` | form/list sheet, `#3F7A51` | `APPLICATION FORM` `#31633F` | mono short link | primary `#3F7A51` **Open Application Form** + external-link icon |
| D · none found | no apply target parsed | bg `#FAFAFA`, **1px dashed** `#D3D8DE` | info circle, `#98A0AA` | `NO APPLY LINK DETECTED` `#8B939D` | 12.5px `#6B7481` "Open the original listing to find how to apply." | secondary **Open source listing** |

Explanatory line above the set in the mock (keep as tooltip/help copy): "The apply bar restyles itself
from the link JobMatch found."

## Screen 1h — Saved Jobs

Header (padding 24/30/16, bottom border): title "Saved jobs" 21/600 + sub 12.5px `#6B7481`
"5 saved · 2 with deadlines this week"; right: a sort combo ("Sort: date saved", options *date saved ·
match score · deadline*) and an **Export CSV** button (both 1px `#CFD5DB`, `#FFF`, radius 4, padding 6/11, 12px).

**Rows** (not cards) — padding 13/4, bottom border 1px `#ECEEF1`, 14px gaps, vertically centered:
`14px filled accent bookmark` · `34×34 logo tile (radius 5, 12/600)` · title 13.5/600 + sub 11.5px
`#8B939D` (`Company · Location · Salary`) · **status chip** · mono 11.5/600 score (width 36, right) ·
saved-age 11.5px `#8B939D` (width 80, right) · 15px vertical-kebab `#AAB1BA`.

Status chips: `Closes in 3 days` warn palette · `Applied 12 Aug` ok palette · plain 11.5px `#8B939D`
text for channel notes ("Form application", "Email application") · `Expired` danger palette, and the
whole row drops to 60% opacity with a line-through title.

Kebab menu: *Open detail · Mark as applied · Copy apply link · Remove from saved*.
Footer note, margin-top 18, centered 12px `#98A0AA`: "Saved jobs are re-checked each time you open the app."
Empty state: centered 13px `#6B7481` "Nothing saved yet." + "Bookmark a job from the results list."

Status bar: `5 saved · 1 expired listing`.

---

## Interactions & Behavior
- **Navigation**: 1a → (parse) 1b → 1c → (Search Jobs) 1d → (click card) 1f → back to 1d.
  Saved (1h) is reachable any time once a job is saved. Use a `QStackedWidget` for the four workflow
  pages; the detail view is a page swap of the search page's content (rail keeps the result list).
- **Save/bookmark** is optimistic and instant; toggling anywhere updates every view and the nav count.
- **Transitions**: keep them minimal and native — no page slides. Only: toggle knob 120ms ease,
  hover color/border 90ms, spinner 900ms linear loop, skeleton shimmer 1.2s.
- **Loading**: search shows 4 skeleton cards; detail pane shows skeleton header + 6 text bars.
- **Errors**: parse failure and source failure per screens 1b/1d above; network loss → status bar
  reads `Offline — showing cached results` in `#C07F2C`.
- **Validation**: resume must be `.pdf`/`.docx` ≤10 MB; profile fields non-empty; years of experience
  0–60; salary min ≤ max.
- **Keyboard**: `Ctrl+O` open resume, `Ctrl+F` focus search, `Ctrl+S` save current job,
  `Ctrl+2/3/4` jump to Profile/Search/Saved, `Esc` closes detail, `↑/↓/Enter` in the list.
- **Responsive**: window min 1040×680. Left nav and filter sidebar are fixed width; the results and
  detail columns absorb extra width. Below 1120px content width, the detail meta column (268px)
  collapses under the main column. Job cards never exceed 900px; center them beyond that.

## State Management
Single app-level store (e.g. a `QObject` with signals, or a dataclass store + `pyqtSignal`):
```
resume_file: Path | None
parse_state: 'idle' | 'parsing' | 'done' | 'error'
parse_progress: int, parse_step: str
profile: {name, current_title, target_title, years, location, remote_ok, skills[{name, confidence}]}
profile_dirty_fields: set[str]
editing_field: str | None
query: {keywords[], location, remote_only, salary_min, salary_max, posted_within, job_types[], levels[]}
results: Job[]          # Job: id, title, company, logo, location, mode, type, salary_min/max,
                        # score, factors{skills, seniority, location, tooling}, posted_at,
                        # apply{type: website|email|form|none, value}, description, requirements[], benefits, source
results_state: 'idle' | 'loading' | 'loaded' | 'error'
sort_by, selected_job_id, viewed_ids: set, saved: SavedJob[]  # + saved_at, applied_at, deadline, expired
```
Parsing and searching run off the GUI thread (`QThreadPool` + worker signals). Saved jobs, the last
profile and the last query persist to a local SQLite file (or `QSettings` for the query); saved
listings are re-validated on launch, flipping stale ones to `expired`.

## Assets
- **Fonts**: IBM Plex Sans (400/500/600/700), IBM Plex Mono (500/600) — Open Font License; bundle TTFs.
- **Icons**: 12–30px line icons, 1.7–2.4px stroke, round caps, drawn inline in the mock: upload arrow,
  magnifier, pencil, bookmark (outline + filled), chevron-left, envelope, globe, form sheet, external
  link, info circle, check, ✕, vertical kebab, lock. Reproduce as a small bundled SVG set
  (e.g. Lucide/Feather, which these match) and render via `QIcon`/`QSvgRenderer` with the color
  passed in per state.
- **Upload illustration**: 72×72 SVG, described in 1a — export from the mock.
- **Company logos**: initials tiles are the design's fallback; there are no image assets in this bundle.
- All sample content (Amara Okafor, Paystack/Flutterwave/Kobo360/Andela/Moniepoint, salaries, scores)
  is **placeholder copy** — do not ship it.

## Files
- `JobMatch AI.dc.html` — all 8 mockups (option ids `1a`–`1h` in the markup; open in a browser).
- `README.md` — this document.
