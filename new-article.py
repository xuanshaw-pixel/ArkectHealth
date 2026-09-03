#!/usr/bin/env python3
"""============================================
   圣链健康 — 新建文章一键脚本
   用法: python3 new-article.py
         python3 new-article.py "标题" "分类" "摘要"
   ============================================"""

import os
import sys
import subprocess
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(SCRIPT_DIR, 'articles')
TEMPLATE = os.path.join(ARTICLES_DIR, '_template.md')

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


def main():
    if not os.path.isfile(TEMPLATE):
        print('❌ 找不到模板文件:', TEMPLATE)
        sys.exit(1)

    # 读取参数
    if len(sys.argv) >= 4:
        title = sys.argv[1]
        category = sys.argv[2]
        summary = sys.argv[3]
    elif len(sys.argv) >= 3:
        title = sys.argv[1]
        category = sys.argv[2]
        summary = ''
    elif len(sys.argv) >= 2:
        title = sys.argv[1]
        category = ''
        summary = ''
    else:
        title = ''
        category = ''
        summary = ''

    # 标题
    if not title:
        title = input('文章标题: ')
    if not title:
        print('❌ 标题不能为空')
        sys.exit(1)

    # 分类
    if not category:
        print('\n选择分类:')
        for i, cat in enumerate(CATEGORIES):
            print(f'  {i+1}) {cat}')
        cat_input = input('输入编号或自定义分类名: ').strip()
        if cat_input.isdigit() and 1 <= int(cat_input) <= len(CATEGORIES):
            category = CATEGORIES[int(cat_input) - 1]
        else:
            category = cat_input

    # 摘要
    if not summary:
        summary = input('文章摘要（回车跳过）: ').strip()
    if not summary:
        summary = '稍后填写'

    # 自动生成 ID
    id_input = input('文章 ID（回车自动生成）: ').strip()
    if not id_input:
        prefix = CATEGORY_PREFIX.get(category, 'article')
        # 找同前缀最大编号
        max_num = 0
        for f in os.listdir(ARTICLES_DIR):
            if f.startswith(prefix + '-') and f.endswith('.md'):
                num_str = f[len(prefix)+1:-3]
                if num_str.isdigit():
                    max_num = max(max_num, int(num_str))
        article_id = f'{prefix}-{max_num + 1}'
    else:
        article_id = id_input

    # 检查文件是否已存在
    out_file = os.path.join(ARTICLES_DIR, article_id + '.md')
    if os.path.isfile(out_file):
        print(f'❌ 文件已存在: {out_file}')
        sys.exit(1)

    # 读取模板并替换
    today = date.today().isoformat()
    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('{{ID}}', article_id)
    content = content.replace('{{CATEGORY}}', category)
    content = content.replace('{{TITLE}}', title)
    content = content.replace('{{SUMMARY}}', summary)
    content = content.replace('{{DATE}}', today)

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'\n✅ 文章已创建: {out_file}')

    # 自动构建
    print('🔨 自动构建中...')
    build_script = os.path.join(SCRIPT_DIR, 'build-articles.py')
    result = subprocess.run([sys.executable, build_script], cwd=SCRIPT_DIR)

    print('\n🎉 完成！')
    print(f'  编辑文章: {out_file}')
    print(f'  预览页面: consultation/{article_id}.html')
    print('  重新构建: python3 build-articles.py')


if __name__ == '__main__':
    main()
