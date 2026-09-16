#!/usr/bin/env python3
"""============================================
   圣链健康 — 文章构建脚本
   用法: python3 build-articles.py
   功能: 扫描 articles/*.md → 生成 js/articles-data.js
   ============================================"""

import os
import glob
import yaml
import markdown
import re

ARTICLES_DIR = os.path.join(os.path.dirname(__file__), 'articles')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'js', 'articles-data.js')
CONSULTATION_DIR = os.path.join(os.path.dirname(__file__), 'consultation')
CASES_HTML_FILE = os.path.join(os.path.dirname(__file__), 'cases.html')
SITE_URL = 'https://www.arkecthealth.com'

def parse_frontmatter(text):
    """解析 YAML frontmatter，返回 (metadata_dict, body_text)"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    if not match:
        raise ValueError('缺少 YAML frontmatter (需以 --- 包裹)')
    meta = yaml.safe_load(match.group(1))
    body = match.group(2)
    return meta, body

def md_to_html(md_text):
    """Markdown → HTML（自动透传已有 HTML 标签）"""
    return markdown.markdown(
        md_text,
        extensions=['extra', 'nl2br'],
        output_format='html5'
    )

def estimate_read_time(content_html):
    """根据 HTML 内容估算阅读时长（分钟）"""
    text = re.sub(r'<[^>]*>', '', content_html)
    return max(1, round(len(text) / 400))

def extract_toc(content_html):
    """从 HTML 中提取 h2 标签生成 TOC 列表"""
    headings = re.findall(r'<h2[^>]*>(.*?)</h2>', content_html)
    toc = []
    for i, h in enumerate(headings):
        text = re.sub(r'<[^>]*>', '', h).strip()
        slug = 'toc-' + re.sub(r'[^\w]+', '-', text).lower().strip('-')
        toc.append({'text': text, 'slug': slug})
    return toc

def add_toc_ids(content_html, toc):
    """给 h2 标签添加 id 属性用于锚点跳转"""
    for item in toc:
        plain = re.escape(re.sub(r'<[^>]*>', '', item['text']).strip())
        content_html = re.sub(
            r'(<h2)([^>]*>)(' + plain + r')',
            r'\1 id="' + item['slug'] + r'"\2\3',
            content_html, count=1
        )
    return content_html

def generate_article_pages(articles):
    """为每篇文章生成独立 SEO 静态页面 → consultation/[id].html"""
    os.makedirs(CONSULTATION_DIR, exist_ok=True)

    # 按分类分组，按日期排序
    by_category = {}
    for a in articles:
        cat = a['category']
        by_category.setdefault(cat, []).append(a)
    for cat in by_category:
        by_category[cat].sort(key=lambda x: x['date'])

    for a in articles:
        toc = extract_toc(a['content_html'])
        body_html = add_toc_ids(a['content_html'], toc) if toc else a['content_html']
        read_time = estimate_read_time(a['content_html'])

        # 上一篇 / 下一篇（同分类）
        cat_list = by_category.get(a['category'], [])
        idx = next((i for i, x in enumerate(cat_list) if x['id'] == a['id']), -1)
        prev_a = cat_list[idx - 1] if idx > 0 else None
        next_a = cat_list[idx + 1] if idx < len(cat_list) - 1 else None

        # 相关推荐（同分类，排除自身，最多 3 篇）
        related = [x for x in cat_list if x['id'] != a['id']][:3]

        html = build_article_html(a, toc, body_html, read_time, prev_a, next_a, related)

        out_path = os.path.join(CONSULTATION_DIR, a['id'] + '.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)

    print(f'✅ {len(articles)} 篇详情页 → consultation/')


def build_article_head(a):
    """生成详情页 <head> 中的 SEO 标签"""
    json_ld = (
        '{"@context":"https://schema.org","@type":"Article",'
        f'"headline":"{a["title"]}","datePublished":"{a["date"]}",'
        f'"description":"{a["summary"]}",'
        f'"author":{{"@type":"Organization","name":"{a["author"] or "圣链健康"}"}},'
        f'"publisher":{{"@type":"Organization","name":"圣链健康","url":"{SITE_URL}"}}}}'
    )
    return f'''  <title>{a["title"]} — 圣链健康</title>
  <meta name="description" content="{a["summary"]}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{a["title"]}">
  <meta property="og:description" content="{a["summary"]}">
  <meta property="og:url" content="{SITE_URL}/consultation/{a["id"]}.html">
  <meta property="og:site_name" content="圣链健康">
  <meta property="article:published_time" content="{a["date"]}">
  <link rel="canonical" href="{SITE_URL}/consultation/{a["id"]}.html">
  <script type="application/ld+json">{json_ld}</script>'''


def build_article_html(a, toc, body_html, read_time, prev_a, next_a, related):
    """为单篇文章生成完整 HTML 页面"""
    toc_html = ''
    if toc:
        items = '\n'.join(f'<li><a href="#{t["slug"]}">{t["text"]}</a></li>' for t in toc)
        toc_html = f'<nav class="article-toc"><h4>目录</h4><ul>{items}</ul></nav>'
    nav_html = ''
    if prev_a or next_a:
        prev_h = f'<a class="nav-prev" href="{prev_a["id"]}.html"><span class="nav-label">上一篇</span><span class="nav-title">{prev_a["title"]}</span></a>' if prev_a else ''
        next_h = f'<a class="nav-next" href="{next_a["id"]}.html"><span class="nav-label">下一篇</span><span class="nav-title">{next_a["title"]}</span></a>' if next_a else ''
        nav_html = f'<div class="article-nav">{prev_h}{next_h}</div>'
    related_html = ''
    if related:
        cards = ''
        for r in related:
            rt = estimate_read_time(r['content_html'])
            cards += f'<a class="related-card" href="{r["id"]}.html"><span class="related-card-cat">{r["category"]}</span><h4>{r["title"]}</h4><p class="related-card-excerpt">{r["summary"]}</p><span class="related-card-meta">{r["date"]} · 约 {rt} 分钟</span></a>'
        related_html = f'<div class="article-related"><h3>相关推荐</h3><div class="related-grid">{cards}</div></div>'
    head_seo = build_article_head(a)
    back_href = '../case-studies/index.html#' + a['category']
    author_str = a.get('author') or ''
    author_dot = '<span class="dot"></span><span>' + author_str + '</span>' if author_str else ''
    return _article_page_template(a, toc_html, body_html, read_time, nav_html, related_html, head_seo, back_href, author_dot)


def _article_css():
    """文章详情页内联 CSS"""
    return """
    .page-hero{position:relative;min-height:30vh;display:flex;align-items:center;background:var(--color-primary);overflow:hidden;padding-top:80px}
    .page-hero-bg{position:absolute;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,rgba(10,22,40,.93),rgba(10,22,40,.72) 50%,rgba(10,22,40,.88));z-index:1}
    .page-hero-content{position:relative;z-index:3;max-width:720px;padding:var(--spacing-2xl) 0}
    .breadcrumb{padding:var(--spacing-sm) 0;font-size:.82rem}
    .breadcrumb a{color:rgba(255,255,255,.5)}.breadcrumb a:hover{color:var(--color-gold)}
    .breadcrumb span{color:rgba(255,255,255,.3);margin:0 8px}
    .breadcrumb .current{color:var(--color-gold)}
    .article-detail{max-width:780px;margin:0 auto;padding:var(--spacing-2xl) 0}
    .article-detail h1{font-size:2rem;color:var(--color-primary);margin-bottom:var(--spacing-md);line-height:1.5}
    .article-meta{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-bottom:var(--spacing-xl);padding-bottom:var(--spacing-md);border-bottom:1px solid var(--color-gray-light)}
    .article-meta-tag{display:inline-block;padding:6px 16px;background:rgba(201,169,110,.1);color:var(--color-gold);border-radius:20px;font-size:.82rem;font-weight:500}
    .article-meta-info{font-size:.88rem;color:var(--color-gray)}
    .article-meta-info .dot{display:inline-block;width:3px;height:3px;border-radius:50%;background:var(--color-gray);margin:0 8px;vertical-align:middle}
    .article-body{font-size:1.05rem;line-height:2;color:var(--color-text)}
    .article-body h2{font-size:1.4rem;color:var(--color-primary);margin:var(--spacing-lg) 0 var(--spacing-sm);padding-left:16px;border-left:3px solid var(--color-gold)}
    .article-body p{margin-bottom:var(--spacing-sm)}
    .article-body strong{color:var(--color-primary)}
    .article-body ul,.article-body ol{margin:var(--spacing-sm) 0;padding-left:var(--spacing-lg)}
    .article-body li{margin-bottom:8px;line-height:1.9}
    .article-toc{background:var(--color-off-white);border:1px solid var(--color-gray-light);border-radius:var(--border-radius-lg);padding:var(--spacing-md) var(--spacing-lg);margin-bottom:var(--spacing-xl)}
    .article-toc h4{font-size:.88rem;color:var(--color-gold);letter-spacing:2px;margin-bottom:12px;text-transform:uppercase}
    .article-toc ul{list-style:none;padding:0}
    .article-toc li{margin-bottom:8px}
    .article-toc a{font-size:.92rem;color:var(--color-text-light);text-decoration:none;transition:var(--transition)}
    .article-toc a:hover{color:var(--color-gold)}
    .article-share{display:flex;align-items:center;gap:12px;margin:var(--spacing-xl) 0;padding:var(--spacing-md) 0;border-top:1px solid var(--color-gray-light);border-bottom:1px solid var(--color-gray-light)}
    .share-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 20px;border:1px solid var(--color-gray-light);border-radius:40px;font-size:.88rem;color:var(--color-text-light);cursor:pointer;transition:var(--transition);background:transparent}
    .share-btn:hover{border-color:var(--color-gold);color:var(--color-gold)}
    .article-nav{display:flex;justify-content:space-between;gap:var(--spacing-lg);margin:var(--spacing-2xl) 0;padding-top:var(--spacing-xl);border-top:1px solid var(--color-gray-light)}
    .nav-prev,.nav-next{display:flex;flex-direction:column;gap:6px;text-decoration:none;max-width:45%}
    .nav-next{text-align:right;margin-left:auto}
    .nav-label{font-size:.82rem;color:var(--color-gold);letter-spacing:1px}
    .nav-title{font-size:.95rem;color:var(--color-primary);line-height:1.5}
    .nav-prev:hover .nav-title,.nav-next:hover .nav-title{color:var(--color-gold)}
    .article-related{margin:var(--spacing-2xl) 0;padding-top:var(--spacing-xl);border-top:1px solid var(--color-gray-light)}
    .article-related h3{font-size:1.3rem;margin-bottom:var(--spacing-lg)}
    .related-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:var(--spacing-md)}
    .related-card{display:flex;flex-direction:column;padding:var(--spacing-md);border:1px solid var(--color-gray-light);border-radius:var(--border-radius-lg);text-decoration:none;transition:var(--transition)}
    .related-card:hover{border-color:rgba(201,169,110,.4);box-shadow:var(--shadow-sm)}
    .related-card-cat{font-size:.78rem;color:var(--color-gold);letter-spacing:1px;margin-bottom:8px}
    .related-card h4{font-size:1rem;color:var(--color-primary);margin-bottom:8px;line-height:1.4}
    .related-card-excerpt{font-size:.85rem;color:var(--color-text-light);line-height:1.7;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-bottom:8px}
    .related-card-meta{font-size:.8rem;color:var(--color-gray);margin-top:auto}
    .article-back{display:inline-flex;align-items:center;gap:8px;margin-top:var(--spacing-xl);padding:12px 32px;border:1px solid var(--color-gray-light);border-radius:40px;color:var(--color-text-light);font-weight:500;transition:var(--transition);text-decoration:none}
    .article-back:hover{border-color:var(--color-gold);color:var(--color-gold)}
    @media(max-width:768px){.article-detail h1{font-size:1.6rem}.page-hero{min-height:20vh}.article-nav{flex-direction:column}.nav-next{text-align:left;margin-left:0}.related-grid{grid-template-columns:1fr}}
    """


def _article_page_template(a, toc_html, body_html, read_time, nav_html, related_html, head_seo, back_href, author_dot):
    """文章详情页 HTML 模板（由 build_article_html 调用）"""
    css = _article_css()
    head = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
{head_seo}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <style>{css}  </style>
</head>
<body>
  <nav class="navbar" data-transparent>
    <div class="container">
      <a href="../index.html" class="nav-logo">
        <div class="logo-icon">A</div>
        <div class="logo-text">
          <span class="brand-en">ARKECT HEALTH</span>
          <span class="brand-cn">圣链健康</span>
        </div>
      </a>
      <div class="nav-links">
        <a href="../index.html">首页</a><a href="../about.html">关于我们</a>
        <div class="nav-dropdown"><a href="../services.html">我们的服务</a><div class="dropdown-menu"><a href="../service-chronic.html">高端慢病管理</a><a href="../service-private.html">皇家私人医生</a><a href="../service-checkup.html">个性化体检</a><a href="../service-student.html">留学生健康管家</a><a href="../service-uk-treatment.html">赴英看病</a><a href="../service-remote.html">远程问诊</a></div></div>
        <a href="../resources.html">医疗资源</a><a href="../cases.html" class="active">资讯分享</a><a href="../process.html">问诊流程</a><a href="../contact.html" class="btn btn-primary btn-sm nav-cta">预约咨询</a><a href="../en/index.html" class="nav-lang">🇬🇧 EN</a>
      </div>
      <div class="nav-toggle"><span></span><span></span><span></span></div>
    </div>
  </nav>"""
    return head + _tpl_body(a, toc_html, body_html, read_time, nav_html, related_html, back_href, author_dot) + _tpl_foot()


