# 🌧️ Raindrop.io → GitHub Pages 书签导出工具

将你的 Raindrop.io 收藏完美复制到 GitHub，生成一个漂亮的公开网站，可以分享给任何人！

## ✨ 功能特点

- 📁 **支持导出文件** - 处理 Raindrop.io 导出的 HTML/JSON 文件
- 🎨 **精美界面** - 响应式设计，支持深色模式
- 📂 **完整结构** - 保留所有收藏夹、标签、重要标记
- 🔍 **内置搜索** - 前端实时搜索，无需后端
- 📊 **JSON 导出** - 提供 JSON 数据，方便他人导入
- 🏷️ **标签聚合** - 按标签浏览所有相关书签
- 📱 **移动适配** - 完美支持手机和平板访问
- 🆓 **完全免费** - 不需要 Raindrop Pro 订阅

## 🚀 快速开始

### 第一步：从 Raindrop.io 导出书签

1. 登录 [Raindrop.io](https://app.raindrop.io)
2. 点击左侧边栏的 **设置** ⚙️ 图标
3. 找到 **导出** (Export) 选项
4. 点击 **导出所有书签** (Export all bookmarks)
5. 选择 **HTML** 格式（推荐）或 **JSON** 格式
6. 下载导出文件

> 💡 **提示**：导出文件通常命名为 `raindrop_export.html` 或类似名称

### 第二步：上传到 GitHub 仓库

**方式 A：直接在 GitHub 网页上传**

1. 打开你的仓库：https://github.com/你的用户名/Raindrop
2. 创建 `export` 文件夹（点击 Add file → Create new file，输入 `export/`）
3. 点击 **Add file** → **Upload files**
4. 将导出的书签文件拖拽上传到 `export/` 文件夹
5. 点击 **Commit changes**

**方式 B：使用 Git 命令行**

```bash
# 克隆仓库
git clone https://github.com/你的用户名/Raindrop.git
cd Raindrop

# 创建 export 目录并放入导出文件
mkdir -p export
cp ~/Downloads/raindrop_export.html export/

# 提交并推送
git add export/
git commit -m "📥 添加书签导出文件"
git push
```

### 第三步：启用 GitHub Pages

1. 进入仓库的 **Settings** → **Pages**
2. **Source** 选择 **GitHub Actions**
3. 保存

### 第四步：触发构建

上传文件后，GitHub Actions 会自动运行构建。你也可以：

1. 进入 **Actions** 标签页
2. 选择 **Build Bookmarks Site** 工作流
3. 点击 **Run workflow**

### 第五步：访问你的书签网站

几分钟后，你的书签网站将在以下地址可用：
```
https://你的用户名.github.io/Raindrop/
```

---

## 📁 项目结构

```
Raindrop/
├── export/                    # 放置导出的书签文件
│   └── raindrop_export.html   # 从 Raindrop.io 导出的文件
├── scripts/
│   └── process_export.py      # 处理导出文件并生成网站
├── .github/
│   └── workflows/
│       └── sync-raindrop.yml  # GitHub Actions 工作流
├── docs/                      # 生成的网站文件（自动创建）
│   ├── index.html             # 主页
│   ├── style.css              # 样式
│   ├── data.json              # 完整 JSON 数据
│   ├── search.html            # 搜索页面
│   ├── collections/           # 各收藏夹页面
│   └── tags/                  # 标签页面
└── README.md
```

---

## 🔄 更新书签

当你有新的书签想要同步时：

1. 在 Raindrop.io 重新导出书签文件
2. 上传新的导出文件到 `export/` 文件夹（覆盖旧文件）
3. GitHub Actions 会自动重新构建网站

---

## 💻 本地运行

```bash
# 安装依赖（无需额外安装，使用 Python 标准库）

# 处理导出文件
python scripts/process_export.py export/raindrop_export.html

# 或自动查找 export 目录下的文件
python scripts/process_export.py

# 指定输出目录
python scripts/process_export.py export/raindrop_export.html --output my-site

# 自定义网站标题
python scripts/process_export.py export/raindrop_export.html --title "我的收藏"
```

生成的网站文件在 `docs/` 目录下，可以直接用浏览器打开 `docs/index.html` 预览。

---

## 🎨 自定义样式

你可以修改 `scripts/process_export.py` 中的 `generate_css()` 函数来自定义网站样式：

- 主题颜色（`--primary`）
- 卡片样式
- 字体
- 布局

---

## 📊 支持的导出格式

### HTML 格式（推荐）

标准的 Netscape Bookmark HTML 格式，大多数书签管理器都支持。

```html
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>收藏夹名称</H3>
    <DL><p>
        <DT><A HREF="https://example.com">书签标题</A>
        <DD>书签描述
    </DL><p>
</DL><p>
```

### JSON 格式

Raindrop.io 的 JSON 导出格式：

```json
[
  {
    "title": "书签标题",
    "link": "https://example.com",
    "tags": ["tag1", "tag2"],
    "excerpt": "描述",
    "collection": {"title": "收藏夹名称"},
    "important": false
  }
]
```

---

## ❓ 常见问题

### Q: 为什么需要手动导出？

A: Raindrop.io 的 API 需要 Pro 订阅才能使用。这个方案完全免费，只需要手动导出一次即可。

### Q: 多久更新一次？

A: 每次上传新的导出文件时自动更新。建议每周或每月导出一次。

### Q: 支持多少书签？

A: 没有限制！GitHub Pages 支持大型静态网站。

### Q: 可以自定义域名吗？

A: 可以！在仓库 Settings → Pages → Custom domain 中设置。

---

## 📝 更新日志

### v1.1.0
- 添加导出文件处理方案（免费用户适用）
- 支持 HTML 和 JSON 两种导出格式
- 简化 GitHub Actions 工作流

### v1.0.0
- 初始版本

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

<p align="center">
  用 ❤️ 制作 | 数据来源: <a href="https://raindrop.io">Raindrop.io</a>
</p>
