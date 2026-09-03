#!/usr/bin/env python3
"""============================================
   crawl-articles.py - Article Crawler
   From RSS/PubMed, OpenAI translates to .md
   Usage: python3 crawl-articles.py [--count N] [--auto-commit]
   """

import os, sys, glob, re, json, time, argparse, subprocess, requests, feedparser
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__) or '.', '.env'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
SCRIPT_DIR = os.path.dirname(__file__) or '.'
ARTICLES_DIR = os.path.join(SCRIPT_DIR, 'articles')
MAX_PER_CAT = 5
MAX_TOTAL = 1
DELAY = 3

RSS_SOURCES = {
    'uk-news': [
        'https://feeds.bbci.co.uk/news/health/rss.xml',
        'https://www.nhs.uk/news/feed/',
    ],
    'frontier': [
        'https://www.theguardian.com/lifeandstyle/health/rss',
    ],
}

PUBMED_TERM = '(UK[affiliation] OR Britain[affiliation]) AND (clinical trial[pt]) AND 2025[dp]'

CATEGORY_MAP = {'frontier': '医界前沿', 'uk-news': '英伦医讯'}
ID_PREFIX_MAP = {'frontier': 'frontier', 'uk-news': 'uk-news'}


# --- 1. Fetch RSS ---
def fetch_rss(category_key):
    urls = RSS_SOURCES.get(category_key, [])
    items = []
    for feed_url in urls:
        print(f'  Fetching RSS: {feed_url}')
        try:
            resp = requests.get(feed_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ArkectBot/1.0)'
            })
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:MAX_PER_CAT]:
                title = entry.get('title', '').strip()
                summary = entry.get('summary', '').strip()
                summary = re.sub(r'<[^>]+>', '', summary)[:300]
                url = entry.get('link', '')
                date_str = ''
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    t = entry.published_parsed
                    date_str = f'{t.tm_year}-{t.tm_mon:02d}-{t.tm_mday:02d}'
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    t = entry.updated_parsed
                    date_str = f'{t.tm_year}-{t.tm_mon:02d}-{t.tm_mday:02d}'
                if title and summary:
                    items.append({
                        'title': title, 'summary': summary,
                        'url': url,
                        'date': date_str or datetime.now().strftime('%Y-%m-%d'),
                    })
            time.sleep(DELAY)
        except Exception as e:
            print(f'  RSS fetch failed: {e}')
    return items


# --- 2. Fetch PubMed ---
def fetch_pubmed(retmax=10):
    items = []
    print('  Fetching PubMed...')
    try:
        params = {
            'db': 'pubmed', 'term': PUBMED_TERM,
            'retmax': retmax, 'sort': 'date', 'retmode': 'json',
        }
        resp = requests.get(
            'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
            params=params, timeout=15)
        ids = resp.json().get('esearchresult', {}).get('idlist', [])
        if not ids:
            print('  PubMed: no results')
            return items
        params2 = {'db': 'pubmed', 'id': ','.join(ids), 'retmode': 'json'}
        resp2 = requests.get(
            'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',
            params=params2, timeout=15)
        data = resp2.json().get('result', {})
        for pmid in ids:
            info = data.get(pmid, {})
            title = info.get('title', '').strip()
            if not title:
                continue
            abstract = info.get('abstract', '')
            if isinstance(abstract, dict):
                abstract = ' '.join(abstract.values())
            summary = str(abstract)[:300] if abstract else title
            date_str = info.get('pubdate', '')
            if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                date_str = datetime.now().strftime('%Y-%m-%d')
            items.append({
                'title': title, 'summary': summary,
                'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
                'date': date_str,
            })
        time.sleep(DELAY)
    except Exception as e:
        print(f'  PubMed fetch failed: {e}')
    return items


# --- 3. AI Translate ---
def ai_translate(title_en, summary_en, category_zh):
    if not OPENAI_API_KEY:
        return None, None
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""You are a medical news translator for a Chinese health website (圣链健康 / Arkect Health).
Category: {category_zh}

Translate the following English medical news title and summary into Chinese.
Requirements:
- Title: concise, engaging, under 25 Chinese characters
- Summary: natural Chinese, 80-150 characters, highlight key points
- Keep medical terms accurate (e.g. NHS=英国国家医疗服务体系, clinical trial=临床试验)
- Add Chinese context where helpful for UK healthcare news

English Title: {title_en}
English Summary: {summary_en}

