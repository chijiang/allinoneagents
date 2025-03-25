import httpx
from typing import List, Dict, Any, Optional
from pydantic import Field, BaseModel
from bs4 import BeautifulSoup
import json

from app.tools.base import BaseTool, BaseToolInput, BaseToolOutput

class ZhihuHotInput(BaseToolInput):
    limit: int = Field(10, description="返回热榜条目数量，默认为10")

class ZhihuHotItem(BaseModel):
    title: str = Field(..., description="热榜标题")
    url: str = Field(..., description="热榜链接")
    hot_value: Optional[str] = Field(None, description="热度值")

class ZhihuHotOutput(BaseToolOutput):
    items: List[ZhihuHotItem] = Field(..., description="知乎热榜列表")
    
class ZhihuHotTool(BaseTool[ZhihuHotInput, ZhihuHotOutput]):
    """知乎热榜工具"""
    name = "zhihu_hot"
    description = "获取知乎当前热榜信息"
    input_schema = ZhihuHotInput
    output_schema = ZhihuHotOutput
    
    async def _run(self, input_data: ZhihuHotInput) -> ZhihuHotOutput:
        """
        获取知乎热榜数据
        
        Args:
            input_data: 包含返回条目数的输入对象
            
        Returns:
            知乎热榜列表
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        items = []
        
        try:
            # 方法1：使用知乎API获取热榜
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
                    headers=headers,
                    params={"limit": 50},  # 获取更多条目，后面会截取
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hot_items = data.get("data", [])
                    
                    for i, item in enumerate(hot_items):
                        if i >= input_data.limit:
                            break
                        
                        target = item.get("target", {})
                        title = target.get("title", "")
                        url = f"https://www.zhihu.com/question/{target.get('id')}"
                        metrics = item.get("detail_text", "")
                        
                        items.append(ZhihuHotItem(
                            title=title,
                            url=url,
                            hot_value=metrics
                        ))
                else:
                    # 如果API请求失败，尝试备用方法
                    items = await self._fallback_method(input_data.limit)
        except Exception as e:
            # 如果出现异常，尝试备用方法
            items = await self._fallback_method(input_data.limit)
            
        return ZhihuHotOutput(items=items)
    
    async def _fallback_method(self, limit: int) -> List[ZhihuHotItem]:
        """备用方法：使用第三方API或镜像站获取知乎热榜"""
        items = []
        
        # 尝试使用今日热榜API
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # 使用今日热榜开放API：https://www.tophub.fun
                response = await client.get(
                    "https://api.tophub.fun/v2/GetAllInfoGzip?id=1&page=0",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hot_items = data.get("Data", {}).get("data", [])
                    
                    for i, item in enumerate(hot_items):
                        if i >= limit:
                            break
                        
                        title = item.get("Title", "")
                        url = item.get("Url", "")
                        hot_value = item.get("hotValue", "")
                        
                        items.append(ZhihuHotItem(
                            title=title,
                            url=url,
                            hot_value=hot_value
                        ))
                    
                    return items
        except Exception:
            pass
        
        # 如果仍然失败，使用更多备用方法
        try:
            async with httpx.AsyncClient() as client:
                # 使用另一个第三方API
                response = await client.get(
                    "https://tenapi.cn/zhihuresou/",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hot_items = data.get("list", [])
                    
                    for i, item in enumerate(hot_items):
                        if i >= limit:
                            break
                        
                        title = item.get("name", "")
                        url = item.get("url", "")
                        
                        items.append(ZhihuHotItem(
                            title=title,
                            url=url,
                            hot_value=None
                        ))
        except Exception:
            # 如果所有方法都失败，返回一个带有错误信息的条目
            items.append(ZhihuHotItem(
                title="无法获取知乎热榜，可能是API限制或网络问题",
                url="https://www.zhihu.com/hot",
                hot_value=None
            ))
        
        return items 