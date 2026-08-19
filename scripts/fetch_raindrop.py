#!/usr/bin/env python3
"""
Raindrop.io to GitHub Pages Exporter
从 Raindrop.io 获取所有收藏并生成静态网站
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
import html

# Raindrop.io API 配置
RAINDROP_API_BASE = "https://api.raindrop.io/rest/v1"

def get_raindrop_token():
    """从环境变量获取 Raindrop API Token"""
    token = os.environ.get("RAINDROP_API_TOKEN")
    if not token:
        raise ValueError("请设置环境变量 RAINDROP_API_TOKEN")
    return token

def make_request(endpoint, token, params=None):
    """发送 API 请求"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{RAINDROP_API_BASE}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_all_collections(token):
    """获取所有收藏夹（Collections）"""
    result = make_request("/collections", token)
    collections = result.get("items", [])
    
    # 也获取子收藏夹
    for collection in collections:
        if collection.get("parent"):
            continue  # 跳过子收藏夹，后面单独获取
    
    # 获取根级别的收藏夹（包括嵌套）
    root_collections = [c for c in collections if not c.get("parent")]
    
    # 按层级组织收藏夹
    all_collections = []
    for col in collections:
        all_collections.append({
            "id": col["_id"],
            "title": col["title"],
            "parent": col.get("parent", {}).get("$id") if col.get("parent") else None,
            "color": col.get("color", "#4CAF50"),
            "count": col.get("count", 0),
            "public": col.get("public", False),
            "created": col.get("created"),
            "lastUpdate": col.get("lastUpdate")
        })
    
    return all_collections

def get_all_raindrops(token, collection_id):
    """获取某个收藏夹中的所有书签（支持分页）"""
    all_raindrops = []
    page = 0
    per_page = 50
    
    while True:
        params = {"page": page, "perpage": per_page}
        result = make_request(f"/raindrops/{collection_id}", token, params)
        items = result.get("items", [])
        
        if not items:
            break
        
        all_raindrops.extend(items)
        
        if len(items) < per_page:
            break
        
        page += 1
    
    return all_raindrops

def format_raindrop(raindrop):
    """格式化单个书签数据"""
    return {
        "id": raindrop["_id"],
        "title": raindrop.get("title", "无标题"),
        "link": raindrop.get("link", ""),
        "excerpt": raindrop.get("excerpt", ""),
        "note": raindrop.get("note", ""),
        "tags": raindrop.get("tags", []),
        "important": raindrop.get("important", False),
        "cover": raindrop.get("cover", ""),
        "media": raindrop.get("media", []),
        "created": raindrop.get("created"),
        "lastUpdate": raindrop.get("lastUpdate"),
        "domain": raindrop.get("domain", ""),
        "type": raindrop.get("type", "link")  # link, article, image, video, document
    }

def fetch_all_bookmarks(token):
    """获取所有收藏夹和书签"""
    print("正在获取收藏夹列表...")
    collections = get_all_collections(token)
    
    all_data = {
        "collections": {},
        "metadata": {
            "export_time": datetime.now().isoformat(),
            "total_collections": len(collections),
            "total_bookmarks": 0
        }
    }
    
    for collection in collections:
        col_id = collection["id"]
        print(f"正在获取收藏夹 '{collection['title']}' 中的书签...")
        
        raindrops = get_all_raindrops(token, col_id)
        formatted_raindrops = [format_raindrop(r) for r in raindrops]
        
        all_data["collections"][str(col_id)] = {
            "info": collection,
            "bookmarks": formatted_raindrops
        }
        
        all_data["metadata"]["total_bookmarks"] += len(formatted_raindrops)
        print(f"  - 获取了 {len(formatted_raindrops)} 个书签")
    
    print(f"\n总计: {all_data['metadata']['total_collections']} 个收藏夹, {all_data['metadata']['total_bookmarks']} 个书签")
    return all_data