Return JSON only: {{"title_zh": "...", "summary_zh": "..."}}"""
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        text = resp.choices[0].message.content.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        data = json.loads(text)
        return data.get('title_zh', ''), data.get('summary_zh', '')
    except Exception as e:
        print(f'  AI translate failed: {e}')
        return None, None


# --- 4. Helpers ---
def get_existing_titles():
    titles = set()
    for fp in glob.glob(os.path.join(ARTICLES_DIR, '*.md')):
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('title:'):
                        titles.add(line.split(':', 1)[1].strip().strip('"'))
                        break
        except Exception:
            pass
    return titles


def get_next_number(prefix):
    nums = []
    for fp in glob.glob(os.path.join(ARTICLES_DIR, f'{prefix}-*.md')):
        m = re.search(r'-(\d+)\.md$', fp)
        if m:
            nums.append(int(m.group(1)))
    return max(nums, default=0) + 1


# --- 5. Write Markdown ---
def write_md(item, category_key, num):
    prefix = ID_PREFIX_MAP.get(category_key, category_key)
    slug = f'{prefix}-{num:03d}'
    category_zh = CATEGORY_MAP.get(category_key, category_key)
    title_zh = item.get('title_zh', '')
    summary_zh = item.get('summary_zh', '')
    title_en = item.get('title', '')
    summary_en = item.get('summary', '')
    url = item.get('url', '')
    date_str = item.get('date', datetime.now().strftime('%Y-%m-%d'))
    if not title_zh:
        title_zh = title_en[:25]
    if not summary_zh:
        summary_zh = summary_en[:150]
    frontmatter = f"""---
title: "{title_zh}"
date: {date_str}
category: {category_zh}
tags: [英国医疗, NHS, {category_zh}]
source: "{url}"
slug: {slug}
---"""
    body = f"""
## {title_zh}

{summary_zh}

> 原文：[{title_en}]({url})

---

*本文由圣链健康（Arkect Health）AI 系统自动翻译整理，仅供参考。*
*如需专业医疗建议，请咨询 qualified 医疗专业人员。*
"""
    filepath = os.path.join(ARTICLES_DIR, f'{slug}.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter + body)
    print(f'  Written: {filepath}')
    return filepath


# --- 6. Process Category ---
def process_category(category_key, articles, max_count=99):
    existing = get_existing_titles()
    prefix = ID_PREFIX_MAP.get(category_key, category_key)
    num = get_next_number(prefix)
    new_count = 0
    category_zh = CATEGORY_MAP.get(category_key, category_key)
    for art in articles:
        if new_count >= max_count:
            break
        if art['title'] in existing:
            print(f'  Skip (exists): {art["title"][:40]}')
            continue
        title_zh, summary_zh = ai_translate(
            art['title'], art['summary'], category_zh)
        if not title_zh:
            print(f'  Skip (translate failed): {art["title"][:40]}')
            continue
        art['title_zh'] = title_zh
        art['summary_zh'] = summary_zh
        write_md(art, category_key, num)
        num += 1
        new_count += 1
        time.sleep(1)
    return new_count


# --- 7. Main ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=None,
                        help='Max articles to generate')
    parser.add_argument('--auto-commit', action='store_true',
                        help='Git add/commit/push after crawl')
    args = parser.parse_args()
    max_total = args.count if args.count is not None else MAX_TOTAL
    print('Crawler - max', max_total, 'articles')
    print('=' * 50)
    total_new = 0
    half = max(1, max_total // 2)
    print('[frontier]')
    fa = fetch_pubmed(retmax=8)
    fa += fetch_rss('frontier')
    if fa:
        total_new += process_category('frontier', fa, max_count=half)
    print('[uk-news]')
    ua = fetch_rss('uk-news')
    if ua:
        total_new += process_category('uk-news', ua, max_count=half)
    if total_new > 0:
        bs = os.path.join(SCRIPT_DIR, 'build-articles.py')
        print(f'Building {total_new} new article(s)...')
        os.system(f'python3 {bs!r}')
        if args.auto_commit:
            print('Auto git commit & push...')
            os.chdir(SCRIPT_DIR)
            subprocess.run(['git', 'add', '-A'], check=False)
            d = datetime.now().strftime('%Y-%m-%d')
            msg = f'auto-crawl: {total_new} new - {d}'
            subprocess.run(['git', 'commit', '-m', msg], check=False)
            subprocess.run(['git', 'push'], check=False)
            print('  Pushed to GitHub')
        print(f'Done! {total_new} new article(s)')
    else:
        print('No new articles')


if __name__ == '__main__':
    main()
