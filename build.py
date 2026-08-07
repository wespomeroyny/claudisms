#!/usr/bin/env python3
"""Build the published site from claudisms.json (the source of truth).

Inputs   claudisms.json  - every entry
         template.html   - the page shell, with the marker pairs below
Outputs  index.html, claudisms.md, llms.txt, sitemap.xml

Usage:
  python3 build.py            # regenerate all four outputs
  python3 build.py --check    # exit 1 if any output is out of date (used by CI)

template.html must contain both marker pairs, and the JSONLD pair must sit OUTSIDE
any <script> element - the script tag itself is generated:
  <!-- BEGIN:TERMS --> ... <!-- END:TERMS -->
  <!-- BEGIN:JSONLD --> ... <!-- END:JSONLD -->
"""
import json, re, sys, os, html, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(ROOT, 'claudisms.json')
MD_PATH   = os.path.join(ROOT, 'claudisms.md')
HTML_PATH = os.path.join(ROOT, 'index.html')
TPL_PATH  = os.path.join(ROOT, 'template.html')
LLMS_PATH = os.path.join(ROOT, 'llms.txt')
MAP_PATH  = os.path.join(ROOT, 'sitemap.xml')

# Section order on the page. Any category not listed is appended alphabetically.
ORDER = [
    'Confirmed Claudisms',
    'Structural / framing tics',
    'Register tics to avoid',
    'Spoken-word tells',
    # Everything below sits under the "Imported from external references" banner
    # and must be level 3. A new category has to be added here explicitly.
    'Vocabulary',
    'Phrases',
    'Structural tics',
]


MD_HEADER = """# Claudisms

A living banlist of the words, phrases, and structural tics that signal AI-generated writing - the ones to flag and scrub from a draft before it goes out. It grows as new ones are caught. For the thinking behind why it matters, read [Your Name Is Still on It](https://wespomeroy.substack.com/p/your-name-is-still-on-it).

Words, phrases, and tics that AI models over-reach for. Flagged as they appear and listed here so they can be systematically checked and scrubbed from drafts.

---
"""

MD_IMPORTED_NOTE = """## Imported from external AI-writing references

Cross-validated against Will Francis's "How to Stop Claude Writing Like an AI" (willfrancis.com, March 2026), Wikipedia's "Signs of AI writing" page, and the Washington Post analysis of 328K ChatGPT messages. Items below are widely-flagged AI tells that weren't already in this banlist. Some are diction a careful writer would catch instinctively - listed here as defaults to avoid.
"""

MD_FOOTER = """---

## Usage

When drafting, check against this list before producing. If a candidate phrase appears here, rewrite in plainer English before showing the draft. This list grows - add new entries as they're flagged.

*A living list of AI-writing tells. Free to copy and adapt.*
"""


def load():
    with open(JSON_PATH, encoding='utf-8') as f:
        return json.load(f)


def categories(data):
    seen = []
    for t in data['terms']:
        if t['category'] not in seen:
            seen.append(t['category'])
    ordered = [c for c in ORDER if c in seen]
    ordered += sorted(c for c in seen if c not in ORDER)
    return ordered


IMPORTED_BANNER_HTML = """  <hr>

  <h2>Imported from external AI-writing references</h2>
  <p class="note">
    Cross-validated against Will Francis's "How to Stop Claude Writing Like an AI" (willfrancis.com,
    March 2026), Wikipedia's "Signs of AI writing" page, and the Washington Post analysis of 328K
    ChatGPT messages. Items below are widely-flagged AI tells that weren't already in this banlist.
    Some are diction a careful writer would catch instinctively - listed here as defaults to avoid.
  </p>
"""


ALLOWED_INLINE = ('code', 'em', 'strong', 'abbr')


def esc(s):
    """Escape only what HTML requires, then restore the handful of inline tags
    that entry text is allowed to carry. The source text uses literal quotes and
    apostrophes, so html.escape() would mangle every existing entry."""
    out = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    for tag in ALLOWED_INLINE:
        out = out.replace(f'&lt;{tag}&gt;', f'<{tag}>').replace(f'&lt;/{tag}&gt;', f'</{tag}>')
    return out


def head(term):
    """The bolded head, exactly as authored."""
    return term.get('display') or term['term']


def body(term):
    """The text that follows the bolded head, stored verbatim in the JSON so the
    separator each entry actually uses (" - ", " and ...", " in the ... sense")
    is preserved rather than guessed."""
    d = term['definition'].strip()
    return ' ' + d


