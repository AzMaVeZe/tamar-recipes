# המתכונים של תמר

Family recipe site, hosted on **GitHub Pages**: https://azmaveze.github.io/tamar-recipes/

Plain static HTML/CSS/JS. No framework, no server, no database. Pages are **generated** from one data file by a small stdlib-only Python script, so every page shares the same header, footer, cards and styles.

## Layout

| Path | What it is |
|---|---|
| `data/recipes.json` | **The source of truth.** Site settings, categories, and every recipe (title, source, kosher, tags, time, yield, category, image). |
| `data/transcriptions/recipe-NN.json` | Text transcription of each scanned recipe (ingredients, steps, notes). Shown under the scan; also feeds search. |
| `tools/build.py` | Generates everything in `web/` from `data/`. |
| `web/assets/site.css`, `web/assets/site.js` | Shared styles and behavior (filter/search, "🎲 תפתיעו אותי", cooking mode, "הכנתי את זה", share, the add-recipe form). Hand-written, not generated. |
| `web/images/` | Recipe scans (JPG). |
| `web/` (everything else) | **Generated.** Don't edit the HTML by hand; edit `data/` and rebuild. |
| `.github/workflows/pages.yml` | On every push to `main` that touches `web/`, `data/` or `tools/`: runs the build and publishes `web/` to Pages. |

## Common tasks

**Add a recipe**
1. Put the scan in `web/images/` (JPG, ideally ≥1400px wide so it's readable on phones).
2. Add an entry to `data/recipes.json` → `recipes` (copy an existing one; give it the next `recipe-NN` id).
3. Optional: add `data/transcriptions/recipe-NN.json` with the text version (same shape as the existing files).
4. `python3 tools/build.py`, check `web/` locally, commit, merge to `main`. The workflow deploys.

**Fix a transcription** – edit `data/transcriptions/recipe-NN.json`. Words marked `word[?]` render as "uncertain"; a bare `[?]` renders as "unreadable". When a recipe is fully checked, remove the marks and set `"confidence": "verified"`.

**Change categories** – edit `categories` in `data/recipes.json` and each recipe's `category`. Chips, the categories page, counts and the form update on rebuild.

**Turn on Formspree for the add-recipe form** – create a form at formspree.io, put its id in `data/recipes.json` → `site.formspree_id`, rebuild. While it's empty, the form sends the recipe through WhatsApp instead (no dead end, and no email address in the page source).

**Custom domain** – set it in Settings → Pages, then update `site.url` in `data/recipes.json` (used for canonical/OG/sitemap and the 404 page's `<base>`) and rebuild.

## Notes

- Internal links are relative, so the site works under `/tamar-recipes/` and at the root of a custom domain.
- Accessibility follows IS 5568 / WCAG 2.1 AA: see `web/accessibility.html` (generated from `tools/build.py`). The statement still needs the accessibility contact's details.
- Transcriptions were produced automatically from the scans and are marked as unverified on the site until a person checks them.