def _tpl_body(a, toc_html, body_html, read_time, nav_html, related_html, back_href, author_dot):
    """文章正文区域（hero + article content）"""
    return f"""
  <section class="page-hero">
    <div class="page-hero-bg"></div>
    <div class="container">
      <div class="page-hero-content">
        <div class="breadcrumb"><a href="../index.html">首页</a><span>›</span><a href="../cases.html">资讯分享</a><span>›</span><span class="current">{a["title"]}</span></div>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="container">
      <div class="article-detail">
        <h1>{a["title"]}</h1>
        <div class="article-meta">
          <span class="article-meta-tag">{a["category"]}</span>
          <span class="article-meta-info"><span>{a["date"]}</span>{author_dot}<span class="dot"></span><span>约 {read_time} 分钟</span></span>
        </div>
        {toc_html}
        <div class="article-body">{body_html}</div>
        <div class="article-share">
          <button class="share-btn" onclick="navigator.clipboard.writeText(window.location.href);this.textContent='✓ 已复制';setTimeout(()=>this.innerHTML='复制链接',2000)">复制链接</button>
        </div>
        {nav_html}
        {related_html}
        <a class="article-back" href="{back_href}">← 返回资讯列表</a>
      </div>
    </div>
  </section>"""


def _tpl_foot():
    """页脚 + 脚本"""
    return """
  <footer class="footer">
    <div class="container">
      <div class="footer-top">
        <div class="footer-brand">
          <div class="footer-logo">
            <div class="logo-icon">A</div>
            <span class="brand-text">ARKECT HEALTH</span>
          </div>
          <p>圣链健康成立于2019年，亚洲首家全球医疗精准匹配平台。与英国顶级医疗机构深度合作，为每一个家庭提供全周期、主动式、定制化的健康守护。</p>
        </div>
        <div class="footer-col">
          <h5>关于我们</h5>
          <a href="../about.html">公司简介</a>
          <a href="../resources.html">医疗资源</a>
          <a href="../doctors.html">精选医生</a>
          <a href="../cases.html">资讯分享</a>
        </div>
        <div class="footer-col">
          <h5>我们的服务</h5>
          <a href="../service-chronic.html">高端慢病管理</a>
          <a href="../service-private.html">皇家私人医生</a>
          <a href="../service-checkup.html">个性化体检</a>
          <a href="../service-student.html">留学生健康管家</a>
          <a href="../service-uk-treatment.html">赴英看病</a>
          <a href="../service-remote.html">远程问诊</a>
        </div>
        <div class="footer-col">
          <h5>快速链接</h5>
          <a href="../process.html">问诊流程</a>
          <a href="../blog.html">健康资讯</a>
          <a href="../contact.html">联系我们</a>
        </div>
        <div class="footer-qr-group"><div class="footer-qr"><img loading="lazy" src="../images/qrcode-official.png" alt="微信公众号"><span>微信公众号</span></div><div class="footer-qr"><img loading="lazy" src="../images/qrcode-video.png" alt="视频号"><span>视频号</span></div></div>
      </div>
      <div class="footer-locations">
        <div class="footer-location">
          <div class="loc-flag">🇬🇧</div>
          <div class="loc-info">
            <h6>伦敦总部</h6>
            <p>London, United Kingdom<br>enquiries@arkect.co.uk</p>
          </div>
        </div>
        <div class="footer-location">
          <div class="loc-flag">🇨🇳</div>
          <div class="loc-info">
            <h6>北京总部</h6>
            <p>Beijing, China<br>enquiries@arkect.co.uk</p>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© 2019-2026 Arkect Health 圣链健康. All Rights Reserved.</span>
        <div class="footer-links">
          <a href="#">隐私政策</a>
          <a href="#">数据保护</a>
          <a href="#">使用条款</a>
        </div>
      </div>
    </div>
  </footer>
  <script src="../js/main.js"></script>
</body>
</html>"""


