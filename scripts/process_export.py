#!/usr/bin/env python3
"""
Raindrop.io 导出文件处理器
处理从 Raindrop.io 手动导出的书签文件（HTML 或 JSON 格式）
生成静态网站并推送到 GitHub Pages
"""

import os
import re
import json
import html
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser


class BookmarkHTMLParser(HTMLParser):
    """解析 Netscape Bookmark HTML 格式"""
    
    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.current_folder = "未分类"
        self.current_bookmark = None
        self.folders = {0: "未分类"}  # id -> name
        self.folder_stack = [0]
        self.in_h3 = False
        self.in_a = False
        self.in_dd = False
        self.dd_text = ""
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "h3":
            self.in_h3 = True
        elif tag == "a":
            self.in_a = True
            self.current_bookmark = {
                "title": "",
                "link": attrs_dict.get("href", ""),
                "tags": [],
                "created": attrs_dict.get("add_date", ""),
                "icon": attrs_dict.get("icon", ""),
                "description": ""
            }
        elif tag == "dd":
            self.in_dd = True
            self.dd_text = ""
        elif tag == "dl":
            # 进入子文件夹
            pass
            
    def handle_endtag(self, tag):
        if tag == "h3":
            self.in_h3 = False
        elif tag == "a":
            self.in_a = False
        elif tag == "dd":
            self.in_dd = False
            if self.current_bookmark and self.dd_text:
                self.current_bookmark["description"] = self.dd_text.strip()
        elif tag == "dl":
            # 退出当前文件夹
            if len(self.folder_stack) > 1:
                self.folder_stack.pop()
                self.current_folder = self.folders.get(self.folder_stack[-1], "未分类")
                
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
            
        if self.in_h3:
            # 新文件夹
            folder_id = len(self.folders)
            self.folders[folder_id] = data
            self.folder_stack.append(folder_id)
            self.current_folder = data
            
        elif self.in_a and self.current_bookmark:
            self.current_bookmark["title"] = data
            
            # 尝试从标题提取标签 (格式: "标题 #tag1 #tag2")
            if "#" in data:
                parts = data.split("#")
                self.current_bookmark["title"] = parts[0].strip()
                self.current_bookmark["tags"] = [t.strip() for t in parts[1:] if t.strip()]
            
            self.current_bookmark["folder"] = self.current_folder
            self.bookmarks.append(self.current_bookmark)
            self.current_bookmark = None
            
        elif self.in_dd:
            self.dd_text += data


def parse_html_bookmarks(file_path):
    """解析 HTML 格式的书签文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = BookmarkHTMLParser()
    parser.feed(content)
    
    # 按文件夹组织
    collections = {}
    for bm in parser.bookmarks:
        folder = bm.get("folder", "未分类")
        if folder not in collections:
            collections[folder] = []
        collections[folder].append(bm)
    
    return collections


def parse_json_bookmarks(file_path):
    """解析 JSON 格式的书签文件（Raindrop 导出格式）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Raindrop JSON 导出格式通常是数组
    if isinstance(data, list):
        collections = {}
        for item in data:
            folder = item.get("collection", {}).get("title", "未分类")
            if folder not in collections:
                collections[folder] = []
            
            collections[folder].append({
                "title": item.get("title", "无标题"),
                "link": item.get("link", ""),
                "tags": item.get("tags", []),
                "description": item.get("excerpt", "") or item.get("note", ""),
                "created": item.get("created", ""),
                "icon": item.get("media", [{}])[0].get("link", "") if item.get("media") else "",
                "important": item.get("important", False)
            })
        return collections
    
    # 或者是嵌套格式
    if isinstance(data, dict):
        if "result" in data:
            data = data["result"]
        
        collections = {}
        for item in data:
            folder = item.get("collection", "未分类")
            if isinstance(folder, dict):
                folder = folder.get("title", "未分类")
            if folder not in collections:
                collections[folder] = []
            
            collections[folder].append({
                "title": item.get("title", "无标题"),
                "link": item.get("link", ""),
                "tags": item.get("tags", []),
                "description": item.get("excerpt", "") or item.get("note", ""),
                "created": item.get("created", ""),
                "icon": item.get("cover", ""),
                "important": item.get("important", False)
            })
        return collections
    
    return {}