MARKERS = ('<!-- BEGIN:TERMS -->', '<!-- END:TERMS -->',
           '<!-- BEGIN:JSONLD -->', '<!-- END:JSONLD -->')


def validate(data):
    """Refuse to build anything questionable. Every check here exists because the
    failure it catches would otherwise ship silently rather than crash."""
    terms = data['terms']
    ids = [t['id'] for t in terms]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f'duplicate ids: {dupes}')

    levels = {}
    for t in terms:
        for field in ('id', 'term', 'display', 'category', 'definition', 'url'):
            if not t.get(field):
                raise SystemExit(f"term {t.get('id')!r} is missing {field}")
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', t['id']):
            raise SystemExit(f"term {t['id']!r} is not a kebab-case slug")
        want = f"https://claudisms.ai/#{t['id']}"
        if t['url'] != want:
            raise SystemExit(f"term {t['id']!r} url is {t['url']!r}, expected {want!r}")

        lvl = t.get('level', 2)
        if lvl not in (2, 3):
            raise SystemExit(f"term {t['id']!r} has level {lvl!r}; must be 2 or 3")
        prev = levels.setdefault(t['category'], lvl)
        if prev != lvl:
            raise SystemExit(
                f"category {t['category']!r} mixes level {prev} and {lvl}"
            )

        blob = t['display'] + t['definition']
        for mk in MARKERS:
            if mk in blob:
                raise SystemExit(f"term {t['id']!r} contains the build marker {mk}")
        for tag in ALLOWED_INLINE:
            if blob.count(f'<{tag}>') != blob.count(f'</{tag}>'):
                raise SystemExit(f"term {t['id']!r} has unbalanced <{tag}> tags")
        stray = re.sub(r'</?(?:' + '|'.join(ALLOWED_INLINE) + r')>', '', blob)
        if '<' in stray or '>' in stray.replace('->', ''):
            raise SystemExit(
                f"term {t['id']!r} contains raw angle brackets outside the "
                f"allowed inline tags {ALLOWED_INLINE}"
            )

    unknown = [c for c in levels if c not in ORDER]
    if unknown:
        raise SystemExit(
            f'category {unknown!r} is not in ORDER in build.py - add it in the '
            f'position it should appear, so it cannot land under the wrong banner'
        )
    if data.get('count') != len(terms):
        raise SystemExit(
            f"count field ({data.get('count')}) != actual terms ({len(terms)})"
        )


def t_level(data, cat):
    return next(t.get('level', 2) for t in data['terms'] if t['category'] == cat)


MD_INLINE = ((r'<strong>(.*?)</strong>', r'**\1**'),
             (r'<em>(.*?)</em>', r'*\1*'),
             (r'<code>(.*?)</code>', r'`\1`'),
             (r'<abbr>(.*?)</abbr>', r'\1'))


def md_inline(text):
    """Inline HTML in an entry becomes Markdown emphasis in the .md output."""
    for pat, rep in MD_INLINE:
        text = re.sub(pat, rep, text)
    return text


def render_md(data):
    parts = [MD_HEADER]
    imported_done = False
    for cat in categories(data):
        if t_level(data, cat) == 3 and not imported_done:
            parts.append('\n' + MD_IMPORTED_NOTE)
            imported_done = True
        lvl = next(x.get('level', 2) for x in data['terms'] if x['category'] == cat)
        parts.append(f"\n{'#' * lvl} {cat}\n\n")
        for t in data['terms']:
            if t['category'] != cat:
                continue
            parts.append(f"- **{md_inline(head(t))}**{md_inline(body(t))}\n")
        if t_level(data, cat) == 2:
            parts.append('\n---\n')
    parts.append('\n' + MD_FOOTER)
    return ''.join(parts)


def render_terms_html(data):
    out = []
    imported_done = False
    for cat in categories(data):
        lvl = next(t.get('level', 2) for t in data['terms'] if t['category'] == cat)
        if lvl == 3 and not imported_done:
            out.append(IMPORTED_BANNER_HTML)
            imported_done = True
        out.append(f'  <h{lvl}>{esc(cat)}</h{lvl}>')
        out.append('  <ul>')
        for t in data['terms']:
            if t['category'] != cat:
                continue
            out.append(
                f'    <li id="{t["id"]}"><strong>{esc(head(t))}</strong>'
                f'{esc(body(t))}</li>'
            )
        out.append('  </ul>')
    return '\n'.join(out)


