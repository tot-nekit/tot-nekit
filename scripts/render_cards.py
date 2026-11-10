"""Render self-contained, animated SVGs and GitHub-compatible Markdown."""
import base64
import calendar
import json
import os
import textwrap
from collections import defaultdict
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = os.environ.get("STATIC") == "1"
OUT = Path(os.environ.get("CARD_OUTPUT", ROOT / "cards"))
OUT.mkdir(parents=True, exist_ok=True)
CONFIG = json.loads((ROOT / "profile.json").read_text())
DATA = json.loads((ROOT / "data/github.json").read_text())
PAPER, INK, MUTED, BLUE, LINE = "#f7f5ef", "#282722", "#706e65", "#2455ed", "#dfddd4"
FONT = base64.b64encode((ROOT / "fonts/InstrumentSerif-Regular.ttf").read_bytes()).decode()


def text(x, y, value, size=14, color=INK, klass="", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" class="{klass}" {extra}>{escape(str(value))}</text>'


def svg(name, width, height, content, title, delay=0):
    animation = "" if STATIC else f"""
      .enter {{animation:enter .85s cubic-bezier(.2,.8,.2,1) {delay}s backwards}}
      .grow {{transform-box:fill-box;transform-origin:center bottom;animation:grow .9s ease-out var(--d,0s) backwards}}
      .cell {{animation:appear .55s ease var(--d,0s) backwards}}
      .orbit {{transform-origin:710px 160px;animation:spin 38s linear infinite}}
      .pulse {{animation:pulse 3s ease-in-out infinite}}
      @keyframes enter {{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:translateY(0)}}}}
      @keyframes grow {{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
      @keyframes appear {{from{{opacity:0}}to{{opacity:1}}}}
      @keyframes spin {{to{{transform:rotate(360deg)}}}}
      @keyframes pulse {{50%{{opacity:.35}}}}
      @media(prefers-reduced-motion:reduce) {{*{{animation:none!important;transition:none!important}}}}
    """
    style = f"""@font-face{{font-family:Instrument;src:url(data:font/ttf;base64,{FONT}) format('truetype')}}
      text{{font-family:Arial,Helvetica,sans-serif}} .serif{{font-family:Instrument,Georgia,serif}}
      .mono{{font-family:ui-monospace,'Courier New',monospace;letter-spacing:1.5px}} {animation}"""
    value = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title><style>{style}</style>
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="14" fill="{PAPER}" stroke="{LINE}"/>{content}</svg>'''
    (OUT / f"{name}.svg").write_text(value)


def days():
    return [d for w in DATA["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]


def hero():
    parts = [text(36, 38, f'PERSONAL WORKSPACE / @{CONFIG["username"]}', 11, MUTED, "mono")]
    parts += ['<g class="enter">', text(34, 121, CONFIG["first_name"], 88, INK, "serif"),
              text(34, 208, CONFIG["last_name"] + ".", 88, BLUE, "serif"), '</g>']
    parts += [text(38, 251, CONFIG["tagline"], 18), text(38, 281, CONFIG["intro"], 14, MUTED)]
    parts += [f'<circle cx="710" cy="160" r="103" fill="none" stroke="{LINE}"/>',
              f'<circle cx="710" cy="160" r="74" fill="none" stroke="{LINE}"/>',
              f'<path d="M596 160h228M710 46v228" stroke="{LINE}"/>',
              '<g class="orbit">', f'<ellipse cx="710" cy="160" rx="100" ry="37" fill="none" stroke="{BLUE}" stroke-width="1.5" transform="rotate(-35 710 160)"/>',
              f'<circle cx="792" cy="112" r="7" fill="{BLUE}"/>', '</g>',
              text(710, 179, 'n.', 66, BLUE, 'serif', 'text-anchor="middle"'),
              text(710, 300, 'MAKE IT USEFUL.', 10, MUTED, 'mono', 'text-anchor="middle"')]
    parts += [f'<path d="M36 320h808" stroke="{LINE}"/>', text(38, 347, 'PYTHON  /  JAVASCRIPT  /  TYPESCRIPT', 11, MUTED, 'mono'), text(842, 347, 'CODE → PRODUCT', 11, BLUE, 'mono', 'text-anchor="end"')]
    svg('hero', 880, 370, ''.join(parts), f'{CONFIG["first_name"]} {CONFIG["last_name"]} — {CONFIG["tagline"]}')


def heatmap():
    weeks = DATA['contributionsCollection']['contributionCalendar']['weeks']
    counts = [d['contributionCount'] for d in days()]
    peak = max(counts, default=0)
    palette = ['#e5e7ed', '#bbcaff', '#83a1fb', '#4f78f3', BLUE]
    parts = [text(30, 36, 'A YEAR IN CODE', 11, MUTED, 'mono'), text(850, 36, 'PUBLIC CONTRIBUTIONS', 10, MUTED, 'mono', 'text-anchor="end"')]
    for col, week in enumerate(weeks):
        for d in week['contributionDays']:
            day = date.fromisoformat(d['date'])
            row = (day.weekday() + 1) % 7
            count = d['contributionCount']
            level = 0 if not count else min(4, 1 + int(3 * count / max(peak, 1)))
            parts.append(f'<rect class="cell" x="{30+col*15.5}" y="{58+row*16}" width="12" height="12" rx="3" fill="{palette[level]}" style="--d:{.2+col*.014:.3f}s"><title>{d["date"]}: {count} contributions</title></rect>')
    parts += [text(30, 194, f'{sum(counts):,} contributions in the displayed period', 13, MUTED), text(690, 194, 'LESS', 9, MUTED, 'mono')]
    for i, color in enumerate(palette):
        parts.append(f'<rect x="{727+i*17}" y="183" width="12" height="12" rx="3" fill="{color}"/>')
    parts.append(text(846, 194, 'MORE', 9, MUTED, 'mono', 'text-anchor="end"'))
    svg('heatmap', 880, 218, ''.join(parts), 'Blue contribution calendar; ' + str(sum(counts)) + ' contributions', .15)


def activity():
    all_days = days()
    today = date.fromisoformat(DATA['updated'])
    # Twelve months, including the current month; partial first month is omitted.
    month_keys = []
    for n in range(11, -1, -1):
        month_index = today.year*12+today.month-1-n
        month_keys.append((month_index//12, month_index%12+1))
    totals = defaultdict(int)
    by_date = {}
    best = current = 0
    for d in all_days:
        day = date.fromisoformat(d['date'])
        totals[day.year, day.month] += d['contributionCount']
        by_date[day] = d['contributionCount']
        current = current+1 if d['contributionCount'] else 0
        best = max(best, current)
    cursor = today if by_date.get(today) else today-timedelta(days=1)
    streak = 0
    while by_date.get(cursor, 0):
        streak += 1
        cursor -= timedelta(days=1)
    active = sum(d['contributionCount'] > 0 for d in all_days)
    busiest = max((d['contributionCount'] for d in all_days), default=0)
    parts = [text(30, 36, 'THE RHYTHM', 11, MUTED, 'mono'), text(30, 79, 'Small steps. Real progress.', 36, INK, 'serif'), text(850, 35, 'LAST 12 MONTHS', 10, MUTED, 'mono', 'text-anchor="end"')]
    values = [totals[k] for k in month_keys]
    peak = max(values, default=0)
    best_month = values.index(peak)
    for i, (year, month) in enumerate(month_keys):
        height = max(3, round(92*values[i]/max(1, peak)))
        x = 32+i*48
        color = BLUE if i == best_month else '#d9d7cc'
        parts += [f'<rect class="grow" x="{x}" y="{214-height}" width="30" height="{height}" rx="4" fill="{color}" style="--d:{.35+i*.045}s"/>', text(x+15, 237, calendar.month_abbr[month].upper(), 9, MUTED, 'mono', 'text-anchor="middle"')]
        if i == best_month:
            parts.append(text(x+15, 206-height, values[i], 12, BLUE, '', 'text-anchor="middle"'))
    parts += [f'<path d="M632 98v147" stroke="{LINE}"/>']
    for y, number, label in [(120, active, 'ACTIVE DAYS'), (174, best, 'BEST STREAK / DAYS'), (228, busiest, 'BUSIEST DAY')]:
        parts += [text(663, y, number, 31, BLUE, 'serif'), text(718, y-2, label, 9, MUTED, 'mono')]
    parts += [text(30, 275, f'CURRENT STREAK  {streak} DAYS', 10, MUTED, 'mono'), text(850, 275, 'UPDATED '+DATA['updated'], 10, MUTED, 'mono', 'text-anchor="end"')]
    svg('activity', 880, 300, ''.join(parts), f'Monthly activity: {active} active days, best streak {best} days, busiest day {busiest} contributions', .3)


def tiles():
    for i, tile in enumerate(CONFIG['tiles']):
        color, ink = tile['color'], tile['ink']
        parts = [f'<rect x=".5" y=".5" width="279" height="239" rx="14" fill="{color}"/>', '<g class="enter">',
                 text(24, 34, f'0{i+1} /', 11, ink, 'mono'), text(252, 37, '↗', 25, ink, '', 'text-anchor="end"'),
                 f'<circle cx="236" cy="117" r="48" fill="none" stroke="{ink}" stroke-opacity=".14"/>',
                 f'<circle cx="236" cy="117" r="31" fill="none" stroke="{ink}" stroke-opacity=".14" class="pulse"/>',
                 text(24, 135, tile['title'], 30, ink), text(24, 180, tile['subtitle'], 16, ink), text(24, 209, tile['detail'], 12, ink), '</g>']
        svg(tile['id'], 280, 240, ''.join(parts), tile['title']+' — '+tile['subtitle'], .5+i*.12)


def repositories():
    public = {r['name']: r for r in DATA['repositories']['nodes']}
    featured = [public[name] for name in CONFIG['featured'] if name in public]
    for i, repo in enumerate(featured):
        desc = CONFIG.get('project_descriptions', {}).get(repo['name']) or repo.get('description') or 'A public project. Explore the code on GitHub.'
        # Cyrillic needs the sans-serif fallback; only the title uses Instrument Serif.
        parts = [text(30, 34, f'0{i+1} / SELECTED WORK', 10, MUTED, 'mono'), text(30, 84, repo['name'], 39, INK, 'serif'), text(846, 50, '↗', 30, BLUE, '', 'text-anchor="end"')]
        for j, line in enumerate(textwrap.wrap(desc, width=94)[:2]):
            parts.append(text(31, 117+j*22, line, 14, MUTED))
        lang = repo.get('primaryLanguage') or {'name': 'Project', 'color': BLUE}
        parts += [f'<circle cx="35" cy="169" r="4" fill="{lang.get("color") or BLUE}"/>', text(48, 173, lang['name'], 11, MUTED), text(850, 173, f'{repo["stargazerCount"]} STARS   /   {repo["forkCount"]} FORKS', 10, MUTED, 'mono', 'text-anchor="end"')]
        svg('repo-'+repo['name'], 880, 196, ''.join(parts), repo['name']+' — '+desc, .65+i*.1)
    return featured


def main():
    hero()
    heatmap()
    activity()
    tiles()
    featured = repositories()
    if STATIC or os.environ.get('CARD_OUTPUT'):
        return
    md = [f'<!-- Generated by scripts/render_cards.py. Edit profile.json to customize. -->\n',
          f'<img src="./cards/hero.svg" width="100%" alt="{escape(CONFIG["first_name"]+" "+CONFIG["last_name"])} — {escape(CONFIG["tagline"])}" />\n',
          '<img src="./cards/heatmap.svg" width="100%" alt="My contributions over the past year" />\n',
          '<img src="./cards/activity.svg" width="100%" alt="Monthly contributions, active days and streaks" />\n', '<p>']
    for tile in CONFIG['tiles']:
        md.append(f'<a href="{escape(tile["url"], quote=True)}"><img src="./cards/{tile["id"]}.svg" width="32.5%" alt="{tile["title"]}: {tile["subtitle"]}" /></a>')
    md += ['</p>\n', '### Selected work\n']
    for repo in featured:
        md.append(f'<a href="{repo["url"]}"><img src="./cards/repo-{repo["name"]}.svg" width="100%" alt="{escape(repo["name"])} — view repository" /></a>\n')
    md += ['---\n', f'[Explore my repositories](https://github.com/{CONFIG["username"]}?tab=repositories) · [About this profile](./SETUP.md)\n']
    (ROOT/'README.md').write_text('\n'.join(md))
    preview = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nikita — GitHub profile preview</title><style>body{margin:0;background:#fff;color:#282722;font-family:Arial,sans-serif}main{max-width:880px;margin:36px auto;padding:20px}img{display:block;width:100%;height:auto;margin-bottom:14px}.tiles{display:flex;gap:1.25%;margin-bottom:14px}.tiles a{width:32.5%}.tiles img{margin:0}a{color:#2455ed}h2{font-size:20px;font-weight:500;margin:28px 0 16px}footer{font-size:13px;margin:25px 0}</style><main>'
    preview += ''.join(f'<img src="cards/{name}.svg" alt="{name}">' for name in ['hero','heatmap','activity'])
    preview += '<div class="tiles">'+''.join(f'<a href="{escape(t["url"],quote=True)}"><img src="cards/{t["id"]}.svg" alt="{t["title"]}"></a>' for t in CONFIG['tiles'])+'</div><h2>Selected work</h2>'
    preview += ''.join(f'<a href="{r["url"]}"><img src="cards/repo-{r["name"]}.svg" alt="{escape(r["name"])}"></a>' for r in featured)
    preview += '<footer>Built with SVG. Updated daily from GitHub.</footer></main></html>'
    (ROOT/'preview.html').write_text(preview)
    print(f'Rendered {6+len(featured)} SVG cards and README.md.')


if __name__ == '__main__':
    main()