def process_bookmarks_file(file_path):
    """自动检测并处理书签文件"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    ext = path.suffix.lower()
    
    if ext == '.json':
        print(f"📄 检测到 JSON 格式文件")
        return parse_json_bookmarks(file_path)
    elif ext in ['.html', '.htm']:
        print(f"📄 检测到 HTML 格式文件")
        return parse_html_bookmarks(file_path)
    else:
        # 尝试自动检测
        with open(file_path, 'r', encoding='utf-8') as f:
            first_chars = f.read(100)
        
        if first_chars.strip().startswith('{') or first_chars.strip().startswith('['):
            print(f"📄 自动检测: JSON 格式")
            return parse_json_bookmarks(file_path)
        else:
            print(f"📄 自动检测: HTML 格式")
            return parse_html_bookmarks(file_path)


def generate_html_site(collections, output_dir, title="我的书签收藏"):
    """生成静态 HTML 网站"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 统计信息
    total_bookmarks = sum(len(bms) for bms in collections.values())
    total_collections = len(collections)
    
    metadata = {
        "export_time": datetime.now().isoformat(),
        "total_collections": total_collections,
        "total_bookmarks": total_bookmarks,
        "title": title
    }
    
    # 生成主页面
    index_html = generate_index_html(collections, metadata)
    (output_path / "index.html").write_text(index_html, encoding="utf-8")
    
    # 为每个收藏夹生成单独页面
    collections_dir = output_path / "collections"
    collections_dir.mkdir(exist_ok=True)
    
    for folder_name, bookmarks in collections.items():
        col_html = generate_collection_html(folder_name, bookmarks, metadata)
        safe_name = sanitize_filename(folder_name)
        (collections_dir / f"{safe_name}.html").write_text(col_html, encoding="utf-8")
    
    # 生成标签页面
    tags_dir = output_path / "tags"
    tags_dir.mkdir(exist_ok=True)
    
    all_tags = {}
    for folder_name, bookmarks in collections.items():
        for bookmark in bookmarks:
            for tag in bookmark.get("tags", []):
                if tag not in all_tags:
                    all_tags[tag] = []
                all_tags[tag].append({**bookmark, "folder": folder_name})
    
    for tag, bookmarks in all_tags.items():
        tag_html = generate_tag_html(tag, bookmarks, metadata)
        safe_tag = sanitize_filename(tag)
        (tags_dir / f"{safe_tag}.html").write_text(tag_html, encoding="utf-8")
    
    # 生成标签索引
    tags_index_html = generate_tags_index_html(all_tags, metadata)
    (tags_dir / "index.html").write_text(tags_index_html, encoding="utf-8")
    
    # 生成 CSS 样式
    css = generate_css()
    (output_path / "style.css").write_text(css, encoding="utf-8")
    
    # 生成 JSON 数据
    json_data = {
        "collections": collections,
        "metadata": metadata
    }
    (output_path / "data.json").write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # 生成搜索页面
    search_html = generate_search_html(collections, metadata)
    (output_path / "search.html").write_text(search_html, encoding="utf-8")
    
    print(f"\n✅ 静态网站已生成到: {output_path}")
    print(f"   📊 {total_collections} 个收藏夹, {total_bookmarks} 个书签")
    
    return metadata


def sanitize_filename(name):
    """清理文件名"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip() or "untitled"


def generate_css():
    """生成 CSS 样式"""
    return """
/* Raindrop Bookmarks Gallery */
:root {
    --primary: #4A90D9;
    --primary-dark: #357ABD;
    --bg: #f5f7fa;
    --card-bg: #ffffff;
    --text: #333333;
    --text-muted: #666666;
    --border: #e1e5eb;
    --shadow: 0 2px 8px rgba(0,0,0,0.1);
    --radius: 12px;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg: #1a1a2e;
        --card-bg: #16213e;
        --text: #e8e8e8;
        --text-muted: #a0a0a0;
        --border: #2a2a4e;
    }
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

.container { max-width: 1400px; margin: 0 auto; padding: 20px; }

header {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    padding: 40px 20px;
    text-align: center;
    margin-bottom: 30px;
}

header h1 { font-size: 2.5em; margin-bottom: 10px; }
header p { opacity: 0.9; font-size: 1.1em; }

nav {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 15px 20px;
    position: sticky;
    top: 0;
    z-index: 100;
}

