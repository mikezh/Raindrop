#!/usr/bin/env python3
"""
Raindrop.io 导出文件处理器 - 心情看板版
生成类似 Pinterest 的瀑布流视觉书签墙
"""

import os
import re
import json
import html
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse


class BookmarkHTMLParser(HTMLParser):
    """解析 Netscape Bookmark HTML 格式（支持 Raindrop.io 扩展属性）"""
    
    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.current_folder = "未分类"
        self.current_bookmark = None
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
            
            # 解析标签（Raindrop 使用 TAGS 属性）
            tags_str = attrs_dict.get("tags", "")
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
            
            self.current_bookmark = {
                "title": "",
                "link": attrs_dict.get("href", ""),
                "tags": tags,
                "created": attrs_dict.get("add_date", ""),
                "icon": attrs_dict.get("data-cover", "") or attrs_dict.get("icon", ""),  # Raindrop 使用 DATA-COVER
                "description": "",
                "important": attrs_dict.get("data-important", "false").lower() == "true"
            }
        elif tag == "dd":
            self.in_dd = True
            self.dd_text = ""
            
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
            if self.current_folder != "未分类":
                self.current_folder = "未分类"
                
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
            
        if self.in_h3:
            self.current_folder = data
        elif self.in_a and self.current_bookmark:
            self.current_bookmark["title"] = data
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
    
    collections = {}
    for bm in parser.bookmarks:
        folder = bm.get("folder", "未分类")
        if folder not in collections:
            collections[folder] = []
        collections[folder].append(bm)
    
    return collections


def parse_json_bookmarks(file_path):
    """解析 JSON 格式的书签文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        collections = {}
        for item in data:
            folder = item.get("collection", {})
            if isinstance(folder, dict):
                folder = folder.get("title", "未分类")
            else:
                folder = str(folder) if folder else "未分类"
            
            if folder not in collections:
                collections[folder] = []
            
            cover = ""
            if item.get("cover"):
                cover = item["cover"]
            elif item.get("media") and len(item["media"]) > 0:
                cover = item["media"][0].get("link", "")
            
            collections[folder].append({
                "title": item.get("title", "无标题"),
                "link": item.get("link", ""),
                "tags": item.get("tags", []),
                "description": item.get("excerpt", "") or item.get("note", ""),
                "created": item.get("created", ""),
                "icon": cover,
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
        with open(file_path, 'r', encoding='utf-8') as f:
            first_chars = f.read(100)
        
        if first_chars.strip().startswith('{') or first_chars.strip().startswith('['):
            print(f"📄 自动检测: JSON 格式")
            return parse_json_bookmarks(file_path)
        else:
            print(f"📄 自动检测: HTML 格式")
            return parse_html_bookmarks(file_path)


def get_domain(url):
    """提取域名"""
    try:
        return urlparse(url).netloc
    except:
        return ""


def get_favicon_url(domain):
    """获取 favicon URL"""
    if not domain:
        return ""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"


def generate_css():
    """生成心情看板风格 CSS"""
    return """
/* 心情看板 - Mood Board Style */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --bg: #0a0a0b;
    --card-bg: #141416;
    --card-hover: #1a1a1d;
    --text: #ffffff;
    --text-muted: #8b8b8e;
    --accent: #6366f1;
    --accent-glow: rgba(99, 102, 241, 0.3);
    --border: rgba(255, 255, 255, 0.06);
    --radius: 16px;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    min-height: 100vh;
}

/* Header */
.header {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(10, 10, 11, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
}

.header-inner {
    max-width: 1800px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}

.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text);
    text-decoration: none;
}

.logo-icon {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

/* Filter Tabs */
.filter-tabs {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.filter-tab {
    padding: 8px 16px;
    border-radius: 20px;
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
}

.filter-tab:hover {
    background: var(--card-bg);
    color: var(--text);
}

.filter-tab.active {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
}

/* Search */
.search-wrapper {
    position: relative;
    width: 280px;
}

.search-input {
    width: 100%;
    padding: 10px 16px 10px 40px;
    border-radius: 12px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 0.875rem;
    outline: none;
    transition: all 0.2s;
}

.search-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
}

.search-input::placeholder {
    color: var(--text-muted);
}

.search-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    pointer-events: none;
}

/* Main Content */
.main {
    max-width: 1800px;
    margin: 0 auto;
    padding: 24px;
}

/* Masonry Grid */
.masonry {
    column-count: 5;
    column-gap: 16px;
}

@media (max-width: 1600px) { .masonry { column-count: 4; } }
@media (max-width: 1200px) { .masonry { column-count: 3; } }
@media (max-width: 900px) { .masonry { column-count: 2; } }
@media (max-width: 600px) { .masonry { column-count: 1; } }