def escape_js_string(s):
    """将 HTML 字符串转为 JS 单行字符串（处理引号和换行）"""
    s = s.replace('\\', '\\\\')
    s = s.replace("'", "\\'")
    s = s.replace('\n', ' ')
    s = re.sub(r'\s{2,}', ' ', s)
    return s

def html_escape(s):
    """HTML 属性值转义"""
    s = s.replace('&', '&amp;')
    s = s.replace('"', '&quot;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    return s

def format_date_zh(date_str):
    """将 2025-11-20 格式化为 2025年11月"""
    parts = date_str.split('-')
    if len(parts) >= 2:
        return parts[0] + '年' + str(int(parts[1])) + '月'
    return date_str

def generate_card_html(article, idx):
    """生成单张文章卡片的静态 HTML"""
    delay = (idx % 3) + 1
    cat = html_escape(article['category'])
    title = html_escape(article['title'])
    summary = html_escape(article['summary'])
    date_zh = format_date_zh(article.get('date', ''))
    aid = html_escape(article['id'])
    img = article.get('image', '')

    # 图片区域
    if img and img != 'None':
        img_html = f'''          <div class="case-image"><img loading="lazy" src="{html_escape(img)}" alt="{title}" onerror="this.style.display='none';this.parentElement.classList.add('no-image');"><div class="case-image-fallback"><svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h2v5zm0 4h-2v-2h2v2z"/></svg></div></div>'''
    else:
        img_html = '''          <div class="case-image no-image"><div class="case-image-fallback"><svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h2v5zm0 4h-2v-2h2v2z"/></svg></div></div>'''

    card = f'''        <a href="consultation/{aid}.html" class="case-card animate-on-scroll delay-{delay}" data-category="{cat}" data-id="{aid}">
{img_html}
          <div class="case-tag">{cat}</div>
          <h4>{title}</h4>
          <div class="case-meta"><span>{date_zh}</span></div>
          <p>{summary}</p>
        </a>'''
    return card

def generate_filters_html(tab_key, categories, articles):
    """生成筛选按钮的静态 HTML"""
    # 筛出属于该 tab 的文章
    tab_articles = [a for a in articles if a['category'] in categories]
    total = len(tab_articles)

    if not tab_articles or len(categories) <= 1:
        # 单分类或无文章，不需要筛选按钮
        return ''

    # 统计每个分类数量
    counts = {}
    for a in tab_articles:
        counts[a['category']] = counts.get(a['category'], 0) + 1

    buttons = [f'          <button class="case-filter-btn active" data-filter="all">全部 ({total})</button>']
    for cat in categories:
        cnt = counts.get(cat, 0)
        if cnt > 0:
            buttons.append(f'          <button class="case-filter-btn" data-filter="{html_escape(cat)}">{html_escape(cat)} ({cnt})</button>')

    return '\n'.join(buttons)

def _replace_between_markers(html, marker, new_content):
    """替换 <!-- BUILD:BEGIN:marker --> ... <!-- BUILD:END:marker --> 之间的内容
    
    如果找不到 BEGIN/END 标记，也尝试兼容旧的单行占位符 <!-- marker -->
    """
    begin = f'<!-- BUILD:BEGIN:{marker} -->'
    end = f'<!-- BUILD:END:{marker} -->'
    if begin in html and end in html:
        # 新格式：替换两个标记之间的全部内容
        pattern = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
        replacement = begin + '\n' + new_content + '\n' + end
        return pattern.sub(replacement, html)
    else:
        # 兼容旧格式：单行占位符
        old_marker = f'<!-- {marker} -->'
        if old_marker in html:
            return html.replace(old_marker, new_content)
        else:
            print(f'  ⚠️  cases.html 中未找到标记 {marker}，跳过注入')
            return html

def inject_cases_html(articles):
    """将静态文章卡片注入 cases.html"""
    # Tab 配置：tab_key → (grid_marker, filter_marker, categories)
    tab_map = {
        'recovery':      ('recovery-grid',      'recovery-filters',      ['慢病管理','远程问诊','赴英就医','留学生服务','干货分享']),
        'frontier':      ('frontier-grid',      'frontier-filters',      ['医界前沿']),
        'uk-news':       ('uk-news-grid',       'uk-news-filters',       ['英伦医讯']),
        'uk-knowledge':  ('uk-knowledge-grid',  'uk-knowledge-filters',  ['英伦医知']),
    }

    with open(CASES_HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    for tab_key, (grid_marker, filter_marker, categories) in tab_map.items():
        # 筛出该 tab 的文章，按日期倒序
        tab_articles = [a for a in articles if a['category'] in categories]
        tab_articles.sort(key=lambda a: a.get('date', ''), reverse=True)

        # 生成卡片 HTML
        cards = [generate_card_html(a, idx) for idx, a in enumerate(tab_articles)]
        grid_html = '\n'.join(cards) if cards else '          <p style="text-align:center;color:var(--text-light);padding:60px 0;">暂无文章，敬请期待</p>'

        # 生成筛选按钮 HTML
        filter_html = generate_filters_html(tab_key, categories, articles)

        # 使用双标记替换（支持重复构建）
        html = _replace_between_markers(html, grid_marker, grid_html)
        html = _replace_between_markers(html, filter_marker, filter_html)

    with open(CASES_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'✅ 静态文章卡片已注入 {CASES_HTML_FILE}')

def main():
    md_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, '*.md')))
    # 跳过 _ 开头的文件（模板等）
    md_files = [f for f in md_files if not os.path.basename(f).startswith('_')]
    if not md_files:
        print('⚠️  articles/ 目录下没有找到 .md 文件')
        return

    articles = []
    for filepath in md_files:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        try:
            meta, body = parse_frontmatter(text)
        except ValueError as e:
            print(f'❌ {filename}: {e}')
            continue

        # 必填字段检查
        required = ['id', 'category', 'title', 'summary', 'date']
        missing = [k for k in required if k not in meta or not meta[k]]
        if missing:
            print(f'❌ {filename}: 缺少必填字段 {missing}')
            continue

        # Markdown → HTML
        content_html = md_to_html(body)

        articles.append({
            'id': meta['id'],
            'category': meta['category'],
            'title': meta['title'],
            'summary': meta['summary'],
            'date': str(meta['date']),
            'author': meta.get('author', ''),
            'image': meta.get('image', ''),
            'content_html': content_html,
        })
        print(f'✅ {filename} → {meta["id"]}')

    # 生成 js/articles-data.js
    lines = [
        '/* ============================================',
        '   圣链健康 — 资讯分享文章数据（自动生成）',
        '   由 build-articles.py 从 articles/*.md 构建',
        '   ⚠️  请勿手动编辑，修改请编辑 .md 源文件',
        '   ============================================ */',
        '',
        'var ARTICLES = [',
    ]

    for i, a in enumerate(articles):
        comma = ',' if i < len(articles) - 1 else ''
        content_js = escape_js_string(a['content_html'])
        lines.append(f'  {{')
        lines.append(f'    id: \'{escape_js_string(a["id"])}\',')
        lines.append(f'    category: \'{escape_js_string(a["category"])}\',')
        lines.append(f'    title: \'{escape_js_string(a["title"])}\',')
        lines.append(f'    summary: \'{escape_js_string(a["summary"])}\',')
        lines.append(f'    date: \'{escape_js_string(a["date"])}\',')
        lines.append(f'    author: \'{escape_js_string(a["author"])}\',')
        lines.append(f'    image: \'{escape_js_string(a["image"])}\',')
        lines.append(f'    content: \'{content_js}\'')
        lines.append(f'  }}{comma}')

    lines.append('];')
    lines.append('')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'\n🎉 构建完成！{len(articles)} 篇文章 → {OUTPUT_FILE}')

    # 生成 consultation/[id].html 详情页
    generate_article_pages(articles)

    # 将静态文章卡片注入 cases.html（SEO 友好）
    inject_cases_html(articles)

if __name__ == '__main__':
    main()
