#!/usr/bin/env python3
"""============================================
   圣链健康 — 微信文章同步脚本
   用法: python3 sync-article.py
   功能：从微信公众号复制内容 → 清洗排版 → 生成 .md → 自动构建
   ============================================"""

import os
import re
import sys
import tempfile
import subprocess
import webbrowser
from datetime import date
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(SCRIPT_DIR, 'articles')

CATEGORIES = ['慢病管理', '远程问诊', '赴英就医', '留学生服务', '干货分享', '医界前沿', '英伦医讯', '英伦医知']
CATEGORY_PREFIX = {
    '慢病管理': 'chronic-care',
    '远程问诊': 'remote-consult',
    '赴英就医': 'uk-treatment',
    '留学生服务': 'student',
    '干货分享': 'tips',
    '医界前沿': 'frontier',
    '英伦医讯': 'uk-news',
    '英伦医知': 'uk-knowledge',
}


# ──────────────────────────────────────────────
#  HTML → Markdown 转换器（纯 stdlib，无第三方依赖）
# ──────────────────────────────────────────────

class WechatHtmlToMarkdown(HTMLParser):
    """将微信公众号的 HTML 转为干净的 Markdown"""

    TAG_MAP = {
        'h1': '#', 'h2': '##', 'h3': '###', 'h4': '####',
    }
    INLINE_MAP = {
        'strong': '**', 'b': '**',
        'em': '*', 'i': '*',
    }

    def __init__(self):
        super().__init__()
        self.output = []
        self._tag_stack = []
        self._list_depth = 0
        self._in_blockquote = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self._tag_stack.append(tag)

        if tag in self.TAG_MAP:
            prefix = self.TAG_MAP[tag]
            self.output.append('\n\n' + prefix + ' ')
        elif tag in ('p', 'div'):
            self.output.append('\n\n')
        elif tag == 'br':
            self.output.append('\n')
        elif tag in ('strong', 'b', 'em', 'i'):
            marker = self.INLINE_MAP.get(tag, '')
            self.output.append(marker)
        elif tag == 'a':
            href = dict(attrs).get('href', '')
            if href:
                self.output.append('[')
                self._tag_stack[-1] = ('a', href)
        elif tag in ('ul', 'ol'):
            self._list_depth += 1
            self.output.append('\n')
        elif tag == 'li':
            indent = '  ' * (self._list_depth - 1)
            self.output.append('\n' + indent + '- ')
        elif tag == 'blockquote':
            self._in_blockquote = True
            self.output.append('\n\n> ')
        elif tag in ('img', 'image'):
            src = dict(attrs).get('data-src') or dict(attrs).get('src', '')
            if src:
                self.output.append(f'\n\n![图片]({src})\n\n')
        elif tag == 'section':
            pass  # 微信用 <section> 做布局，忽略

    def handle_endtag(self, tag):
        tag = tag.lower()
        if not self._tag_stack:
            return
        popped = self._tag_stack.pop()

        if tag in self.TAG_MAP:
            self.output.append('\n\n')
        elif tag in ('p', 'div'):
            self.output.append('\n')
        elif tag in ('strong', 'b', 'em', 'i'):
            marker = self.INLINE_MAP.get(tag, '')
            self.output.append(marker)
        elif tag == 'a':
            if isinstance(popped, tuple) and popped[0] == 'a':
                href = popped[1]
                self.output.append(f']({href})')
            else:
                self.output.append(']')
        elif tag in ('ul', 'ol'):
            self._list_depth = max(0, self._list_depth - 1)
            self.output.append('\n')
        elif tag == 'blockquote':
            self._in_blockquote = False
            self.output.append('\n')

    def handle_data(self, data):
        if self._in_blockquote:
            data = data.replace('\n', '\n> ')
        self.output.append(data)

    def get_markdown(self):
        text = ''.join(self.output)
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        return text.strip()