/* Card */
.card {
    break-inside: avoid;
    margin-bottom: 16px;
    border-radius: var(--radius);
    background: var(--card-bg);
    overflow: hidden;
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
    text-decoration: none;
    display: block;
    border: none;
    box-shadow: none;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.card-cover {
    width: 100%;
    display: block;
    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%);
}

.card-no-cover {
    width: 100%;
    aspect-ratio: 16/10;
    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%);
    display: flex;
    align-items: center;
    justify-content: center;
}

.card-no-cover-text {
    font-size: 2rem;
    opacity: 0.3;
}

.card-body {
    padding: 14px;
}

.card-title {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text);
    margin-bottom: 6px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.4;
}

.card-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
}

.card-favicon {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    opacity: 0.6;
}

.card-domain {
    font-size: 0.75rem;
    color: var(--text-muted);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 8px;
}

.card-tag {
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    background: rgba(99, 102, 241, 0.15);
    color: var(--accent);
    text-decoration: none;
    transition: all 0.2s;
}

.card-tag:hover {
    background: var(--accent);
    color: white;
}

.card-important {
    border: 2px solid #f59e0b;
}

.card-important .card-body::before {
    content: "⭐";
    position: absolute;
    top: 10px;
    right: 10px;
}

/* Collection Section */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
}

.section-title {
    font-size: 1.5rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 12px;
}

.section-count {
    font-size: 0.875rem;
    color: var(--text-muted);
    font-weight: 400;
}

/* Stats Bar */
.stats-bar {
    display: flex;
    gap: 24px;
    padding: 20px 0;
    margin-bottom: 20px;
}

.stat {
    display: flex;
    align-items: baseline;
    gap: 8px;
}

.stat-value {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--accent);
}

.stat-label {
    font-size: 0.875rem;
    color: var(--text-muted);
}

/* Empty State */
.empty {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.empty-icon {
    font-size: 4rem;
    margin-bottom: 16px;
    opacity: 0.3;
}

/* Lightbox */
.lightbox {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
}

.lightbox.active {
    display: flex;
    align-items: center;
    justify-content: center;
}

.lightbox-content {
    max-width: 90vw;
    max-height: 90vh;
    border-radius: 12px;
    overflow: hidden;
}

.lightbox-close {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
}

/* Footer */
.footer {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
    font-size: 0.875rem;
    border-top: 1px solid var(--border);
    margin-top: 40px;
}

.footer a {
    color: var(--accent);
    text-decoration: none;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.card {
    animation: fadeIn 0.4s ease-out;
    animation-fill-mode: both;
}

.card:nth-child(1) { animation-delay: 0.02s; }
.card:nth-child(2) { animation-delay: 0.04s; }
.card:nth-child(3) { animation-delay: 0.06s; }
.card:nth-child(4) { animation-delay: 0.08s; }
.card:nth-child(5) { animation-delay: 0.10s; }
.card:nth-child(n+6) { animation-delay: 0.12s; }

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}
"""


def sort_bookmarks_by_time(bookmarks):
    """按时间倒序排列书签（最新的在前）"""
    def get_timestamp(bm):
        created = bm.get("created", "")
        if created:
            try:
                return int(created)
            except:
                return 0
        return 0
    
    return sorted(bookmarks, key=get_timestamp, reverse=True)


def generate_index_html(collections, metadata, all_tags):
    """生成主页"""
    all_bookmarks = []
    for folder, bookmarks in collections.items():
        for bm in bookmarks:
            bm["_folder"] = folder
            all_bookmarks.append(bm)
    
    # 按时间倒序排列
    all_bookmarks = sort_bookmarks_by_time(all_bookmarks)
    
    # 生成收藏夹过滤标签
    folder_tabs = '<a href="#" class="filter-tab active" data-filter="all">全部</a>'
    for folder in collections.keys():
        safe_name = sanitize_filename(folder)
        folder_tabs += f'<a href="collections/{safe_name}.html" class="filter-tab">{html.escape(folder)}</a>'
    
    # 生成标签过滤（显示所有标签）
    tag_tabs = ""
    sorted_tags = sorted(all_tags.items(), key=lambda x: len(x[1]), reverse=True)
    for tag, _ in sorted_tags:
        safe_tag = sanitize_filename(tag)
        tag_tabs += f'<a href="tags/{safe_tag}.html" class="filter-tab">{html.escape(tag)}</a>'
    
    # 生成卡片
    cards_html = ""
    for bm in all_bookmarks:
        cards_html += generate_card_html(bm)
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(metadata['title'])}</title>
    <link rel="stylesheet" href="style.css">
    <meta property="og:title" content="{html.escape(metadata['title'])}">
    <meta property="og:description" content="{metadata['total_bookmarks']} 个精选书签">
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <a href="index.html" class="logo">
                <div class="logo-icon">📚</div>
                <span>{html.escape(metadata['title'])}</span>
            </a>
            
            <nav class="filter-tabs">
                {folder_tabs}
            </nav>
            
            <nav class="filter-tabs">
                {tag_tabs}
            </nav>
            
            <div class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input type="text" class="search-input" id="search" placeholder="搜索书签...">
            </div>
        </div>
    </header>
    
    <main class="main">
        <div class="stats-bar">
            <div class="stat">
                <span class="stat-value">{metadata['total_bookmarks']}</span>
                <span class="stat-label">个书签</span>
            </div>
            <div class="stat">
                <span class="stat-value">{metadata['total_collections']}</span>
                <span class="stat-label">个收藏夹</span>
            </div>
            <div class="stat">
                <span class="stat-value">{len(all_tags)}</span>
                <span class="stat-label">个标签</span>
            </div>
        </div>
        
        <div class="masonry" id="grid">
            {cards_html}
        </div>
    </main>
    
    <footer class="footer">
        <p>最后更新: {metadata['export_time']}</p>
        <p>数据来源: <a href="https://raindrop.io" target="_blank">Raindrop.io</a></p>
    </footer>
    
    <script src="app.js"></script>
</body>
</html>
"""


def generate_collection_html(folder_name, bookmarks, metadata):
    """生成收藏夹页面"""
    # 按时间倒序排列
    bookmarks = sort_bookmarks_by_time(bookmarks)
    
    cards_html = ""
    for bm in bookmarks:
        cards_html += generate_card_html(bm, tag_link_prefix="../tags/")
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(folder_name)} - {html.escape(metadata['title'])}</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <a href="../index.html" class="logo">
                <div class="logo-icon">📚</div>
                <span>{html.escape(metadata['title'])}</span>
            </a>
            
            <a href="../index.html" class="filter-tab">← 返回全部</a>
        </div>
    </header>
    
    <main class="main">
        <div class="section-header">
            <h1 class="section-title">
                {html.escape(folder_name)}
                <span class="section-count">{len(bookmarks)} 个书签</span>
            </h1>
        </div>
        
        <div class="masonry">
            {cards_html}
        </div>
    </main>
    
    <footer class="footer">
        <p>最后更新: {metadata['export_time']}</p>
    </footer>
