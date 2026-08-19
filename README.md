# 🌧️ Raindrop.io → GitHub Pages 书签导出工具

将你的 Raindrop.io 收藏完美复制到 GitHub，生成一个漂亮的公开网站，可以分享给任何人！

## ✨ 功能特点

- 🔄 **自动同步** - 通过 GitHub Actions 每6小时自动同步一次
- 🎨 **精美界面** - 响应式设计，支持深色模式
- 📂 **完整结构** - 保留所有收藏夹、标签、重要标记
- 🔍 **内置搜索** - 前端实时搜索，无需后端
- 📊 **JSON 导出** - 提供 JSON 数据，方便他人导入
- 🏷️ **标签聚合** - 按标签浏览所有相关书签
- 📱 **移动适配** - 完美支持手机和平板访问

## 🚀 快速开始

### 第一步：获取 Raindrop.io API Token

1. 登录 [Raindrop.io](https://app.raindrop.io)
2. 进入 **设置** → **集成** (Settings → Integrations)
3. 点击 **生成测试令牌** (Generate test token)
4. 复制生成的 Token

### 第二步：创建 GitHub 仓库

1. 在 GitHub 上创建一个**新仓库**（可以是公开或私有）
2. 将本项目的所有文件上传到仓库

### 第三步：配置 GitHub Secrets

1. 进入仓库的 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. Name: `RAINDROP_API_TOKEN`
4. Value: 粘贴你的 Raindrop API Token
5. 点击 **Add secret**

### 第四步：启用 GitHub Pages

1. 进入仓库的 **Settings** → **Pages**
2. Source 选择 **Deploy from a branch**
3. Branch 选择 **gh-pages**，文件夹选择 **/(root)**
4. 点击 **Save**

### 第五步：触发同步

方式一：手动触发
- 进入仓库的 **Actions** 标签页
- 选择 **Sync Raindrop Bookmarks** 工作流
- 点击 **Run workflow**

方式二：自动触发
- 工作流会每6小时自动运行一次
- 你也可以修改 `.github/workflows/sync-raindrop.yml` 中的 cron 表达式来调整频率

### 第六步：访问你的书签网站

几分钟后，你的书签网站将在以下地址可用：
```
https://你的用户名.github.io/仓库名/
```

## 📁 项目结构

```
raindrop-to-github/
├── scripts/
│   └── fetch_raindrop.py    # 主脚本：获取数据并生成网站
├── .github/
│   └── workflows/
│       └── sync-raindrop.yml  # GitHub Actions 工作流
├── docs/                     # 生成的网站文件（自动创建）
│   ├── index.html           # 主页
│   ├── style.css            # 样式
│   ├── data.json            # 完整 JSON 数据
│   ├── search.html          # 搜索页面
│   ├── collections/         # 各收藏夹页面
│   └── tags/                # 标签页面
└── README.md
```

## ⚙️ 配置选项

### 自定义同步频率

编辑 `.github/workflows/sync-raindrop.yml`：

```yaml
schedule:
  - cron: '0 */6 * * *'  # 每6小时
  # - cron: '0 0 * * *'  # 每天一次
  # - cron: '0 0 * * 0'  # 每周一次
```

### 使用自定义域名

1. 在仓库的 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **Variables** 标签
3. 创建新变量：
   - Name: `CUSTOM_DOMAIN`
   - Value: `你的域名.com`
4. 在你的域名 DNS 设置中添加 CNAME 记录指向 `你的用户名.github.io`

### 本地运行

```bash
# 安装依赖
pip install requests

# 设置环境变量
export RAINDROP_API_TOKEN="你的token"

# 运行脚本
python scripts/fetch_raindrop.py --output docs
```

## 🎨 自定义样式

你可以修改 `scripts/fetch_raindrop.py` 中的 `generate_css()` 函数来自定义网站样式。

主要可自定义的内容：
- 主题颜色（`--primary`）
- 卡片样式
- 字体
- 布局

## 📊 数据格式

生成的 `data.json` 包含完整的书签数据：

```json
{
  "collections": {
    "收藏夹ID": {
      "info": {
        "id": 12345,
        "title": "收藏夹名称",
        "color": "#4CAF50",
        "count": 50
      },
      "bookmarks": [
        {
          "id": 111,
          "title": "书签标题",
          "link": "https://example.com",
          "excerpt": "描述",
          "tags": ["tag1", "tag2"],
          "important": false,
          "cover": "https://...",
          "created": "2024-01-01T00:00:00.000Z"
        }
      ]
    }
  },
  "metadata": {
    "export_time": "2024-01-01T12:00:00",
    "total_collections": 10,
    "total_bookmarks": 500
  }
}
```

## 🔒 安全说明

- **API Token 安全**：你的 Raindrop API Token 存储在 GitHub Secrets 中，只有你可以访问
- **公开数据**：生成的网站是公开的，请确保你的书签中没有敏感信息
- **只读访问**：此工具只读取数据，不会修改或删除你的 Raindrop 收藏

## 🛠️ 故障排除

### 同步失败

1. 检查 GitHub Actions 日志，查看具体错误
2. 确认 `RAINDROP_API_TOKEN` secret 已正确设置
3. 确认 Token 没有过期

### 页面未更新

1. 确认 GitHub Pages 已启用并指向 `gh-pages` 分支
2. 检查 Actions 是否成功完成
3. 可能需要等待几分钟让 GitHub Pages 重新部署

### 样式问题

1. 清除浏览器缓存
2. 检查是否有自定义 CSS 冲突

## 📝 更新日志

### v1.0.0
- 初始版本
- 支持完整导出所有收藏夹和书签
- 生成响应式静态网站
- GitHub Actions 自动同步
- 标签聚合和搜索功能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

<p align="center">
  用 ❤️ 制作 | 数据来源: <a href="https://raindrop.io">Raindrop.io</a>
</p>
