from app.tools.base import BaseTool
from app.tools.search import SearchTool
from app.tools.zhihu import ZhihuHotTool

# 工具注册表
TOOLS = {
    "search": SearchTool(),
    "zhihu_hot": ZhihuHotTool(),
}

__all__ = ["TOOLS", "BaseTool", "SearchTool", "ZhihuHotTool"] 