def render_llms(data):
    n = len(data['terms'])
    return f"""# Claudisms

> {data['description']}

Claudisms is a living, curated banlist of the words, phrases, and structural tics that signal AI-generated writing. Each entry names a tic and explains why to avoid it and what to write instead. Released into the public domain (CC0) - free to quote, cite, and reuse.

## Content
- [Claudisms (Markdown)](https://claudisms.ai/claudisms.md): The full list in plain markdown - the best source for reading or citing.
- [Claudisms (JSON)](https://claudisms.ai/claudisms.json): The full list as structured data ({n} terms with ids, aliases, categories, and definitions).
- [Claudisms (HTML)](https://claudisms.ai/): The human-readable page.
- [Source and contributions](https://github.com/wespomeroyny/claudisms): The canonical repository.
"""


def render_sitemap(data):
    d = data['updated']
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>https://claudisms.ai/</loc><lastmod>{d}</lastmod>'
        '<changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
        f'  <url><loc>https://claudisms.ai/claudisms.md</loc><lastmod>{d}</lastmod>'
        '<priority>0.6</priority></url>\n'
        f'  <url><loc>https://claudisms.ai/claudisms.json</loc><lastmod>{d}</lastmod>'
        '<priority>0.6</priority></url>\n'
        '</urlset>\n'
    )


TAG_RE = re.compile(r'</?(?:code|em|strong|abbr)>')


def plain(text):
    """Definition text with its presentational separator and inline tags removed -
    what a machine-readable consumer should get."""
    t = TAG_RE.sub('', text).strip()
    t = re.sub(r'^[-\u2013\u2014]\s+', '', t)
    return ' '.join(t.split())


def render_jsonld(data):
    ld = {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "@id": "https://claudisms.ai/#claudisms",
        "name": data['name'],
        "alternateName": "A living banlist of AI-writing tells",
        "description": data['description'],
        "url": data['url'],
        "inLanguage": "en",
        "license": data['license'],
        "dateModified": data['updated'],
        "hasDefinedTerm": [],
    }
    for t in data['terms']:
        entry = {
            "@type": "DefinedTerm",
            "name": t['term'],
            "description": plain(t['definition']),
            "url": t['url'],
            "inDefinedTermSet": "https://claudisms.ai/#claudisms",
        }
        extra = [a for a in (t.get('aliases') or []) if a.lower() != t['term'].lower()]
        if extra:
            entry['alternateName'] = extra
        ld['hasDefinedTerm'].append(entry)
    out = json.dumps(ld, ensure_ascii=False, indent=1)
    # A '<' inside a <script> element can terminate it early. JSON allows \u003c,
    # so escaping it keeps the payload valid JSON and inert as markup.
    out = out.replace('<', '\\u003c').replace('>', '\\u003e')
    return ('<script type="application/ld+json">\n' + out + '\n</script>')


def splice(src, name, body):
    b, e = f'<!-- BEGIN:{name} -->', f'<!-- END:{name} -->'
    if b not in src or e not in src:
        raise SystemExit(f'index.html is missing the {name} markers ({b} / {e})')
    pre, rest = src.split(b, 1)
    _, post = rest.split(e, 1)
    return f'{pre}{b}\n{body}\n{e}{post}'


def render_html(data):
    with open(TPL_PATH, encoding='utf-8') as f:
        src = f.read()
    src = splice(src, 'TERMS', render_terms_html(data))
    src = splice(src, 'JSONLD', render_jsonld(data))
    return src


def write(path, content):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    with open(path, encoding='utf-8') as f:
        back = f.read()
    if back != content:
        raise SystemExit(f'read-back mismatch on {path}')
    if not back.endswith('\n'):
        raise SystemExit(f'{path} is not newline-terminated')


def main():
    check = '--check' in sys.argv
    data = load()
    validate(data)

    outputs = (
        (MD_PATH, render_md(data)),
        (HTML_PATH, render_html(data)),
        (LLMS_PATH, render_llms(data)),
        (MAP_PATH, render_sitemap(data)),
    )
    if check:
        stale = []
        for path, want in outputs:
            with open(path, encoding='utf-8') as f:
                if f.read() != want:
                    stale.append(os.path.basename(path))
        if stale:
            print('OUT OF DATE: ' + ', '.join(stale) + ' - run: python3 build.py')
            return 1
        print(f'up to date ({len(data["terms"])} terms)')
        return 0
    for path, content in outputs:
        write(path, content)
    print(f'built {len(data["terms"])} terms -> '
          + ', '.join(os.path.basename(p) for p, _ in outputs))
    return 0


if __name__ == '__main__':
    sys.exit(main())
