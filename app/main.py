import json
import os
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import API_TITLE, API_VERSION, API_DESCRIPTION, LLM_MODEL, LLM_TEMPERATURE, HOST, PORT, DEBUG
from app.agent import create_agent_executor
from app.tools import TOOLS

# 创建 FastAPI 应用
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取 Agent 执行器
agent_executor = create_agent_executor(
    model_name=LLM_MODEL, 
    temperature=LLM_TEMPERATURE
)

# 请求模型
class QuestionRequest(BaseModel):
    question: str = Field(..., description="用户提问的问题")
    chat_history: Optional[List[Dict[str, str]]] = Field(default=[], description="聊天历史记录，格式为[{\"role\": \"user\"|\"assistant\", \"content\": \"消息内容\"}]")

# 工具信息模型
class ToolInfo(BaseModel):
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: List[Dict[str, Any]] = Field(..., description="工具参数列表")

# 响应模型
class AgentResponse(BaseModel):
    answer: str = Field(..., description="模型的回答")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="模型调用的工具")
    tool_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="工具执行结果")

@app.get("/")
async def root():
    """API 根路径，返回欢迎信息"""
    return {"message": f"欢迎使用 {API_TITLE} v{API_VERSION}"}

@app.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """列出所有可用的工具"""
    tool_list = []
    for name, tool in TOOLS.items():
        tool_list.append(tool.to_dict())
    return tool_list

@app.post("/chat", response_model=AgentResponse)
async def chat(request: QuestionRequest):
    """
    聊天接口，处理用户问题并返回回答
    
    Args:
        request: 包含用户问题和聊天历史的请求
    
    Returns:
        代理回答和工具调用信息
    """
    try:
        # 运行 LangGraph
        initial_state = {
            "question": request.question,
            "chat_history": request.chat_history,
            "messages": [],
            "tool_calls": []
        }
        
        # 异步执行代理
        result = await agent_executor.ainvoke(initial_state)
        
        # 从最后一个输出中提取回答
        output = None
        tool_calls = result.get("tool_calls", [])
        tool_results = result.get("tool_results", [])
        
        # 将最后一个LLM输出解析为回答
        messages = result.get("messages", [])
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                output = last_message.content
                
                # 尝试提取最终回答
                if "回答：" in output:
                    answer_parts = output.split("回答：")
                    if len(answer_parts) > 1:
                        output = answer_parts[-1].strip()
        
        return AgentResponse(
            answer=output or "抱歉，我无法处理您的请求。",
            tool_calls=tool_calls,
            tool_results=tool_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

# 启动应用
if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG) 