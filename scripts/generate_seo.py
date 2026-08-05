#!/usr/bin/env python3
"""
Derives all crawler-facing SEO / LLM-agent artifacts from resume.yaml at
build time: robots.txt, sitemap.xml, llms.txt, and the <!-- SEO:META -->
and <!-- SEO:JSONLD --> blocks in index.html.

resume.yaml stays the single source of truth — nothing generated here is
hand-maintained or committed back to the repo; it's regenerated fresh on
every CI build and shipped as part of the Pages deploy artifact only.

Run: python3 scripts/generate_seo.py
"""
import html
import json
import re
from datetime import datetime, timezone

import yaml

ROOT = "."

AI_CRAWLERS = [
    "*", "GPTBot", "ChatGPT-User", "OAI-SearchBot",
    "ClaudeBot", "Claude-Web", "anthropic-ai",
    "PerplexityBot", "Google-Extended", "Applebot-Extended",
    "CCBot", "Bytespider", "cohere-ai", "Amazonbot",
]


def load_resume():
    with open(f"{ROOT}/resume.yaml", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc["content"]


def strip_inline_md(line):
    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
    line = re.sub(r"\*([^*]+)\*", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    return line


def strip_md(text):
    """Flattens a '- bullet\\n- bullet' markdown block into one plain sentence."""
    if not text:
        return ""
    lines = [l.strip().lstrip("-").strip() for l in str(text).splitlines() if l.strip()]
    return strip_inline_md(" ".join(lines))


def md_lines(text):
    """Splits a '- bullet\\n- bullet' markdown block into individual plain-text lines."""
    if not text:
        return []
    lines = [l.strip().lstrip("-").strip() for l in str(text).splitlines() if l.strip()]
    return [strip_inline_md(l) for l in lines if l]
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "\u2026"


def truncate(text, limit=160):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "\u2026"


def site_url(basics):
    url = (basics.get("url") or "").strip() or "https://example.com/"
    if not url.endswith("/"):
        url += "/"
    return url


def write_robots(url):
    lines = []
    for bot in AI_CRAWLERS:
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines.append(f"Sitemap: {url}sitemap.xml")
    with open(f"{ROOT}/robots.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_sitemap(url):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n"
        f"    <loc>{url}</loc>\n"
        f"    <lastmod>{today}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>1.0</priority>\n"
        "  </url>\n"
        "</urlset>\n"
    )
    with open(f"{ROOT}/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml)


def write_llms_txt(data, url):
    b = data.get("basics", {})
    loc = data.get("location", {})
    out = [f"# {b.get('name', '')}", ""]

    if b.get("headline"):
        out += [f"> {b['headline']}", ""]

    summary = strip_md(b.get("summary"))
    if summary:
        out += [summary, ""]

    contact = []
    if b.get("email"):
        contact.append(f"Email: {b['email']}")
    if b.get("phone"):
        contact.append(f"Phone: {b['phone']}")
    loc_bits = ", ".join(filter(None, [loc.get("city"), loc.get("region"), loc.get("country")]))
    if loc_bits:
        contact.append(f"Location: {loc_bits}")
    contact.append(f"Site: {url}")
    for p in data.get("profiles") or []:
        contact.append(f"{p.get('network')}: {p.get('url')}")
    out += ["## Contact"] + [f"- {c}" for c in contact] + [""]

    work = data.get("work") or []
    if work:
        out.append("## Experience")
        for job in work:
            dates = f"{job.get('startDate', '')} \u2013 {job.get('endDate') or 'Present'}"
            out.append(f"### {job.get('position', '')}, {job.get('name', '')} ({dates})")
            for line in md_lines(job.get("summary")):
                out.append(f"- {line}")
            kws = job.get("keywords") or []
            if kws:
                out.append(f"Keywords: {', '.join(kws)}")
            out.append("")

    skills = data.get("skills") or []
    if skills:
        out.append("## Skills")
        for s in skills:
            kws = ", ".join(s.get("keywords") or [])
            out.append(f"- {s.get('name', '')} ({s.get('level', '')}): {kws}")
        out.append("")

    projects = data.get("projects") or []
    if projects:
        out.append("## Projects")
        for p in projects:
            desc = p.get("description") or strip_md(p.get("summary"))
            out.append(f"- {p.get('name', '')}: {desc} ({p.get('url', '')})")
        out.append("")

    edu = data.get("education") or []
    if edu:
        out.append("## Education")
        for e in edu:
            dates = f"{e.get('startDate', '')} \u2013 {e.get('endDate') or 'Present'}"
            area = f", {e.get('area')}" if e.get("area") else ""
            out.append(f"- {e.get('degree', '')}{area} \u2014 {e.get('institution', '')} ({dates})")
        out.append("")

    certs = data.get("certificates") or []
    if certs:
        out.append("## Certificates")
        for c in certs:
            out.append(f"- {c.get('name', '')} \u2014 {c.get('issuer', '')} ({c.get('date', '')})")
        out.append("")

    out.append("## Notes for automated readers")
    out.append(
        "Generated from resume.yaml at build time; mirrors the canonical "
        f"r\u00e9sum\u00e9 content. Structured data: {url} (JSON-LD in <head>). "
        f"Full source: {url}resume.yaml."
    )

    with open(f"{ROOT}/llms.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out).strip() + "\n")


def build_json_ld(data, url):
    b = data.get("basics", {})
    loc = data.get("location", {})

    same_as = [p.get("url") for p in (data.get("profiles") or []) if p.get("url")]

    knows_about = []
    for s in data.get("skills") or []:
        if s.get("name"):
            knows_about.append(s["name"])
        knows_about.extend(s.get("keywords") or [])

    alumni_of = [
        {"@type": "EducationalOrganization", "name": e.get("institution")}
        for e in (data.get("education") or [])
        if e.get("institution")
    ]

    ld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": b.get("name"),
        "jobTitle": b.get("headline"),
        "description": truncate(strip_md(b.get("summary")), 300) or None,
        "email": f"mailto:{b['email']}" if b.get("email") else None,
        "telephone": b.get("phone"),
        "url": url,
        "sameAs": same_as or None,
        "knowsAbout": knows_about or None,
        "alumniOf": alumni_of or None,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": loc.get("city"),
            "addressRegion": loc.get("region"),
            "addressCountry": loc.get("country"),
        }
        if loc
        else None,
    }
    ld = {k: v for k, v in ld.items() if v}
    return json.dumps(ld, ensure_ascii=False, indent=2)


def build_meta_block(data, url):
    b = data.get("basics", {})
    title = f"{b.get('name', '')} \u2014 {b.get('headline', '')}".strip(" \u2014")
    desc = truncate(strip_md(b.get("summary")) or b.get("headline") or "")
    og_image = f"{url}icon-512.png"

    def tag(name, content, prop=False):
        attr = "property" if prop else "name"
        return f'<meta {attr}="{name}" content="{html.escape(content)}" />'

    lines = [
        f"<title>{html.escape(title)}</title>",
        tag("description", desc),
        f'<link rel="canonical" href="{html.escape(url)}" />',
        tag("og:type", "profile", prop=True),
        tag("og:title", title, prop=True),
        tag("og:description", desc, prop=True),
        tag("og:url", url, prop=True),
        tag("og:image", og_image, prop=True),
        tag("twitter:card", "summary"),
        tag("twitter:title", title),
        tag("twitter:description", desc),
        tag("twitter:image", og_image),
    ]
    return "\n".join(lines)


def inject_head(data, url):
    path = f"{ROOT}/index.html"
    with open(path, encoding="utf-8") as f:
        src = f.read()

    meta_block = build_meta_block(data, url)
    jsonld_block = f'<script type="application/ld+json">\n{build_json_ld(data, url)}\n</script>'

    src = re.sub(
        r"<!-- SEO:META -->.*?<!-- /SEO:META -->",
        f"<!-- SEO:META -->\n{meta_block}\n<!-- /SEO:META -->",
        src,
        flags=re.S,
    )
    src = re.sub(
        r"<!-- SEO:JSONLD -->.*?<!-- /SEO:JSONLD -->",
        f"<!-- SEO:JSONLD -->\n{jsonld_block}\n<!-- /SEO:JSONLD -->",
        src,
        flags=re.S,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(src)


def main():
    data = load_resume()
    url = site_url(data.get("basics", {}))
    write_robots(url)
    write_sitemap(url)
    write_llms_txt(data, url)
    inject_head(data, url)
    print(f"SEO artifacts generated for {url}")


if __name__ == "__main__":
    main()
