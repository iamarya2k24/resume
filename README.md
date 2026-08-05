# Résumé Site

Single-page résumé hosted on GitHub Pages. `resume.yaml` (YAMLResume schema) is the only file you edit — everything else is markup, styling, or generated at build time.

![Deployed with GitHub Actions](https://img.shields.io/badge/deploy-GitHub%20Actions-2f5d50)
![License MIT](https://img.shields.io/badge/license-MIT-1b1f1d)

## Preview

![Résumé site screenshot](docs/screenshot.png)

> Screenshot not included in this scaffold. Add your own after deploying — see [Adding the screenshot](#adding-the-screenshot).

## How it works

1. `index.html` loads, then JavaScript fetches `resume.yaml` and parses it with [`js-yaml`](https://github.com/nodeca/js-yaml) (CDN).
2. The parsed `content.*` data (YAMLResume schema) renders into the DOM — experience, skills, projects, education, certificates, languages, publications, volunteer work, interests, references.
3. On every push to `main`, GitHub Actions (`.github/workflows/deploy.yml`) runs `scripts/generate_seo.py`, which reads `resume.yaml` and writes:
   - `robots.txt` — explicitly allows major AI/LLM crawlers (see [SEO & crawler access](#seo--crawler-access))
   - `sitemap.xml`
   - `llms.txt` — plain-markdown résumé for agents that don't execute JavaScript
   - `<title>`, meta description, Open Graph/Twitter tags, and a JSON-LD `Person` block, injected into `index.html`'s `<head>`
4. The workflow also writes `build-info.json` (commit hash, build time) — the footer reads it and links to the exact commit deployed.
5. Everything is uploaded as a Pages artifact and deployed. None of the generated files (`robots.txt`, `sitemap.xml`, `llms.txt`, `build-info.json`) are committed to git — they're derived fresh every build, so `resume.yaml` stays the single source of truth with no drift.

## File structure

```
your-repo/
├── index.html                        # markup, fetch/parse/render logic, SEO marker blocks
├── styles.css                         # all styling
├── resume.yaml                        # all content — edit this to update the résumé
├── site.webmanifest                   # PWA/home-screen icon metadata
├── favicon.svg / favicon.ico / favicon-16x16.png / favicon-32x32.png
├── apple-touch-icon.png / icon-192.png / icon-512.png
├── scripts/
│   └── generate_seo.py                # build-time: robots.txt, sitemap.xml, llms.txt, meta/JSON-LD injection
├── .github/workflows/
│   └── deploy.yml                     # CI: run generate_seo.py, write build-info.json, deploy to Pages
├── .gitignore                         # ignores the files generate_seo.py produces
└── README.md
```

## Local development

`fetch()` requires the page to be served over HTTP, not opened as a `file://` URL.

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000`. The footer and SEO tags won't show build info locally (those only exist after the Actions build) — that's expected.

To preview the generated SEO artifacts locally:

```bash
pip install pyyaml
python3 scripts/generate_seo.py
```

This writes `robots.txt`, `sitemap.xml`, `llms.txt`, and injects meta/JSON-LD directly into your local `index.html`. **Don't commit the result** — revert `index.html` (`git checkout index.html`) after checking it; the `.gitignore` already excludes the other three.

## Editing content

Edit `resume.yaml` only. It follows the [YAMLResume schema](https://yamlresume.dev/docs/compiler/schema) — top-level content keys:

| Key | Purpose |
|---|---|
| `basics` | Name, headline, contact, summary |
| `location` | City, region, country |
| `profiles` | LinkedIn, GitHub, etc. |
| `work` | Jobs — `name`, `position`, dates, `summary`, `keywords` |
| `skills` | `{ name, level, keywords }` groups |
| `projects` | `{ name, url, description, summary, keywords }` |
| `education`, `certificates`, `languages`, `publications`, `volunteer`, `interests`, `references` | Optional — rendered only if present |

Sections with no data are skipped automatically. `endDate` left blank renders as "Present". `summary` fields support `- ` bullet lists, `**bold**`, `*italic*`, and `[text](url)` links.

## SEO & crawler access

`robots.txt` (generated at build time) explicitly allows: `*`, `GPTBot`, `ChatGPT-User`, `OAI-SearchBot`, `ClaudeBot`, `Claude-Web`, `anthropic-ai`, `PerplexityBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`, `Bytespider`, `cohere-ai`, `Amazonbot`.

**Known limitation:** the résumé body renders via JavaScript. Search engines that execute JS (Google) see it fine. Most AI/LLM crawlers fetch raw HTML only and won't see the rendered body — so three things exist specifically for them, all generated from `resume.yaml` so they can't drift out of sync:

- **JSON-LD** (`Person` schema) in `<head>` — structured facts: name, job title, contact, skills, education, social links
- **`llms.txt`** — the full résumé as plain markdown
- **`resume.yaml` itself** — plain text, fetchable and parseable without JS

If you want the rendered body itself visible to non-JS crawlers too, that requires server-side or build-time HTML rendering (not just data injection) — out of scope for this static-artifact-only setup, but ask if you want it added.

## Deployment (GitHub Pages via Actions)

```bash
git init
git add .
git commit -m "Initial resume site"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

Then:

1. **Settings → Pages → Source → GitHub Actions** (not "Deploy from a branch")
2. Push triggers `.github/workflows/deploy.yml` automatically — check the **Actions** tab

Site goes live at the URL shown under Settings → Pages once the workflow finishes.

To update content: edit `resume.yaml`, commit, push. To force a rebuild without content changes: `git commit --allow-empty -m "Trigger build" && git push`.

## Adding the screenshot

1. Deploy the site.
2. Screenshot it in a browser at a reasonable width (~1280px).
3. Save as `docs/screenshot.png`, commit, push.

```bash
mkdir -p docs
git add docs/screenshot.png
git commit -m "Add site screenshot"
git push
```

## Custom domain (optional)

1. Add a `CNAME` file to the repo root containing your domain.
2. At your DNS provider, add a `CNAME` record pointing to `<username>.github.io`.
3. **Settings → Pages** → enter the custom domain, enable **Enforce HTTPS** once the certificate provisions.
4. `basics.url` in `resume.yaml` drives the canonical URL, sitemap, and Open Graph tags — update it to match your custom domain, or they'll keep pointing at the `github.io` URL.

## License

MIT — use, modify, and redeploy freely.