</body>
</html>
"""


def generate_card_html(bm, tag_link_prefix="tags/"):
    """生成单个卡片 HTML"""
    title = bm.get("title", "无标题")
    link = bm.get("link", "#")
    description = bm.get("description", "")
    cover = bm.get("icon", "")
    tags = bm.get("tags", [])
    important = bm.get("important", False)
    domain = get_domain(link)
    favicon = get_favicon_url(domain)
    
    important_class = " card-important" if important else ""
    
    # 封面图
    if cover:
        cover_html = f'<img src="{html.escape(cover)}" class="card-cover" alt="" loading="lazy">'
    else:
        # 使用标题首字符作为占位
        first_char = title[0] if title else "📌"
        cover_html = f'<div class="card-no-cover"><span class="card-no-cover-text">{html.escape(first_char)}</span></div>'
    
    # 标签（可点击）
    tags_html = ""
    if tags:
        tags_html = '<div class="card-tags">' + "".join([
            f'<a href="{tag_link_prefix}{sanitize_filename(tag)}.html" class="card-tag">{html.escape(tag)}</a>'
            for tag in tags[:3]
        ]) + '</div>'
    
    return f"""<a href="{html.escape(link)}" target="_blank" rel="noopener" class="card{important_class}" title="{html.escape(title)}">
    {cover_html}
    <div class="card-body">
        <div class="card-title">{html.escape(title)}</div>
        <div class="card-meta">
            <img src="{html.escape(favicon)}" class="card-favicon" alt="" loading="lazy">
            <span class="card-domain">{html.escape(domain)}</span>
        </div>
        {tags_html}
    </div>
</a>"""


def generate_tag_html(tag, bookmarks, metadata, all_tags):
    """生成标签页面"""
    # 按时间倒序排列
    bookmarks = sort_bookmarks_by_time(bookmarks)
    
    cards_html = ""
    for bm in bookmarks:
        cards_html += generate_card_html(bm, tag_link_prefix="../tags/")
    
    # 相关标签
    related_tags_html = ""
    sorted_tags = sorted(all_tags.items(), key=lambda x: len(x[1]), reverse=True)[:15]
    for t, _ in sorted_tags:
        safe_t = sanitize_filename(t)
        active_class = " active" if t == tag else ""
        related_tags_html += f'<a href="{safe_t}.html" class="filter-tab{active_class}">{html.escape(t)} ({len(all_tags[t])})</a>'
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>#{html.escape(tag)} - {html.escape(metadata['title'])}</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <a href="../index.html" class="logo">
                <div class="logo-icon">📚</div>
                <span>{html.escape(metadata['title'])}</span>
            </a>
            
            <nav class="filter-tabs">
                {related_tags_html}
            </nav>
        </div>
    </header>
    
    <main class="main">
        <div class="section-header">
            <h1 class="section-title">
                #{html.escape(tag)}
                <span class="section-count">{len(bookmarks)} 个书签</span>
            </h1>
        </div>
        
        <div class="masonry">
            {cards_html}
        </div>
    </main>
    
    <footer class="footer">
        <p>最后更新: {metadata['export_time']}</p>
    </footer>
</body>
</html>
"""


