# Claudisms

A living banlist of the words, phrases, and structural tics that signal AI-generated
writing - the ones to flag and scrub from a draft before it goes out.

Published at **[claudisms.ai](https://claudisms.ai/)**, deployed automatically from this repository. Released into the public domain
under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) - copy it, fork it,
wire it into your own tooling, no attribution required.

## Use it

| File | What it's for |
|---|---|
| `claudisms.json` | **The source of truth.** Every entry, machine-readable. Build tooling against this. |
| `template.html` | The page shell - layout, styling, copy. Edit this to change anything that isn't an entry. |
| `claudisms.md` | The same list as Markdown, for reading or pasting into a style guide. |
| `index.html` | The published page. |
| `llms.txt`, `sitemap.xml` | Machine-readable pointers for crawlers. |

`claudisms.md`, `index.html`, `llms.txt` and `sitemap.xml` are **generated** - from
`claudisms.json` and `template.html`. Don't edit them by hand; your changes will be
overwritten on the next build. CI rebuilds and compares all four, so drift can't ship.

Pull the list straight from the site:

```bash
curl -s https://claudisms.ai/claudisms.json
```

Each entry looks like this:

```json
{
  "id": "sit-with",
  "term": "sit with",
  "display": "\"sit with\" / \"worth sitting with\"",
  "aliases": ["sit with", "worth sitting with"],
  "category": "Confirmed Claudisms",
  "definition": "- reflective-pose filler. Sounds thoughtful; doesn't say anything.",
  "url": "https://claudisms.ai/#sit-with"
}
```

`aliases` are the strings a scanner should match on. `display` is the heading as it
appears on the page. `definition` keeps its own leading separator so entries that
continue their heading mid-sentence still read correctly.

## Build

```bash
python3 build.py           # regenerate claudisms.md and index.html from the JSON
python3 build.py --check   # exit 1 if the generated files are out of date
```

No dependencies beyond the Python standard library. CI runs `--check` on every pull
request, so a change to `claudisms.json` has to ship with its regenerated output.

## Contribute

New entries are welcome - see [CONTRIBUTING.md](CONTRIBUTING.md) for the bar an entry
has to clear and how to open a pull request.

## Why this exists

Models reach for the same small set of moves, and once you can name them you stop
shipping them. For the thinking behind it, read
[Your Name Is Still on It](https://wespomeroy.substack.com/p/your-name-is-still-on-it).