nav ul { list-style: none; display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
nav a { color: var(--text); text-decoration: none; padding: 8px 16px; border-radius: 20px; transition: all 0.3s; }
nav a:hover { background: var(--primary); color: white; }

.stats { display: flex; gap: 20px; justify-content: center; margin: 20px 0; flex-wrap: wrap; }
.stat-item { background: var(--card-bg); padding: 15px 25px; border-radius: var(--radius); text-align: center; box-shadow: var(--shadow); }
.stat-number { font-size: 2em; font-weight: bold; color: var(--primary); }

.collections-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
.collection-card { background: var(--card-bg); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow); transition: transform 0.3s, box-shadow 0.3s; }
.collection-card:hover { transform: translateY(-5px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
.collection-card h3 { color: var(--primary); margin-bottom: 10px; font-size: 1.3em; }
.collection-count { color: var(--text-muted); font-size: 0.9em; }

.bookmarks-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; margin: 20px 0; }
.bookmark-card { background: var(--card-bg); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); transition: transform 0.3s, box-shadow 0.3s; }
.bookmark-card:hover { transform: translateY(-5px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
.bookmark-cover { width: 100%; height: 160px; object-fit: cover; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.bookmark-content { padding: 15px; }
.bookmark-title { font-size: 1.1em; font-weight: 600; margin-bottom: 8px; color: var(--text); }
.bookmark-title a { color: inherit; text-decoration: none; }
.bookmark-title a:hover { color: var(--primary); }
.bookmark-excerpt { color: var(--text-muted); font-size: 0.9em; margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.bookmark-meta { display: flex; gap: 10px; flex-wrap: wrap; font-size: 0.8em; }
.bookmark-tag { background: var(--primary); color: white; padding: 3px 10px; border-radius: 12px; text-decoration: none; transition: opacity 0.3s; }
.bookmark-tag:hover { opacity: 0.8; }
.bookmark-domain { color: var(--text-muted); font-size: 0.85em; }
.bookmark-important { border-left: 4px solid #f59e0b; }

.tags-grid { display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }
.tag-item { background: var(--card-bg); padding: 8px 16px; border-radius: 20px; text-decoration: none; color: var(--text); box-shadow: var(--shadow); transition: all 0.3s; }
.tag-item:hover { background: var(--primary); color: white; }

.search-box { max-width: 600px; margin: 20px auto; }
.search-box input { width: 100%; padding: 15px 20px; border: 2px solid var(--border); border-radius: 25px; font-size: 1.1em; background: var(--card-bg); color: var(--text); outline: none; transition: border-color 0.3s; }
.search-box input:focus { border-color: var(--primary); }

footer { text-align: center; padding: 30px; color: var(--text-muted); border-top: 1px solid var(--border); margin-top: 40px; }

@media (max-width: 768px) {
    header h1 { font-size: 1.8em; }
    .collections-grid, .bookmarks-grid { grid-template-columns: 1fr; }
    nav ul { flex-direction: column; align-items: center; }
}
"""


def generate_index_html(collections, metadata):
    """生成主页 HTML"""
    collections_html = ""
    for folder_name, bookmarks in collections.items():
        count = len(bookmarks)
        safe_name = sanitize_filename(folder_name)
        collections_html += f"""
        <div class="collection-card">
            <h3><a href="collections/{safe_name}.html">{html.escape(folder_name)}</a></h3>
            <p class="collection-count">{count} 个书签</p>
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(metadata['title'])}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>📚 {html.escape(metadata['title'])}</h1>
        <p>从 Raindrop.io 导出的书签集合</p>
    </header>
    
    <nav>
        <ul>
            <li><a href="index.html">首页</a></li>
            <li><a href="tags/index.html">标签</a></li>
            <li><a href="search.html">搜索</a></li>
            <li><a href="data.json" download>下载 JSON</a></li>
        </ul>
    </nav>
    
    <main class="container">
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{metadata['total_collections']}</div>
                <div>收藏夹</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{metadata['total_bookmarks']}</div>
                <div>书签</div>
            </div>
        </div>
        
        <h2 style="margin: 30px 0 20px; text-align: center;">收藏夹列表</h2>
        <div class="collections-grid">
            {collections_html}
        </div>
    </main>
    
    <footer>
        <p>最后更新: {metadata['export_time']}</p>
        <p>数据来源: <a href="https://raindrop.io" target="_blank">Raindrop.io</a></p>
    </footer>
</body>
</html>
"""


def generate_collection_html(folder_name, bookmarks, metadata):
    """生成收藏夹页面 HTML"""
    bookmarks_html = ""
    for bm in bookmarks:
        cover_html = f'<img src="{html.escape(bm.get("icon", ""))}" class="bookmark-cover" alt="">' if bm.get("icon") else '<div class="bookmark-cover"></div>'
        
        tags_html = "".join([
            f'<a href="../tags/{sanitize_filename(tag)}.html" class="bookmark-tag">{html.escape(tag)}</a>'
            for tag in bm.get("tags", [])[:5]
        ])
        
        important_class = "bookmark-important" if bm.get("important") else ""
        
        # 提取域名
        domain = ""
        if bm.get("link"):
            try:
                from urllib.parse import urlparse
                domain = urlparse(bm["link"]).netloc
            except:
                pass
        
        bookmarks_html += f"""
        <div class="bookmark-card {important_class}">
            <a href="{html.escape(bm.get('link', '#'))}" target="_blank">
                {cover_html}
            </a>
            <div class="bookmark-content">
                <div class="bookmark-title">
                    <a href="{html.escape(bm.get('link', '#'))}" target="_blank">{html.escape(bm.get('title', '无标题'))}</a>
                </div>
                <p class="bookmark-excerpt">{html.escape(bm.get('description', '')[:150])}</p>
                <p class="bookmark-domain">{html.escape(domain)}</p>
                <div class="bookmark-meta">{tags_html}</div>
            </div>
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(folder_name)} - 书签收藏</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header>
        <h1>📚 {html.escape(folder_name)}</h1>
        <p>{len(bookmarks)} 个书签</p>
    </header>
    
    <nav>
        <ul>
            <li><a href="../index.html">首页</a></li>
            <li><a href="../tags/index.html">标签</a></li>
            <li><a href="../search.html">搜索</a></li>
        </ul>
    </nav>
    
    <main class="container">
        <div class="bookmarks-grid">
            {bookmarks_html}
        </div>
    </main>
    
    <footer>
        <p>最后更新: {metadata['export_time']}</p>
    </footer>
</body>
</html>
"""


def generate_tag_html(tag, bookmarks, metadata):
    """生成标签页面 HTML"""
    bookmarks_html = ""
    for bm in bookmarks:
        cover_html = f'<img src="{html.escape(bm.get("icon", ""))}" class="bookmark-cover" alt="">' if bm.get("icon") else '<div class="bookmark-cover"></div>'
        
        bookmarks_html += f"""
        <div class="bookmark-card">
            <a href="{html.escape(bm.get('link', '#'))}" target="_blank">
                {cover_html}
            </a>
            <div class="bookmark-content">
                <div class="bookmark-title">
                    <a href="{html.escape(bm.get('link', '#'))}" target="_blank">{html.escape(bm.get('title', '无标题'))}</a>
                </div>
                <p class="bookmark-excerpt">{html.escape(bm.get('description', '')[:150])}</p>
                <p class="bookmark-domain">来自: {html.escape(bm.get('folder', ''))}</p>
            </div>
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>标签: {html.escape(tag)} - 书签收藏</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header>
        <h1>🏷️ 标签: {html.escape(tag)}</h1>
        <p>{len(bookmarks)} 个书签</p>
    </header>
    
    <nav>
        <ul>
            <li><a href="../index.html">首页</a></li>
            <li><a href="index.html">所有标签</a></li>
            <li><a href="../search.html">搜索</a></li>
        </ul>
    </nav>
    
    <main class="container">
        <div class="bookmarks-grid">
            {bookmarks_html}
        </div>
    </main>
    
    <footer>
        <p>从 Raindrop.io 导出</p>
    </footer>
</body>
</html>
"""


def generate_tags_index_html(all_tags, metadata):
    """生成标签索引页面"""
    tags_html = ""
    for tag, bookmarks in sorted(all_tags.items()):
        tags_html += f'<a href="{sanitize_filename(tag)}.html" class="tag-item">{html.escape(tag)} ({len(bookmarks)})</a>'
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>所有标签 - 书签收藏</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header>
        <h1>🏷️ 所有标签</h1>
        <p>{len(all_tags)} 个标签</p>
    </header>
    
    <nav>
        <ul>
            <li><a href="../index.html">首页</a></li>
            <li><a href="index.html">所有标签</a></li>
            <li><a href="../search.html">搜索</a></li>
        </ul>
    </nav>
    
    <main class="container">
        <div class="tags-grid">
            {tags_html}
        </div>
    </main>
    
    <footer>
        <p>从 Raindrop.io 导出</p>
    </footer>
</body>
</html>
"""


def generate_search_html(collections, metadata):
    """生成搜索页面"""
    all_bookmarks = []
    for folder_name, bookmarks in collections.items():
        for bm in bookmarks:
            all_bookmarks.append({
                "title": bm.get("title", ""),
                "link": bm.get("link", ""),
                "description": bm.get("description", ""),
                "tags": bm.get("tags", []),
                "folder": folder_name
            })
    
    bookmarks_json = json.dumps(all_bookmarks, ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>搜索书签</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>🔍 搜索书签</h1>
    </header>
    
    <nav>
        <ul>
            <li><a href="index.html">首页</a></li>
            <li><a href="tags/index.html">标签</a></li>
            <li><a href="search.html">搜索</a></li>
        </ul>
    </nav>
    
    <main class="container">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="输入关键词搜索..." autofocus>
        </div>
        <div id="searchResults" class="bookmarks-grid"></div>
    </main>
    
    <footer>
        <p>从 Raindrop.io 导出</p>
    </footer>
    
    <script>
        const bookmarks = {bookmarks_json};
        const input = document.getElementById('searchInput');
        const results = document.getElementById('searchResults');
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function search(query) {{
            if (!query.trim()) {{
                results.innerHTML = '<p style="text-align:center;color:var(--text-muted);">输入关键词开始搜索</p>';
                return;
            }}
            
            const q = query.toLowerCase();
            const filtered = bookmarks.filter(bm => 
                bm.title.toLowerCase().includes(q) ||
                (bm.description && bm.description.toLowerCase().includes(q)) ||
                bm.tags.some(t => t.toLowerCase().includes(q)) ||
                bm.folder.toLowerCase().includes(q)
            );
            
            if (filtered.length === 0) {{
                results.innerHTML = '<p style="text-align:center;color:var(--text-muted);">没有找到匹配的书签</p>';
                return;
            }}
            
            results.innerHTML = filtered.map(bm => `
                <div class="bookmark-card">
                    <div class="bookmark-content">
                        <div class="bookmark-title">
                            <a href="${{escapeHtml(bm.link)}}" target="_blank">${{escapeHtml(bm.title)}}</a>
                        </div>
                        <p class="bookmark-excerpt">${{escapeHtml((bm.description || '').substring(0, 150))}}</p>
                        <p class="bookmark-domain">来自: ${{escapeHtml(bm.folder)}}</p>
                    </div>
                </div>
            `).join('');
        }}
        
        input.addEventListener('input', (e) => search(e.target.value));
        search('');
    </script>
</body>
</html>
"""


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="处理 Raindrop.io 导出的书签文件")
    parser.add_argument("file", nargs="?", help="书签文件路径 (HTML 或 JSON)")
    parser.add_argument("--output", "-o", default="docs", help="输出目录 (默认: docs)")
    parser.add_argument("--title", "-t", default="我的书签收藏", help="网站标题")
    parser.add_argument("--watch", "-w", action="store_true", help="监视文件变化自动重新生成")
    args = parser.parse_args()
    
    if not args.file:
        # 查找默认的导出文件
        export_dir = Path("export")
        if export_dir.exists():
            for ext in [".json", ".html", ".htm"]:
                for f in export_dir.glob(f"*{ext}"):
                    args.file = str(f)
                    print(f"📂 自动找到导出文件: {f}")
                    break
                if args.file:
                    break
        
        if not args.file:
            print("❌ 请指定书签文件路径，或将导出文件放在 export/ 目录下")
            print("\n使用方法:")
            print("  python scripts/process_export.py 书签文件.html")
            print("  python scripts/process_export.py 书签文件.json")
            print("  python scripts/process_export.py  # 自动查找 export/ 目录下的文件")
            return
    
    # 处理书签文件
    print(f"\n🔄 正在处理: {args.file}")
    collections = process_bookmarks_file(args.file)
    
    if not collections:
        print("❌ 没有找到任何书签")
        return
    
    # 生成静态网站
    generate_html_site(collections, args.output, args.title)
    
    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