def generate_js():
    """生成 JavaScript"""
    return """
// 搜索功能
const searchInput = document.getElementById('search');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const cards = document.querySelectorAll('.card');
        
        cards.forEach(card => {
            const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
            const domain = card.querySelector('.card-domain')?.textContent.toLowerCase() || '';
            const tags = Array.from(card.querySelectorAll('.card-tag'))
                .map(t => t.textContent.toLowerCase())
                .join(' ');
            
            const match = title.includes(query) || domain.includes(query) || tags.includes(query);
            card.style.display = match ? '' : 'none';
        });
    });
}

// 图片加载失败处理
document.querySelectorAll('.card-cover').forEach(img => {
    img.addEventListener('error', function() {
        const card = this.closest('.card');
        const title = card.querySelector('.card-title')?.textContent || '📌';
        const firstChar = title[0];
        this.outerHTML = `<div class="card-no-cover"><span class="card-no-cover-text">${firstChar}</span></div>`;
    });
});

// 无限滚动提示
console.log('📚 心情看板已加载');
"""


def generate_html_site(collections, output_dir, title="我的书签收藏"):
    """生成静态网站"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    total_bookmarks = sum(len(bms) for bms in collections.values())
    total_collections = len(collections)
    
    # 收集所有标签
    all_tags = {}
    for folder, bookmarks in collections.items():
        for bm in bookmarks:
            for tag in bm.get("tags", []):
                if tag not in all_tags:
                    all_tags[tag] = []
                all_tags[tag].append(bm)
    
    metadata = {
        "export_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_collections": total_collections,
        "total_bookmarks": total_bookmarks,
        "title": title
    }
    
    # 生成主页
    (output_path / "index.html").write_text(
        generate_index_html(collections, metadata, all_tags),
        encoding="utf-8"
    )
    
    # 生成收藏夹页面
    collections_dir = output_path / "collections"
    collections_dir.mkdir(exist_ok=True)
    
    for folder_name, bookmarks in collections.items():
        safe_name = sanitize_filename(folder_name)
        (collections_dir / f"{safe_name}.html").write_text(
            generate_collection_html(folder_name, bookmarks, metadata),
            encoding="utf-8"
        )
    
    # 生成标签页面
    tags_dir = output_path / "tags"
    tags_dir.mkdir(exist_ok=True)
    
    for tag, bookmarks in all_tags.items():
        safe_tag = sanitize_filename(tag)
        (tags_dir / f"{safe_tag}.html").write_text(
            generate_tag_html(tag, bookmarks, metadata, all_tags),
            encoding="utf-8"
        )
    
    # 生成 CSS
    (output_path / "style.css").write_text(generate_css(), encoding="utf-8")
    
    # 生成 JS
    (output_path / "app.js").write_text(generate_js(), encoding="utf-8")
    
    # 生成 JSON 数据
    json_data = {"collections": collections, "metadata": metadata}
    (output_path / "data.json").write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"\n✅ 心情看板已生成到: {output_path}")
    print(f"   📊 {total_collections} 个收藏夹, {total_bookmarks} 个书签, {len(all_tags)} 个标签")
    
    return metadata


def sanitize_filename(name):
    """清理文件名"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip() or "untitled"


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成心情看板风格的书签网站")
    parser.add_argument("file", nargs="?", help="书签文件路径")
    parser.add_argument("--output", "-o", default="docs", help="输出目录")
    parser.add_argument("--title", "-t", default="我的书签收藏", help="网站标题")
    args = parser.parse_args()
    
    if not args.file:
        export_dir = Path("export")
        if export_dir.exists():
            for ext in [".json", ".html", ".htm"]:
                for f in export_dir.glob(f"*{ext}"):
                    if f.name != ".gitkeep":
                        args.file = str(f)
                        print(f"📂 找到导出文件: {f}")
                        break
                if args.file:
                    break
        
        if not args.file:
            print("❌ 请指定书签文件，或将文件放在 export/ 目录")
            return
    
    print(f"\n🔄 处理中: {args.file}")
    collections = process_bookmarks_file(args.file)
    
    if not collections:
        print("❌ 没有找到书签")
        return
    
    generate_html_site(collections, args.output, args.title)
    print("\n✨ 完成！")


if __name__ == "__main__":
    main()