def generate_html_site(data, output_dir):
    """生成静态 HTML 网站"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 生成主页面
    index_html = generate_index_html(data)
    (output_path / "index.html").write_text(index_html, encoding="utf-8")
    
    # 为每个收藏夹生成单独页面
    collections_dir = output_path / "collections"
    collections_dir.mkdir(exist_ok=True)
    
    for col_id, col_data in data["collections"].items():
        col_html = generate_collection_html(col_data, data)
        safe_title = sanitize_filename(col_data["info"]["title"])
        (collections_dir / f"{safe_title}.html").write_text(col_html, encoding="utf-8")
    
    # 生成标签页面
    tags_dir = output_path / "tags"
    tags_dir.mkdir(exist_ok=True)
    
    all_tags = {}
    for col_id, col_data in data["collections"].items():
        for bookmark in col_data["bookmarks"]:
            for tag in bookmark.get("tags", []):
                if tag not in all_tags:
                    all_tags[tag] = []
                all_tags[tag].append({**bookmark, "collection": col_data["info"]})
    
    for tag, bookmarks in all_tags.items():
        tag_html = generate_tag_html(tag, bookmarks)
        safe_tag = sanitize_filename(tag)
        (tags_dir / f"{safe_tag}.html").write_text(tag_html, encoding="utf-8")
    
    # 生成标签索引
    tags_index_html = generate_tags_index_html(all_tags)
    (tags_dir / "index.html").write_text(tags_index_html, encoding="utf-8")
    
    # 生成 CSS 样式
    css = generate_css()
    (output_path / "style.css").write_text(css, encoding="utf-8")
    
    # 生成 JSON 数据（方便他人导入）
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    (output_path / "data.json").write_text(json_data, encoding="utf-8")
    
    # 生成搜索页面
    search_html = generate_search_html(data)
    (output_path / "search.html").write_text(search_html, encoding="utf-8")
    
    print(f"\n静态网站已生成到: {output_path}")

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

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* Header */
header {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    padding: 40px 20px;
    text-align: center;
    margin-bottom: 30px;
}

header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
}

header p {
    opacity: 0.9;
    font-size: 1.1em;
}

/* Navigation */
nav {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 15px 20px;
    position: sticky;
    top: 0;
    z-index: 100;
}

nav ul {
    list-style: none;
    display: flex;
    gap: 20px;
    justify-content: center;
    flex-wrap: wrap;
}

nav a {
    color: var(--text);
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 20px;
    transition: all 0.3s;
}

nav a:hover {
    background: var(--primary);
    color: white;
}

/* Stats */
.stats {
    display: flex;
    gap: 20px;
    justify-content: center;
    margin: 20px 0;
    flex-wrap: wrap;
}

.stat-item {
    background: var(--card-bg);
    padding: 15px 25px;
    border-radius: var(--radius);
    text-align: center;
    box-shadow: var(--shadow);
}

.stat-number {
    font-size: 2em;
    font-weight: bold;
    color: var(--primary);
}

/* Collection Grid */
.collections-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.collection-card {
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 20px;
    box-shadow: var(--shadow);
    transition: transform 0.3s, box-shadow 0.3s;
}

.collection-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.collection-card h3 {
    color: var(--primary);
    margin-bottom: 10px;
    font-size: 1.3em;
}

.collection-count {
    color: var(--text-muted);
    font-size: 0.9em;
}

/* Bookmark Grid */
.bookmarks-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.bookmark-card {
    background: var(--card-bg);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: transform 0.3s, box-shadow 0.3s;
}

.bookmark-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.bookmark-cover {
    width: 100%;
    height: 160px;
    object-fit: cover;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bookmark-content {
    padding: 15px;
}

.bookmark-title {
    font-size: 1.1em;
    font-weight: 600;
    margin-bottom: 8px;
    color: var(--text);
}

.bookmark-title a {
    color: inherit;
    text-decoration: none;
}

.bookmark-title a:hover {
    color: var(--primary);
}

.bookmark-excerpt {
    color: var(--text-muted);
    font-size: 0.9em;
    margin-bottom: 10px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.bookmark-meta {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 0.8em;
}

.bookmark-tag {
    background: var(--primary);
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    text-decoration: none;
    transition: opacity 0.3s;
}

.bookmark-tag:hover {
    opacity: 0.8;
}

.bookmark-domain {
    color: var(--text-muted);
    font-size: 0.85em;
}

.bookmark-important {
    color: #f59e0b;
}

/* Tags Page */
.tags-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 20px 0;
}

.tag-item {
    background: var(--card-bg);
    padding: 8px 16px;
    border-radius: 20px;
    text-decoration: none;
    color: var(--text);
    box-shadow: var(--shadow);
    transition: all 0.3s;
}

.tag-item:hover {
    background: var(--primary);
    color: white;
}

/* Search */
.search-box {
    max-width: 600px;
    margin: 20px auto;
}

.search-box input {
    width: 100%;
    padding: 15px 20px;
    border: 2px solid var(--border);
    border-radius: 25px;
    font-size: 1.1em;
    background: var(--card-bg);
    color: var(--text);
    outline: none;
    transition: border-color 0.3s;
}

.search-box input:focus {
    border-color: var(--primary);
}

/* Footer */
footer {
    text-align: center;
    padding: 30px;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
    margin-top: 40px;
}

/* Responsive */
@media (max-width: 768px) {
    header h1 {
        font-size: 1.8em;
    }
    
    .collections-grid,
    .bookmarks-grid {
        grid-template-columns: 1fr;
    }
    
    nav ul {
        flex-direction: column;
        align-items: center;
    }
}

/* Type badges */
.type-link::before { content: "🔗 "; }
.type-article::before { content: "📄 "; }
.type-video::before { content: "🎬 "; }
.type-image::before { content: "🖼️ "; }
.type-document::before { content: "📎 "; }
"""

