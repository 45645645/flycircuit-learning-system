#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIR = ROOT / "papers"
SITE_DIR = ROOT / "site"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def markdown_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph():
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_paragraph()
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(heading.group(1))
            title = heading.group(2)
            anchor = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", title.lower()).strip("-")
            out.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
        elif line.startswith("- "):
            flush_paragraph()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + inline(line[2:]) + "</li>")
        else:
            paragraph.append(line)
    flush_paragraph()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def page(title: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    nav = f"""
    <nav class="topnav">
      <a href="{prefix}index.html">學習路徑</a>
      <a href="{prefix}map.html">層級心智圖</a>
      <a href="{prefix}concepts.html">概念 Wiki</a>
      <a href="{prefix}papers.html">論文目錄</a>
    </nav>"""
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · FlyCircuit 學習系統</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
  <header class="site-header"><a href="{prefix}index.html">FlyCircuit Connectomics 學習系統</a></header>
  {nav}
  <main>{body}</main>
  <footer>由結構化論文資料自動建置 · 原始 PDF 保持唯讀</footer>
  <script src="{prefix}assets/app.js"></script>
</body>
</html>"""


def source_label(source: dict) -> str:
    parts = []
    if source.get("pdf_page"):
        parts.append(f'PDF p. {source["pdf_page"]}')
    if source.get("section"):
        parts.append(source["section"])
    if source.get("figure"):
        parts.append(source["figure"])
    return " · ".join(parts)


def load_papers():
    papers = []
    for folder in PAPERS_DIR.iterdir():
        if not folder.is_dir():
            continue
        meta = load_json(folder / "meta.json")
        claims = load_json(folder / "claims.json")["nodes"]
        content = (folder / "content.md").read_text(encoding="utf-8")
        papers.append({"folder": folder, "meta": meta, "claims": claims, "content": content})
    return sorted(papers, key=lambda p: p["meta"]["learning_order"])


def build_paper(paper, type_map, confidence_map):
    meta = paper["meta"]
    claim_cards = []
    for node in paper["claims"]:
        type_info = type_map[node["type"]]
        deps = "".join(f'<li><a href="../map.html#{html.escape(dep)}">{html.escape(dep)}</a></li>' for dep in node.get("depends_on", []))
        dep_block = f'<details><summary>依賴節點</summary><ul>{deps}</ul></details>' if deps else ""
        claim_cards.append(f"""
        <article class="claim-card" id="{html.escape(node['id'])}" style="--type-color:{type_info['color']}">
          <div class="claim-type">{type_info['zh']} · {type_info['en']}</div>
          <h3>{html.escape(node['title_zh'])}</h3>
          <p class="term-en">{html.escape(node['title_en'])}</p>
          <p>{html.escape(node['statement'])}</p>
          <p class="source">來源：{html.escape(source_label(node['source']))}</p>
          <p class="confidence">標記：{html.escape(confidence_map[node['confidence']])}</p>
          {dep_block}
        </article>""")
    tags = "".join(f"<span>{html.escape(x)}</span>" for x in meta["keywords"])
    # application/json 內容必須保留為合法 JSON；只處理可能提前結束 script 的字串。
    metadata = json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")
    body = f"""
    <article class="paper-page">
      <div class="eyebrow">核心論文 · 學習順序 {meta['learning_order']}</div>
      <h1>{html.escape(meta['title_zh'])}</h1>
      <p class="paper-title-en">{html.escape(meta['title'])}</p>
      <div class="paper-facts">
        <span>{meta['year']}</span><span>{html.escape(meta['venue'])}</span>
        <a href="https://doi.org/{html.escape(meta['doi'])}">DOI</a>
      </div>
      <div class="tags">{tags}</div>
      <section class="reading-content">{markdown_to_html(paper['content'])}</section>
      <section>
        <h2>結構化知識節點</h2>
        <p>以下節點用來產生心智圖及依賴關係。每個節點都保留來源與判讀層級。</p>
        <div class="claim-grid">{''.join(claim_cards)}</div>
      </section>
      <script type="application/json" id="paper-meta">{metadata}</script>
    </article>"""
    return page(meta["title_zh"], body, depth=1)


def build_index(papers):
    steps = []
    for paper in papers:
        meta = paper["meta"]
        steps.append(f"""
        <a class="learning-step" href="papers/{meta['id']}.html">
          <span class="step-number">{meta['learning_order']}</span>
          <span><strong>{meta['year']} · {html.escape(meta['title_zh'])}</strong><small>{html.escape(meta['title'])}</small></span>
        </a>""")
    body = f"""
    <section class="hero">
      <p class="eyebrow">個人開發中的 pilot · v0.1 · 兩篇 Current Biology 核心論文</p>
      <h1>從單神經元影像到果蠅腦資訊流</h1>
      <p>先沿著學習路徑理解研究如何建立，再用概念 Wiki 查名詞、用心智圖追蹤知識依賴、用論文頁回到證據。</p>
      <div class="entry-grid">
        <a href="#learning"><strong>我是新手</strong><span>從學習路徑開始</span></a>
        <a href="concepts.html"><strong>我要查概念</strong><span>進入概念 Wiki</span></a>
        <a href="papers.html"><strong>我要找來源</strong><span>進入論文目錄</span></a>
        <a href="map.html"><strong>我要看結構</strong><span>打開層級心智圖</span></a>
      </div>
    </section>
    <section id="learning">
      <h2>第一條學習路徑</h2>
      <p>這不是兩篇互不相干的摘要。2011 建立資料與空間架構；2015 將它轉成有方向、有權重的網路。</p>
      <div class="learning-path">{''.join(steps)}</div>
      <div class="next-module">
        <strong>下一個教材單元</strong>
        <p>以小型 connectivity matrix 重現 degree／strength、modularity、small-world 與 rich-club 的基本概念。</p>
      </div>
    </section>"""
    return page("學習路徑", body)


def build_papers_page(papers):
    cards = []
    for paper in papers:
        meta = paper["meta"]
        search = " ".join([meta["title"], meta["title_zh"], meta["authors_short"], *meta["keywords"], *meta["methods"]])
        cards.append(f"""
        <article class="paper-card" data-search="{html.escape(search.lower())}">
          <p class="eyebrow">{meta['year']} · {html.escape(meta['venue'])}</p>
          <h2><a href="papers/{meta['id']}.html">{html.escape(meta['title_zh'])}</a></h2>
          <p>{html.escape(meta['authors_short'])}</p>
          <p class="paper-title-en">{html.escape(meta['title'])}</p>
        </article>""")
    body = f"""
    <h1>論文目錄</h1>
    <p>目前先收錄兩篇核心論文；其餘四篇會在資料結構確認後加入。</p>
    <label class="search-label">搜尋論文、方法或關鍵字<input id="paper-search" type="search" placeholder="例如：LPU、registration、rich club"></label>
    <div class="paper-list">{''.join(cards)}</div>"""
    return page("論文目錄", body)


def build_concepts(papers, type_map):
    nodes = [node for p in papers for node in p["claims"]]
    cards = []
    for node in nodes:
        t = type_map[node["type"]]
        cards.append(f"""
        <article class="concept-card" data-type="{node['type']}" style="--type-color:{t['color']}">
          <div class="claim-type">{t['zh']} · {t['en']}</div>
          <h2><a href="map.html#{node['id']}">{html.escape(node['title_zh'])}</a></h2>
          <p class="term-en">{html.escape(node['title_en'])}</p>
          <p>{html.escape(node['statement'])}</p>
        </article>""")
    body = f"""
    <h1>概念 Wiki</h1>
    <p>第一版以論文中的 Definition、Assumption、Method、Construction、Result、Property、Claim 與 Limitation 為主要條目。</p>
    <div class="concept-grid">{''.join(cards)}</div>"""
    return page("概念 Wiki", body)


def build_map(papers, type_map):
    all_nodes = {node["id"]: node for p in papers for node in p["claims"]}
    paper_for_node = {node["id"]: p["meta"]["id"] for p in papers for node in p["claims"]}
    levels: dict[int, list[dict]] = {}

    def depth(node_id, active=None):
        active = set(active or [])
        if node_id in active:
            return 0
        active.add(node_id)
        deps = [d for d in all_nodes[node_id].get("depends_on", []) if d in all_nodes]
        return 0 if not deps else 1 + max(depth(d, active) for d in deps)

    for node_id, node in all_nodes.items():
        levels.setdefault(depth(node_id), []).append(node)
    sections = []
    for level in sorted(levels):
        cards = []
        for node in levels[level]:
            t = type_map[node["type"]]
            deps = ", ".join(all_nodes[d]["title_zh"] for d in node.get("depends_on", []) if d in all_nodes) or "起點節點"
            cards.append(f"""
            <article class="map-node" id="{node['id']}" style="--type-color:{t['color']}">
              <span>{t['zh']}</span>
              <h3>{html.escape(node['title_zh'])}</h3>
              <p class="term-en">{html.escape(node['title_en'])}</p>
              <p>{html.escape(node['statement'])}</p>
              <small>依賴：{html.escape(deps)}</small>
              <a href="papers/{paper_for_node[node['id']]}.html#{node['id']}">查看來源定位</a>
            </article>""")
        sections.append(f'<section class="map-level"><h2>層級 {level}</h2><div>{"".join(cards)}</div></section>')
    legend = "".join(f'<span style="--type-color:{t["color"]}">{t["zh"]}</span>' for t in type_map.values())
    body = f"""
    <h1>知識依賴心智圖</h1>
    <p>由下往上閱讀：定義、假設與方法形成建構；建構支持結果與性質；結果再支持資訊流主張。紅色限制節點提醒哪些地方不能過度解讀。</p>
    <div class="legend">{legend}</div>
    <div class="map-board">{''.join(sections)}</div>"""
    return page("層級心智圖", body)


def main():
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "papers").mkdir(exist_ok=True)
    (SITE_DIR / "assets").mkdir(exist_ok=True)
    types = load_json(ROOT / "config" / "knowledge-types.json")
    type_map = {x["id"]: x for x in types["types"]}
    confidence_map = types["confidence"]
    papers = load_papers()

    (SITE_DIR / "index.html").write_text(build_index(papers), encoding="utf-8")
    (SITE_DIR / "papers.html").write_text(build_papers_page(papers), encoding="utf-8")
    (SITE_DIR / "concepts.html").write_text(build_concepts(papers, type_map), encoding="utf-8")
    (SITE_DIR / "map.html").write_text(build_map(papers, type_map), encoding="utf-8")
    for paper in papers:
        output = SITE_DIR / "papers" / f"{paper['meta']['id']}.html"
        output.write_text(build_paper(paper, type_map, confidence_map), encoding="utf-8")

    for asset in (ROOT / "assets").iterdir():
        if asset.is_file():
            (SITE_DIR / "assets" / asset.name).write_bytes(asset.read_bytes())
    print(f"Built {len(papers)} papers and {sum(len(p['claims']) for p in papers)} knowledge nodes in {SITE_DIR}")


if __name__ == "__main__":
    main()
