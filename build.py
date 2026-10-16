#!/usr/bin/env python3
"""
Gera as páginas estáticas do site a partir de src/index.html.

    python3 build.py

Saída (estes arquivos são os publicados na Cloudflare):
    index.html      -> português (página principal)
    en/index.html   -> inglês
    es/index.html   -> espanhol
    sitemap.xml

Por quê: o Google lê o HTML como ele vem do servidor. Antes, esse HTML era só
em inglês e o português aparecia via JavaScript, então o site não aparecia em
buscas em português. Agora cada idioma tem a sua URL, já com o texto no HTML.

Para mudar um texto: edite o bloco I18N em src/index.html e rode o build.
Sem dependências externas (só Python 3).
"""
import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://lbhorizon.com.br"
LANGS = {  # código: (caminho, og:locale)
    "pt": ("/", "pt_BR"),
    "en": ("/en/", "en_US"),
    "es": ("/es/", "es_ES"),
}
HREFLANG = {"pt": "pt-BR", "en": "en", "es": "es"}

# Dados da empresa para o Google (schema.org). Ajuste aqui se algo mudar.
BUSINESS = {
    "name": "LB Horizon",
    "telephone": "+55-21-98376-9654",
    "email": "hello@lbhorizon.com.br",
    "founder": "Leonardo Ferreira dos Santos",
    "foundingDate": "2026-07-15",
    "city": "Rio de Janeiro",
    "region": "RJ",
    "country": "BR",
    # Coloque aqui as URLs dos perfis oficiais (LinkedIn, Instagram...).
    "sameAs": ["https://www.instagram.com/lbhorizon.consultoria/"],
}
SERVICES = {
    "pt": ["Consultoria em Tecnologia", "Inteligência Artificial", "Automação de Processos",
           "Transformação Digital", "Gestão de Entregas de TI"],
    "en": ["Technology Consulting", "Artificial Intelligence", "Process Automation",
           "Digital Transformation", "IT Delivery Management"],
    "es": ["Consultoría Tecnológica", "Inteligencia Artificial", "Automatización de Procesos",
           "Transformación Digital", "Gestión de Entregas de TI"],
}


def parse_i18n(src: str) -> dict:
    """Lê o objeto I18N do JavaScript de src/index.html."""
    block = re.search(r"var I18N = \{(.*?)\n  \};", src, re.S).group(1)
    out = {}
    for lang in LANGS:
        m = re.search(r"\n    " + lang + r": \{(.*?)\n    \}", block, re.S)
        body = m.group(1)
        d = {}
        pat = r"""'?([\w.]+)'?\s*:\s*(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")"""
        for k, v1, v2 in re.findall(pat, body):
            d[k] = re.sub(r"\\(.)", r"\1", v1 or v2)
        out[lang] = d
    return out


def replace_inner(doc: str, attr: str, key: str, new_inner: str) -> str:
    """Troca o conteúdo do elemento que tem attr="key", respeitando tags aninhadas."""
    m = re.search(r'<(\w+)\b[^>]*\b' + attr + r'="' + re.escape(key) + r'"[^>]*>', doc)
    if not m:
        return doc
    tag, start = m.group(1), m.end()
    depth, pos = 1, start
    tok = re.compile(r"<(/?)" + tag + r"\b[^>]*>")
    while depth:
        t = tok.search(doc, pos)
        depth += -1 if t.group(1) else 1
        pos = t.end()
    return doc[:start] + new_inner + doc[t.start():]


