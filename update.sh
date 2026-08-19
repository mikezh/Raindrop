#!/bin/bash
# Raindrop 书签一键更新脚本
# 用法: ./update.sh 新导出文件.html

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📚 Raindrop 书签更新工具${NC}"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}用法:${NC}"
    echo "  ./update.sh 新导出文件.html"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  ./update.sh ~/Downloads/raindrop_export.html"
    echo "  ./update.sh /path/to/export.html"
    exit 1
fi

SOURCE_FILE="$1"
EXPORT_DIR="export"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查源文件是否存在
if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}❌ 文件不存在: $SOURCE_FILE${NC}"
    exit 1
fi

# 获取文件信息
FILE_SIZE=$(wc -c < "$SOURCE_FILE" | tr -d ' ')
BOOKMARK_COUNT=$(grep -c '<DT><A HREF' "$SOURCE_FILE" 2>/dev/null || echo "0")

echo -e "${GREEN}📄 文件信息:${NC}"
echo "   路径: $SOURCE_FILE"
echo "   大小: $((FILE_SIZE / 1024)) KB"
echo "   书签: $BOOKMARK_COUNT 个"
echo ""

# 确认更新
read -p "确认更新? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消${NC}"
    exit 0
fi

# 进入脚本目录
cd "$SCRIPT_DIR"

# 删除旧的导出文件
echo -e "${YELLOW}🗑️  删除旧文件...${NC}"
rm -f "$EXPORT_DIR"/*.html 2>/dev/null || true

# 复制新文件
echo -e "${YELLOW}📋 复制新文件...${NC}"
cp "$SOURCE_FILE" "$EXPORT_DIR/"

# 重新生成网站
echo -e "${YELLOW}🔄 生成网站...${NC}"
python3 scripts/process_export.py --output docs

# Git 操作
echo -e "${YELLOW}📤 推送到 GitHub...${NC}"
git add -A
git commit -m "📥 更新书签: $BOOKMARK_COUNT 个"
git push

# 触发 GitHub Actions
echo -e "${YELLOW}🚀 触发部署...${NC}"
gh workflow run "Build Bookmarks Site" 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ 完成！${NC}"
echo ""
echo -e "${GREEN}🌐 访问地址:${NC}"
echo "   https://mikezh.github.io/Raindrop/"
echo ""
echo -e "${YELLOW}💡 提示: 等待 1-2 分钟让网站更新${NC}"
