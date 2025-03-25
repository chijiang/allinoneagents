import httpx
from typing import List, Dict, Any, Optional
from pydantic import Field, BaseModel
from bs4 import BeautifulSoup

from app.tools.base import BaseTool, BaseToolInput, BaseToolOutput

class SearchInput(BaseToolInput):
    query: str = Field(..., description="搜索查询关键词")
    num_results: int = Field(5, description="返回结果数量，默认为5")

class SearchResultItem(BaseModel):
    title: str = Field(..., description="搜索结果标题")
    link: str = Field(..., description="搜索结果链接")
    snippet: str = Field(..., description="搜索结果摘要")

class SearchOutput(BaseToolOutput):
    results: List[SearchResultItem] = Field(..., description="搜索结果列表")

class SearchTool(BaseTool[SearchInput, SearchOutput]):
    """搜索引擎工具"""
    name = "search"
    description = "使用搜索引擎查找问题的答案"
    input_schema = SearchInput
    output_schema = SearchOutput
    
    async def _run(self, input_data: SearchInput) -> SearchOutput:
        """
        执行搜索查询
        
        Args:
            input_data: 包含查询关键词和结果数量的输入
            
        Returns:
            搜索结果列表
        """
        # 使用httpx发送搜索请求（这里使用Bing作为示例）
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        async with httpx.AsyncClient() as client:
            # 使用Bing搜索
            response = await client.get(
                f"https://www.bing.com/search",
                params={"q": input_data.query},
                headers=headers
            )
            
            # 解析结果
            results = []
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.select('.b_algo')
                
                for i, result in enumerate(search_results):
                    if i >= input_data.num_results:
                        break
                        
                    title_elem = result.select_one('h2 > a')
                    snippet_elem = result.select_one('.b_caption p')
                    
                    if title_elem and snippet_elem:
                        title = title_elem.text
                        link = title_elem.get('href', '')
                        snippet = snippet_elem.text
                        
                        results.append(SearchResultItem(
                            title=title,
                            link=link,
                            snippet=snippet
                        ))
            
            return SearchOutput(results=results) 