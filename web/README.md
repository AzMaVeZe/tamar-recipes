# המתכונים של תמר — static site

This folder is the source of the recipe site, hosted on **GitHub Pages**.

Live URL (after the one-time setup below):
**https://azmaveze.github.io/tamar-recipes/**

It is plain, self-contained static HTML — no build step, no framework, no
server runtime. That makes it cheap, fast, and portable: it can be hosted
on GitHub Pages, Cloudflare Pages, Netlify, or any static host without
changes.

## Structure

- `index.html` — homepage. Header + hero + filter chips + 24 recipe cards + footer.
  Each card is an `<a href="recipes/recipe-NN.html">` (relative link), so the
  links work under any mount point.
- `recipes/recipe-01.html` … `recipe-24.html` — one stub page per recipe
  ("בקרוב — [name]"). Replace with real content as it's authored.
- `recipes.html`, `categories.html`, `about.html`, `add-recipe.html` —
  header nav destinations (also stubs for now).
- Internal links are **relative**, so the site works both at
  `/tamar-recipes/` (project Pages) and at the root of a custom domain.
- `wix.config.json` — leftover from an earlier Wix attempt; unused by the
  Pages deploy and safe to delete.

> **Images:** the recipe photos currently load from Wix's public CDN
> (`static.wixstatic.com`). The site hosting itself has no Wix dependency.
> Copying the 24 photos into `web/images/` and pointing the cards at them is
> a clean follow-up if you want to be fully independent of that CDN.

## Deploy

Deploys are automated via GitHub Actions
(`.github/workflows/pages.yml`). Every push that touches `web/**`
publishes the folder to GitHub Pages.

### One-time setup (per repo)

1. In GitHub: **Settings → Pages → Build and deployment → Source:
   GitHub Actions**.
2. That's it. The next push under `web/` (or a manual run from the
   **Actions** tab) builds and publishes the site.

> GitHub Pages is free for **public** repositories. For a private repo,
> Pages needs a paid plan — in that case host on Cloudflare Pages or
> Netlify instead (same static files, same relative links).

### Manual redeploy

**Actions** tab → *Deploy web/ to GitHub Pages* → **Run workflow**.

## What's next

1. Replace each recipe stub with the real ingredients + method.
2. Wire the filter chips (`הכל / עוגות / מאפים / בשרי / עוגיות`) to actually
   filter the card grid — small vanilla-JS `data-category` toggle.
3. Optionally copy the recipe photos into `web/images/` to drop the Wix CDN.
4. Attach a custom domain (Settings → Pages → Custom domain) when ready.
