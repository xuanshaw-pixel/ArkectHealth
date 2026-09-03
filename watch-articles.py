#!/usr/bin/env python3 -u
"""
文件监听：自动检测 articles/*.md 的修改，触发 build-articles.py 构建。

使用方式：
    python3 watch-articles.py          # 默认监听，1.5秒轮询
    python3 watch-articles.py --once   # 只构建一次，不监听
    python3 watch-articles.py --interval 3  # 3秒轮询间隔

退出：Ctrl+C
"""

import os
import sys
import time
import subprocess
import glob
from pathlib import Path

# ─── 配置 ───
ARTICLES_DIR = Path(__file__).parent / "articles"
BUILD_SCRIPT = Path(__file__).parent / "build-articles.py"
DEFAULT_INTERVAL = 1.5  # 秒
DEBOUNCE_DELAY = 0.5    # 秒，防抖

def get_md_mtimes():
    """获取所有 .md 文件的修改时间字典 {文件名: mtime}"""
    mtimes = {}
    for f in glob.glob(str(ARTICLES_DIR / "*.md")):
        try:
            mtimes[f] = os.path.getmtime(f)
        except OSError:
            pass
    return mtimes

def run_build():
    """运行构建脚本，返回是否成功"""
    try:
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=30
        )
        # 提取关键输出
        lines = result.stdout.strip().split('\n')
        # 找到汇总行
        for line in lines:
            if '🎉' in line or '构建完成' in line:
                print(f"   {line.strip()}")
        if result.returncode == 0:
            return True
        else:
            # 显示错误信息
            if result.stderr:
                for line in result.stderr.strip().split('\n')[-3:]:
                    print(f"   ⚠️  {line.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("   ⚠️  构建超时（30秒）")
        return False
    except Exception as e:
        print(f"   ⚠️  构建出错: {e}")
        return False

def watch(interval=DEFAULT_INTERVAL, once=False):
    """主监听循环"""
    
    # 启动时先构建一次
    print("🔨 首次构建...")
    if run_build():
        print("✅ 构建成功！")
    else:
        print("❌ 构建失败，请检查错误信息")
    
    if once:
        return
    
    print(f"\n👁️  正在监听 articles/*.md 的修改...（每 {interval}s 检查一次）")
    print(f"   目录: {ARTICLES_DIR}")
    print(f"   按 Ctrl+C 退出\n")
    
    prev_mtimes = get_md_mtimes()
    
    try:
        while True:
            time.sleep(interval)
            
            curr_mtimes = get_md_mtimes()
            
            # 检测变化
            changes = []
            
            # 新增文件
            for f in curr_mtimes:
                if f not in prev_mtimes:
                    changes.append(("新增", f))
                elif curr_mtimes[f] != prev_mtimes[f]:
                    changes.append(("修改", f))
            
            # 删除文件
            for f in prev_mtimes:
                if f not in curr_mtimes:
                    changes.append(("删除", f))
            
            if not changes:
                continue
            
            # 防抖：等待一小段时间，避免编辑器多次保存
            time.sleep(DEBOUNCE_DELAY)
            curr_mtimes = get_md_mtimes()  # 重新获取最新状态
            
            # 显示变化
            for action, f in changes:
                name = Path(f).name
                if action == "新增":
                    print(f"📝 新增: {name}")
                elif action == "修改":
                    print(f"📝 修改: {name}")
                elif action == "删除":
                    print(f"🗑️  删除: {name}")
            
            # 触发构建
            print("🔨 正在构建...")
            if run_build():
                print("✅ 构建完成！")
            else:
                print("❌ 构建失败")
            
            print(f"\n👁️  继续监听...\n")
            prev_mtimes = curr_mtimes
    
    except KeyboardInterrupt:
        print("\n\n👋 监听已停止。再见！")

if __name__ == "__main__":
    # 解析简单参数
    once = "--once" in sys.argv
    interval = DEFAULT_INTERVAL
    
    for i, arg in enumerate(sys.argv):
        if arg == "--interval" and i + 1 < len(sys.argv):
            try:
                interval = float(sys.argv[i + 1])
            except ValueError:
                print("⚠️  --interval 需要数字参数，使用默认值 1.5s")
    
    watch(interval=interval, once=once)