def render(src: str, lang: str, t: dict) -> str:
    doc = src
    path, locale = LANGS[lang]
    url = SITE + path
    esc = lambda s: html.escape(s, quote=True)

    # Textos
    for key in set(re.findall(r'data-i18n="([\w.]+)"', doc)):
        if key in t:
            doc = replace_inner(doc, "data-i18n", key, esc(t[key]).replace("&#x27;", "'"))
    for key in set(re.findall(r'data-i18n-html="([\w.]+)"', doc)):
        if key in t:
            doc = replace_inner(doc, "data-i18n-html", key, t[key])
    for m in set(re.findall(r'data-i18n-attr="(\w[\w-]*):([\w.]+)"', doc)):
        a, key = m
        doc = re.sub(r'(<[^>]*\b)' + a + r'="[^"]*"([^>]*data-i18n-attr="' + a + ":" + re.escape(key) + '")',
                     lambda mm: mm.group(1) + a + '="' + esc(t[key]) + '"' + mm.group(2), doc)

    # Botões de idioma
    def btn(m):
        b = m.group(0)
        pressed = "true" if m.group(1) == lang else "false"
        return re.sub(r'aria-pressed="\w+"', 'aria-pressed="' + pressed + '"', b)
    doc = re.sub(r'<button type="button" data-lang="(\w+)"[^>]*>', btn, doc)

    # WhatsApp com a mensagem no idioma da página
    wa = re.search(r"var WHATSAPP_NUMBER = '(\d+)'", doc).group(1)
    from urllib.parse import quote
    doc = re.sub(r'(id="wa-link" href=")[^"]*"',
                 lambda mm: mm.group(1) + esc("https://wa.me/" + wa + "?text=" + quote(t["contact.waMsg"])) + '"', doc)

    # <html>
    doc = re.sub(r'<html lang="[^"]*">', '<html lang="' + t["htmlLang"] + '" data-page-lang="' + lang + '">', doc, count=1)

    # <head>: título, descrição, Open Graph, canonical, hreflang, dados estruturados
    title, desc = t["meta.title"], t["meta.desc"]
    alternates = "\n".join(
        '<link rel="alternate" hreflang="%s" href="%s%s">' % (HREFLANG[l], SITE, LANGS[l][0]) for l in LANGS
    ) + '\n<link rel="alternate" hreflang="x-default" href="%s/">' % SITE
    ld = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "@id": SITE + "/#empresa",
        "name": BUSINESS["name"],
        "url": url,
        "logo": SITE + "/logo.png",
        "image": SITE + "/og-image.png",
        "description": desc,
        "telephone": BUSINESS["telephone"],
        "email": BUSINESS["email"],
        "foundingDate": BUSINESS["foundingDate"],
        "founder": {"@type": "Person", "name": BUSINESS["founder"]},
        "address": {"@type": "PostalAddress", "addressLocality": BUSINESS["city"],
                    "addressRegion": BUSINESS["region"], "addressCountry": BUSINESS["country"]},
        "areaServed": [{"@type": "Country", "name": "Brasil"}, {"@type": "Place", "name": "América Latina"}],
        "knowsLanguage": ["pt-BR", "en", "es"],
        "inLanguage": t["htmlLang"],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": BUSINESS["name"],
                            "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s}}
                                                for s in SERVICES[lang]]},
    }
    if BUSINESS["sameAs"]:
        ld["sameAs"] = BUSINESS["sameAs"]
    head = "\n".join([
        "<title>%s</title>" % esc(title),
        '<meta name="description" content="%s">' % esc(desc),
        '<meta name="robots" content="index,follow,max-image-preview:large">',
        '<link rel="canonical" href="%s">' % url,
        alternates,
        '<meta property="og:site_name" content="LB Horizon">',
        '<meta property="og:title" content="%s">' % esc(title),
        '<meta property="og:description" content="%s">' % esc(desc),
        '<meta property="og:type" content="website">',
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:locale" content="%s">' % locale,
        '<meta property="og:image" content="%s/og-image.png">' % SITE,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False),
    ])
    doc = re.sub(r"<title>.*?</title>\n", "", doc, count=1)
    doc = re.sub(r'<meta name="description"[^>]*>\n', "", doc, count=1)
    doc = re.sub(r'<meta property="og:[^>]*>\n', "", doc)
    doc = doc.replace('<meta name="viewport" content="width=device-width,initial-scale=1">',
                      '<meta name="viewport" content="width=device-width,initial-scale=1">\n' + head, 1)
    return ("<!-- Arquivo gerado por build.py a partir de src/index.html. Não edite aqui. -->\n" + doc)


def main():
    src = (ROOT / "src" / "index.html").read_text(encoding="utf-8")
    i18n = parse_i18n(src)
    for lang, (path, _) in LANGS.items():
        out = ROOT / path.strip("/") / "index.html" if path != "/" else ROOT / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(src, lang, i18n[lang]), encoding="utf-8")
        print("ok", out.relative_to(ROOT))

    today = datetime.date.today().isoformat()
    alts = "".join('\n    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>' % (HREFLANG[l], SITE, LANGS[l][0])
                   for l in LANGS)
    urls = "".join("\n  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>%s\n  </url>" % (SITE, p, today, alts)
                   for p, _ in LANGS.values())
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + urls + "\n</urlset>\n", encoding="utf-8")
    print("ok sitemap.xml")


if __name__ == "__main__":
    main()
