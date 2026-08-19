#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIR = ROOT / "papers"
SITE_DIR = ROOT / "site"
TUTORIAL_DIR = ROOT / "tutorials" / "ep03-neuron-3d"


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
    <nav class="topnav" aria-label="主要導覽">
      <a href="{prefix}index.html">學習路徑</a>
      <a href="{prefix}map.html">層級心智圖</a>
      <a href="{prefix}concepts.html">概念 Wiki</a>
      <a href="{prefix}papers.html">論文目錄</a>
      <a href="{prefix}tutorials.html">實作教材</a>
    </nav>"""
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · FlyCircuit 學習系統</title>
  <link rel="stylesheet" href="{prefix}assets/style.css?v=20260819-ui2">
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要內容</a>
  <header class="site-header"><a href="{prefix}index.html">FlyCircuit Connectomics 學習系統</a></header>
  {nav}
  <main id="main-content" tabindex="-1">{body}</main>
  <footer>由結構化論文資料自動建置 · 原始 PDF 保持唯讀</footer>
  <script src="{prefix}assets/app.js?v=20260819-ui2"></script>
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
    practice = ""
    if meta["id"] == "chiang-2011-flycircuit":
        practice = """
      <section class="practice-link">
        <p class="eyebrow">從論文走向資料實作</p>
        <h2>將神經影像視覺化</h2>
        <p>使用 FlyCircuit 單神經元 AmiraMesh 體積影像，實作 HxZip 解碼、NumPy 三維陣列、最大強度投影與旋轉動畫。</p>
        <a class="button-link" href="../tutorials/neuron-visualization.html">進入實作教材 →</a>
      </section>"""
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
      {practice}
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
        <a href="tutorials.html"><strong>我要動手做</strong><span>進入實作教材</span></a>
      </div>
    </section>
    <section id="learning">
      <h2>第一條學習路徑</h2>
      <p>這不是兩篇互不相干的摘要。2011 建立資料與空間架構；2015 將它轉成有方向、有權重的網路。</p>
      <div class="learning-path">{''.join(steps)}</div>
      <div class="next-module">
        <strong>實作教材已開始</strong>
        <p><a href="tutorials/neuron-visualization.html">將神經影像視覺化</a>：從 AmiraMesh 體積影像到 NumPy、三視圖與 3D 旋轉動畫。</p>
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


def build_tutorials_index():
    body = """
    <h1>實作教材</h1>
    <p>把論文中的資料、方法與限制轉成可重複執行的 Python 實驗；每個單元保留程式、驗證方式與解讀界線。</p>
    <div class="tutorial-list">
      <article class="tutorial-card">
        <p class="eyebrow">神經影像 · Python · 3D</p>
        <h2><a href="tutorials/neuron-visualization.html">將神經影像視覺化</a></h2>
        <p>讀取 20 個 FlyCircuit AmiraMesh 單神經元體積影像，完成 HxZip 解碼、資料勘查、最大強度投影與旋轉動畫。</p>
        <div class="tags"><span>AmiraMesh</span><span>NumPy</span><span>MIP</span><span>點雲旋轉</span></div>
      </article>
      <article class="tutorial-card planned">
        <p class="eyebrow">規劃中</p>
        <h2>從 connectivity matrix 到網路性質</h2>
        <p>以小型矩陣重現 degree／strength、modularity、small-world 與 rich-club 的基本概念。</p>
      </article>
    </div>"""
    return page("實作教材", body)


def build_neuron_visualization():
    examples = [
        {
            "id": "TH-F-000020",
            "driver": "TH",
            "meaning": "多巴胺能",
            "sex": "雌性",
            "range": "0–4095",
            "nonzero": "333,141（2.308%）",
            "panel": "TH-F-000020-three-views.png",
            "panel_size": (2007, 713),
            "spin": "TH-F-000020-spin.webp",
            "spin_size": (314, 296),
            "note": "示範密集分枝、細胞本體與長程延伸在三個正交方向的差異。",
        },
        {
            "id": "Tdc2-F-000001",
            "driver": "Tdc2",
            "meaning": "章魚胺／酪胺能",
            "sex": "雌性",
            "range": "0–255",
            "nonzero": "404,585（1.354%）",
            "panel": "Tdc2-F-000001-three-views.png",
            "panel_size": (2064, 708),
            "spin": "Tdc2-F-000001-spin.webp",
            "spin_size": (445, 371),
            "note": "呈現較寬廣的雙側延伸，適合觀察旋轉時前後分枝如何分離。",
        },
        {
            "id": "Trh-M-100072",
            "driver": "Trh",
            "meaning": "血清素能",
            "sex": "雄性",
            "range": "0–4095",
            "nonzero": "313,703（1.737%）",
            "panel": "Trh-M-100072-three-views.png",
            "panel_size": (1916, 713),
            "spin": "Trh-M-100072-spin.webp",
            "spin_size": (256, 324),
            "note": "本批資料唯一的雄性樣本；用於展示細長垂直形態在不同投影方向的差異。",
        },
        {
            "id": "VGlut-F-300388",
            "driver": "VGlut",
            "meaning": "麩胺酸能",
            "sex": "雌性",
            "range": "0–255",
            "nonzero": "325,836（0.523%）",
            "panel": "VGlut-F-300388-three-views.png",
            "panel_size": (2064, 566),
            "spin": "VGlut-F-300388-spin.webp",
            "spin_size": (842, 307),
            "note": "示範跨越寬廣 X 範圍的形態，也說明 255 與 4095 資料需要各自正規化。",
        },
        {
            "id": "Gad1-F-400376",
            "driver": "Gad1",
            "meaning": "GABA 能",
            "sex": "雌性",
            "range": "0–4095",
            "nonzero": "335,678（3.400%）",
            "panel": "Gad1-F-400376-three-views.png",
            "panel_size": (2050, 713),
            "spin": "Gad1-F-400376-spin.webp",
            "spin_size": (298, 277),
            "note": "呈現較緊密的中央分枝，與長距離延伸型神經元形成形態對照。",
        },
        {
            "id": "fru-F-900054",
            "driver": "fru",
            "meaning": "fruitless 表現神經元",
            "sex": "雌性",
            "range": "0–4095",
            "nonzero": "357,176（4.179%）",
            "panel": "fru-F-900054-three-views.png",
            "panel_size": (1874, 713),
            "spin": "fru-F-900054-spin.webp",
            "spin_size": (212, 303),
            "note": "本批資料非零 voxel 比例最高，顯示集中且細長的分枝形態。",
        },
    ]
    cards = []
    for item in examples:
        spin = ""
        if item["spin"]:
            spin = f"""
          <figure class="tutorial-media spin-media">
            <button class="media-zoom" type="button" aria-label="放大 {item['id']} 繞 Y 軸旋轉動畫" style="--spin-aspect:{item['spin_size'][0]} / {item['spin_size'][1]};--spin-mobile-width:{min(260, round(280 * item['spin_size'][0] / item['spin_size'][1], 2))}px">
              <img src="assets/{item['spin']}" alt="{item['id']} 繞 Y 軸旋轉動畫" loading="lazy" width="{item['spin_size'][0]}" height="{item['spin_size'][1]}">
            </button>
            <figcaption>36 格灰階旋轉動畫；亮度只表示 voxel 強度。</figcaption>
          </figure>"""
        cards.append(f"""
      <article class="neuron-example" id="result-{item['driver'].lower()}" style="--driver-color:var(--driver-{item['driver'].lower()})">
        <div class="example-head">
          <div>
            <p class="driver-name"><span class="driver-tag">{item['driver']}</span><strong>{item['meaning']}</strong></p>
            <h3>{item['id']}</h3>
          </div>
          <p>{item['sex']} · 強度 {item['range']} · 非零 voxel {item['nonzero']}</p>
        </div>
        <p>{item['note']}</p>
        <div class="example-media">
          {spin}
          <figure class="tutorial-media">
            <button class="media-zoom" type="button" aria-label="放大 {item['id']} XY、XZ、ZY 三視圖">
              <img src="assets/{item['panel']}" alt="{item['id']} XY、XZ、ZY 三視圖" loading="lazy" width="{item['panel_size'][0]}" height="{item['panel_size'][1]}">
            </button>
            <figcaption>XY、XZ、ZY 最大強度投影（MIP）。</figcaption>
          </figure>
        </div>
      </article>""")

    body = f"""
    <article class="tutorial-page">
      <p class="eyebrow"><a href="../tutorials.html">實作教材</a> · 神經影像</p>
      <h1>將神經影像視覺化</h1>
      <p class="lead">從 20 個陌生的 FlyCircuit <code>.am</code> 檔開始，確認格式、解開 HxZip、還原 NumPy 三維陣列，再產生三視圖與旋轉動畫。</p>

      <section class="result-summary">
        <div><strong>20</strong><span>單神經元影像</span></div>
        <div><strong>6</strong><span>driver line</span></div>
        <div><strong>60</strong><span>MIP 投影</span></div>
        <div><strong>20</strong><span>旋轉動畫</span></div>
      </section>

      <section class="reading-content">
        <h2>這次做了什麼？</h2>
        <p>原始檔是 AmiraMesh 3D 灰階體積：純文字檔頭加上 HxZip 壓縮的 16-bit <code>ushort</code> 資料。自行撰寫的 <code>amread.py</code> 會解析尺寸與 BoundingBox、使用 zlib 解壓，並以檔頭尺寸交叉驗證解壓位元組數。</p>
        <p>20 個檔案只有約 0.46%–4.18% voxel 非零，因此投影採最大強度投影（Maximum Intensity Projection, MIP），旋轉則只處理非零 voxel 組成的稀疏點雲。</p>

        <h2>強度如何顯示？</h2>
        <p>部分檔案的觀察值範圍是 0–255，部分是 0–4095；它們都存放在 16-bit 容器中。為了比較形態而非絕對亮度，每個影像以自身非零值的第 99.5 百分位作為白點，再以 gamma 0.5 顯示較弱細枝。</p>
        <p class="boundary"><strong>解讀界線：</strong>voxel 強度是影像灰階值，不是突觸數、神經活動或連線權重。不同檔案經個別正規化後適合比較形態，不適合比較絕對訊號強弱。</p>

        <h2>三視圖與旋轉動畫</h2>
        <p>XY 沿 Z 軸取最大值，XZ 沿 Y 軸，ZY 沿 X 軸。靜態 MIP 會失去深度；旋轉動畫則利用運動視差讓人眼重新感受到前後關係。正式動畫採黑底灰階，driver line 顏色只出現在分類標籤與邊框，不賦予影像不存在的生物意義。</p>
      </section>

      <section>
        <h2>六類代表成果</h2>
        <p>每個 driver line 選一條神經元，先看「標記所關聯的神經傳遞表型」，再比較旋轉動畫與三視圖。這些名稱是遺傳標記分類，<strong>不是神經元所在的解剖腦區</strong>。</p>
        <nav class="result-jumps" aria-label="六類神經元成果">
          {''.join(f'<a href="#result-{item["driver"].lower()}">{item["driver"]}｜{item["meaning"]}</a>' for item in examples)}
        </nav>
        {''.join(cards)}
        <p class="result-scope">公開頁呈現六類代表樣本；完整 20 條旋轉動畫、60 張投影、原始影像、程式與開發紀錄仍保留於本機工作區。</p>
      </section>

      <section class="reading-content">
        <h2>與 2011 論文的關係</h2>
        <p>Chiang et al. (2011) 建立 FlyCircuit 單神經元影像、標準腦與影像配準架構；這個實作直接操作已 warp 的單神經元體積，將「共同座標中的神經元影像」從論文概念變成可讀、可驗證的資料處理流程。</p>
        <p><a class="button-link" href="../papers/chiang-2011-flycircuit.html">回到 2011 核心論文 →</a></p>
      </section>
    </article>"""
    return page("將神經影像視覺化", body, depth=1)


def main():
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "papers").mkdir(exist_ok=True)
    (SITE_DIR / "assets").mkdir(exist_ok=True)
    (SITE_DIR / "tutorials").mkdir(exist_ok=True)
    (SITE_DIR / "tutorials" / "assets").mkdir(exist_ok=True)
    types = load_json(ROOT / "config" / "knowledge-types.json")
    type_map = {x["id"]: x for x in types["types"]}
    confidence_map = types["confidence"]
    papers = load_papers()

    (SITE_DIR / "index.html").write_text(build_index(papers), encoding="utf-8")
    (SITE_DIR / "papers.html").write_text(build_papers_page(papers), encoding="utf-8")
    (SITE_DIR / "concepts.html").write_text(build_concepts(papers, type_map), encoding="utf-8")
    (SITE_DIR / "map.html").write_text(build_map(papers, type_map), encoding="utf-8")
    (SITE_DIR / "tutorials.html").write_text(build_tutorials_index(), encoding="utf-8")
    (SITE_DIR / "tutorials" / "neuron-visualization.html").write_text(
        build_neuron_visualization(), encoding="utf-8"
    )
    for paper in papers:
        output = SITE_DIR / "papers" / f"{paper['meta']['id']}.html"
        output.write_text(build_paper(paper, type_map, confidence_map), encoding="utf-8")

    for asset in (ROOT / "assets").iterdir():
        if asset.is_file():
            (SITE_DIR / "assets" / asset.name).write_bytes(asset.read_bytes())
    public_assets = TUTORIAL_DIR / "public-assets"
    for asset in public_assets.iterdir():
        if asset.is_file():
            shutil.copy2(asset, SITE_DIR / "tutorials" / "assets" / asset.name)
    print(
        f"Built {len(papers)} papers, {sum(len(p['claims']) for p in papers)} knowledge nodes, "
        f"and 1 tutorial in {SITE_DIR}"
    )


if __name__ == "__main__":
    main()