def clean_wechat_html(raw_text):
    """判断输入是 HTML 还是纯文本，统一输出干净 Markdown"""
    raw_text = raw_text.strip()
    raw_text = re.sub(r'^[\s]*微信扫一扫.*?\n', '', raw_text)

    if re.search(r'<[a-zA-Z][^>]*>', raw_text):
        # HTML → 转换
        raw_text = re.sub(r'\s+style\s*=\s*"[^"]*"', '', raw_text)
        raw_text = re.sub(r'\s+class\s*=\s*"[^"]*"', '', raw_text)
        raw_text = re.sub(r'<section[^>]*>', '\n', raw_text)
        raw_text = re.sub(r'</section>', '\n', raw_text)

        converter = WechatHtmlToMarkdown()
        converter.feed(raw_text)
        return converter.get_markdown()
    else:
        # 纯文本 → 简单格式整理
        text = raw_text
        text = re.sub(r'\n\s*([一二三四五六七八九十]+[、.．])\s*(.+)', r'\n\n## \1\2', text)
        text = re.sub(r'\n\s*(\d+[、.．])\s*(.+)', r'\n\n### \1\2', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def open_editor(content):
    """打开临时文件让用户粘贴内容，返回编辑后的内容"""
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', encoding='utf-8', delete=False
    )
    tmp.write(content)
    tmp.close()

    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
    if editor:
        subprocess.run([editor, tmp.name])
    else:
        if os.path.exists('/usr/local/bin/code') or os.path.exists('/Applications/Visual Studio Code.app'):
            try:
                subprocess.run(['code', '--wait', tmp.name])
            except FileNotFoundError:
                subprocess.run(['nano', tmp.name])
        else:
            subprocess.run(['nano', tmp.name])

    with open(tmp.name, 'r', encoding='utf-8') as f:
        result = f.read()
    os.unlink(tmp.name)
    return result


def generate_next_id(category):
    """根据分类自动生成下一个文章 ID"""
    prefix = CATEGORY_PREFIX.get(category, 'article')
    max_num = 0
    for f in os.listdir(ARTICLES_DIR):
        if f.startswith(prefix + '-') and f.endswith('.md'):
            num_str = f[len(prefix)+1:-3]
            if num_str.isdigit():
                max_num = max(max_num, int(num_str))
    return f'{prefix}-{max_num + 1}'

    def get_markdown(self):
        text = ''.join(self.output)
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [line.rstrip() for line in text.split('\n')]


