# Contributing

Entries are welcome. The list is only useful if it stays sharp, so there's a bar.

## What makes a good entry

An entry needs three things. If you can't supply all three, it isn't ready yet.

1. **The phrase, and its variants.** Not a vibe - the actual strings a writer would
   produce. "sit with," "worth sitting with." A scanner has to be able to match it.
2. **Why it's a tell.** What the phrase is *doing*: reaching for depth it hasn't
   earned, crowning one item out of a set, inventing an observation nobody made. Name
   the move, not just the mood.
3. **What to write instead.** The plain version. An entry that only forbids something
   leaves the writer stuck.

## What gets rejected

- **Ordinary words that models happen to use.** Everything is used by models. The
  question is whether the phrase signals *unearned* writing.
- **Personal pet peeves.** "I don't like semicolons" is a preference, not a tell.
- **House-style rules.** Any individual publication's voice rules belong in that
  publication's style guide. This list is about AI-writing tells generally.
- **Entries with no plain-English replacement.** See point 3 above.
- **Duplicates.** Check whether an existing entry already covers it. If yours is a
  sharper variant of something listed, propose an added alias instead of a new entry.

## How to propose one

1. Edit **`claudisms.json`** only. It's the source of truth.
2. Add your entry to the `terms` array:

   ```json
   {
     "id": "kebab-case-slug",
     "term": "the phrase",
     "display": "\"the phrase\" / \"a variant\"",
     "aliases": ["the phrase", "a variant"],
     "category": "Confirmed Claudisms",
     "definition": "- what the move is, and what to say instead.",
     "url": "https://claudisms.ai/#kebab-case-slug"
   }
   ```

   `definition` starts with its own separator (usually `- `). `id` and the `#anchor`
   in `url` must match.
3. Bump `count` to the new number of terms and set `updated` to today's date.
4. Run `python3 build.py` and commit the regenerated `claudisms.md`, `index.html`,
   `llms.txt` and `sitemap.xml` alongside your JSON change. CI rebuilds and compares
   all four, and will reject a PR where they're out of sync.

   The build refuses entries that would break the page: raw angle brackets, unbalanced
   inline tags, a duplicate `id`, a `url` whose anchor doesn't match its `id`, a
   category it doesn't know about, or a `count` that disagrees with the list. If it
   stops with a message, the message is the fix.
5. Open the pull request. Say in a sentence or two where you've seen the phrase in the
   wild - real examples are the most persuasive part of a submission.

Entries are reviewed by hand and merged when they clear the bar. A rejection usually
means the entry needs a sharper "why," not that the observation was wrong.