def generate_index_html(data):
    """生成主页 HTML"""
    collections_html = ""
    for col_id, col_data in data["collections"].items():
        info = col_data["info"]
        count = len(col_data["bookmarks"])
        safe_title = sanitize_filename(info["title"])
        collections_html += f"""
        <div class="collection-card">
            <h3><a href="collections/{safe_title}.html">{html.escape(info['title'])}</a></h3>
            <p class="collection-count">{count} 个书签</p>
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的书签收藏</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>📚 我的书签收藏</h1>
        <p>从 Raindrop.io 同步的书签集合</p>
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
                <div class="stat-number">{data['metadata']['total_collections']}</div>
                <div>收藏夹</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{data['metadata']['total_bookmarks']}</div>
                <div>书签</div>
            </div>
        </div>
        
        <h2 style="margin: 30px 0 20px; text-align: center;">收藏夹列表</h2>
        <div class="collections-grid">
            {collections_html}
        </div>
    </main>
    
    <footer>
        <p>最后更新: {data['metadata']['export_time']}</p>
        <p>数据来源: <a href="https://raindrop.io" target="_blank">Raindrop.io</a></p>
    </footer>
</body>
</html>
"""

def generate_collection_html(col_data, all_data):
    """生成收藏夹页面 HTML"""
    info = col_data["info"]
    bookmarks = col_data["bookmarks"]
    
    bookmarks_html = ""
    for bm in bookmarks:
        cover_html = f'<img src="{html.escape(bm["cover"])}" class="bookmark-cover" alt="">' if bm.get("cover") else '<div class="bookmark-cover"></div>'
        
        tags_html = "".join([
            f'<a href="../tags/{sanitize_filename(tag)}.html" class="bookmark-tag">{html.escape(tag)}</a>'
            for tag in bm.get("tags", [])[:5]  # 最多显示5个标签
        ])
        
        important_class = "bookmark-important" if bm.get("important") else ""
        type_class = f"type-{bm.get('type', 'link')}"
        
        bookmarks_html += f"""
        <div class="bookmark-card {important_class}">
            <a href="{html.escape(bm['link'])}" target="_blank">
                {cover_html}
            </a>
            <div class="bookmark-content">
                <div class="bookmark-title {type_class}">
                    <a href="{html.escape(bm['link'])}" target="_blank">{html.escape(bm['title'])}</a>
                </div>
                <p class="bookmark-excerpt">{html.escape(bm.get('excerpt', '')[:150])}</p>
                <p class="bookmark-domain">{html.escape(bm.get('domain', ''))}</p>
                <div class="bookmark-meta">{tags_html}</div>
            </div>
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(info['title'])} - 书签收藏</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header>
        <h1>📚 {html.escape(info['title'])}</h1>
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
        <p>最后更新: {all_data['metadata']['export_time']}</p>
    </footer>
</body>
</html>
"""

def generate_tag_html(tag, bookmarks):
    """生成标签页面 HTML"""
    bookmarks_html = ""
    for bm in bookmarks:
        cover_html = f'<img src="{html.escape(bm.get("cover", ""))}" class="bookmark-cover" alt="">' if bm.get("cover") else '<div class="bookmark-cover"></div>'
        
        bookmarks_html += f"""
        <div class="bookmark-card">
            <a href="{html.escape(bm['link'])}" target="_blank">
                {cover_html}
            </a>
            <div class="bookmark-content">
                <div class="bookmark-title">
                    <a href="{html.escape(bm['link'])}" target="_blank">{html.escape(bm['title'])}</a>
                </div>
                <p class="bookmark-excerpt">{html.escape(bm.get('excerpt', '')[:150])}</p>
                <p class="bookmark-domain">来自: {html.escape(bm.get('collection', {}).get('title', ''))}</p>
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
        <p>从 Raindrop.io 同步</p>
    </footer>
</body>
</html>
"""

def generate_tags_index_html(all_tags):
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
        <p>从 Raindrop.io 同步</p>
    </footer>
</body>
</html>
"""

def generate_search_html(data):
    """生成搜索页面"""
    # 将所有书签数据嵌入到 JavaScript 中
    all_bookmarks = []
    for col_id, col_data in data["collections"].items():
        for bm in col_data["bookmarks"]:
            all_bookmarks.append({
                "title": bm["title"],
                "link": bm["link"],
                "excerpt": bm.get("excerpt", ""),
                "tags": bm.get("tags", []),
                "collection": col_data["info"]["title"]
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
        <p>从 Raindrop.io 同步</p>
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
                bm.excerpt.toLowerCase().includes(q) ||
                bm.tags.some(t => t.toLowerCase().includes(q)) ||
                bm.collection.toLowerCase().includes(q)
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
                        <p class="bookmark-excerpt">${{escapeHtml(bm.excerpt.substring(0, 150))}}</p>
                        <p class="bookmark-domain">来自: ${{escapeHtml(bm.collection)}}</p>
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
    
    parser = argparse.ArgumentParser(description="从 Raindrop.io 导出书签到 GitHub Pages")
    parser.add_argument("--output", "-o", default="docs", help="输出目录 (默认: docs)")
    parser.add_argument("--token", "-t", help="Raindrop API Token (或设置环境变量 RAINDROP_API_TOKEN)")
    args = parser.parse_args()
    
    # 获取 token
    token = args.token or get_raindrop_token()
    
    # 获取所有数据
    data = fetch_all_bookmarks(token)
    
    # 生成静态网站
    generate_html_site(data, args.output)
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