def main():
    print('╔══════════════════════════════════════╗')
    print('║   圣链健康 — 微信文章同步工具       ║')
    print('║   从微信公众号复制 → 自动生成网页   ║')
    print('╚══════════════════════════════════════╝')
    print()

    # ── 1. 输入文章元信息 ──
    title = input('📝 文章标题: ').strip()
    if not title:
        print('❌ 标题不能为空')
        sys.exit(1)

    print('\n📂 选择分类:')
    for i, cat in enumerate(CATEGORIES):
        print(f'  {i+1}) {cat}')
    cat_input = input('输入编号或自定义分类名: ').strip()
    if cat_input.isdigit() and 1 <= int(cat_input) <= len(CATEGORIES):
        category = CATEGORIES[int(cat_input) - 1]
    else:
        category = cat_input or '干货分享'

    summary = input('\n📋 文章摘要（回车跳过）: ').strip()
    if not summary:
        summary = '稍后填写'

    # ── 2. 自动生成 ID ──
    article_id = generate_next_id(category)
    custom_id = input(f'\n🆔 文章 ID（回车使用 {article_id}）: ').strip()
    if custom_id:
        article_id = custom_id

    out_file = os.path.join(ARTICLES_DIR, article_id + '.md')
    if os.path.isfile(out_file):
        print(f'❌ 文件已存在: {out_file}')
        sys.exit(1)

    # ── 3. 获取文章内容 ──
    print('\n' + '─' * 50)
    print('📥 现在请提供文章正文，有两种方式：')
    print('  1) 直接粘贴 — 从微信文章复制文本后粘贴到编辑器')
    print('  2) 从文件读取 — 指定一个已保存的 .txt 或 .html 文件')
    print('─' * 50)

    mode = input('\n选择方式 (1/2，回车默认1): ').strip() or '1'

    if mode == '2':
        filepath = input('文件路径: ').strip()
        filepath = os.path.expanduser(filepath)
        if not os.path.isfile(filepath):
            print(f'❌ 文件不存在: {filepath}')
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        print(f'✅ 已读取文件 ({len(raw_content)} 字符)')
    else:
        hint = (
            '# 👇 在下方粘贴从微信文章复制的内容，保存后关闭此文件即可\n'
            '# （本行是注释，会被自动忽略）\n'
            '#\n'
            '# 提示：\n'
            '#   - 可以直接粘贴微信文章的文本\n'
            '#   - 也可以粘贴 HTML 源码（从浏览器右键"查看源代码"复制）\n'
            '#   - 脚本会自动清理微信排版，转为干净 Markdown\n'
            '#   - 粘贴完成后保存并关闭此文件\n'
            '\n'
        )
        print('\n🔄 正在打开编辑器...')
        print('   粘贴内容后保存关闭即可继续\n')
        raw_content = open_editor(hint)
        raw_content = '\n'.join(
            line for line in raw_content.split('\n')
            if not line.strip().startswith('#')
        )

    if not raw_content.strip():
        print('❌ 内容为空，请重新运行脚本')
        sys.exit(1)

    # ── 4. 清洗排版 ──
    print('\n🧹 正在清洗微信排版...')
    clean_content = clean_wechat_html(raw_content)
    print(f'   原始 {len(raw_content)} 字符 → 清洗后 {len(clean_content)} 字符')

    # ── 5. 预览并确认 ──
    print('\n📖 清洗后内容预览（前 500 字）：')
    print('─' * 50)
    preview = clean_content[:500]
    if len(clean_content) > 500:
        preview += '\n...(更多内容省略)...'
    print(preview)
    print('─' * 50)

    confirm = input('\n✅ 确认发布？(Y/n/e=编辑修改): ').strip().lower()
    if confirm == 'e':
        clean_content = open_editor(clean_content + '\n')
    elif confirm == 'n':
        print('❌ 已取消')
        sys.exit(0)

    # ── 6. 生成 .md 文件 ──
    today = date.today().isoformat()
    frontmatter = (
        f'---\n'
        f'id: {article_id}\n'
        f'category: {category}\n'
        f'title: {title}\n'
        f'summary: {summary}\n'
        f'date: {today}\n'
        f'author: 圣链健康\n'
        f'image: images/articles/{article_id}.jpg\n'
        f'---'
    )
    full_content = frontmatter + '\n\n' + clean_content + '\n'

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(full_content)

    print(f'\n✅ 文章已创建: {out_file}')

    # ── 7. 自动构建 ──
    print('🔨 自动构建中...')
    build_script = os.path.join(SCRIPT_DIR, 'build-articles.py')
    result = subprocess.run([sys.executable, build_script], cwd=SCRIPT_DIR)

    if result.returncode == 0:
        print('\n🎉 同步完成！')
    else:
        print('\n⚠️  构建出现问题，请手动运行: python3 build-articles.py')

    # ── 8. 输出指引 ──
    html_path = os.path.join(SCRIPT_DIR, 'consultation', article_id + '.html')
    print(f'\n┌──────────────────────────────────────────┐')
    print(f'│  📄 文章文件: {out_file}')
    print(f'│  🌐 预览页面: consultation/{article_id}.html')
    print(f'│  🔧 重新构建: python3 build-articles.py')
    print(f'│')
    print(f'│  ⚠️  图片提醒：')
    print(f'│    请将文章封面图保存为:')
    print(f'│    images/articles/{article_id}.jpg')
    print(f'│    建议尺寸: 800×450 (16:9)')
    print(f'└──────────────────────────────────────────┘')

    # 尝试在浏览器中打开预览
    if os.path.isfile(html_path):
        open_browser = input('\n🌐 在浏览器中打开预览？(Y/n): ').strip().lower()
        if open_browser != 'n':
            webbrowser.open(f'file://{html_path}')


if __name__ == '__main__':
    main()