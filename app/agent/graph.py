import json
import os
from typing import Dict, List, Any, Annotated, TypedDict, Optional

import langgraph.graph as lg
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, AIMessage

from app.tools import TOOLS


class AgentState(TypedDict):
    """代理的状态类型"""
    question: str
    chat_history: list[dict]
    messages: list[dict]
    tool_calls: list[dict]
    tool_results: Optional[list[dict]]


# 系统提示模板，告诉模型可用的工具
SYSTEM_PROMPT = """你是一个有用的AI助手，具有访问多种工具的能力。
请仔细回答用户的问题。如果你不知道答案，你可以使用工具来获取更多信息。

可用工具:
{tools}

使用以下格式：

用户问题：用户的问题
思考：你对如何回答的思考过程
工具调用 (如果需要)：
{{
    "name": "工具名称",
    "input": {{
        "参数名": "参数值"
    }}
}}
行动后思考：在使用工具后你的思考
回答：对用户问题的最终回答

开始!
"""


def _format_tools_for_prompt() -> str:
    """格式化工具信息到提示中"""
    tools_desc = []
    for name, tool in TOOLS.items():
        params = []
        schema = tool.input_schema.model_json_schema()
        properties = schema.get("properties", {})
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")
            default = param_info.get("default", None)
            default_str = f"，默认值：{default}" if default is not None else ""
            
            params.append(f"- {param_name} ({param_type}): {param_desc}{default_str}")
        
        tools_desc.append(
            f"{name}: {tool.description}\n"
            f"参数:\n" + "\n".join(params)
        )
    
    return "\n\n".join(tools_desc)


def _parse_tool_calls(output: str) -> List[Dict[str, Any]]:
    """从模型输出中解析工具调用"""
    tool_calls = []
    try:
        # 查找工具调用部分（在 "工具调用" 和 "行动后思考" 之间）
        if "工具调用" in output:
            parts = output.split("工具调用")
            if len(parts) > 1:
                tool_part = parts[1].split("行动后思考")[0]
                
                # 提取JSON对象（可能有多个）
                import re
                json_patterns = re.findall(r'({[^{}]*})', tool_part)
                for pattern in json_patterns:
                    try:
                        tool_call = json.loads(pattern)
                        if "name" in tool_call and "input" in tool_call:
                            tool_calls.append(tool_call)
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    
    return tool_calls


async def _process_tool_calls(state: AgentState) -> AgentState:
    """处理工具调用，执行工具"""
    tool_calls = state.get("tool_calls", [])
    tool_results = []
    
    for call in tool_calls:
        tool_name = call.get("name")
        tool_input = call.get("input", {})
        
        tool = TOOLS.get(tool_name)
        if tool:
            try:
                result = await tool.run(tool_input)
                tool_results.append({
                    "tool_name": tool_name,
                    "result": result.model_dump()
                })
            except Exception as e:
                # 如果工具执行出错，记录错误信息
                tool_results.append({
                    "tool_name": tool_name,
                    "error": str(e)
                })
    
    return {"tool_results": tool_results, **state}


def _should_use_tools(state: AgentState) -> str:
    """决定是否需要使用工具"""
    tool_calls = state.get("tool_calls", [])
    if tool_calls:
        return "use_tools"
    return "finish"


def _generate_response(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """生成用户问题的最终回答"""
    question = state["question"]
    chat_history = state.get("chat_history", [])
    tool_results = state.get("tool_results", [])
    
    # 构建提示
    tools_desc = _format_tools_for_prompt()
    system_prompt = SYSTEM_PROMPT.format(tools=tools_desc)
    
    # 构建历史消息
    messages = []
    for msg in chat_history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    
    # 添加当前问题和工具结果
    current_prompt = f"用户问题: {question}\n"
    
    if tool_results:
        current_prompt += "工具执行结果:\n"
        for result in tool_results:
            tool_name = result.get("tool_name")
            if "error" in result:
                current_prompt += f"{tool_name} 执行失败: {result['error']}\n"
            else:
                result_data = result.get("result", {})
                current_prompt += f"{tool_name} 执行结果: {json.dumps(result_data, ensure_ascii=False)}\n"
    
    messages.append(HumanMessage(content=current_prompt))
    
    # 调用LLM生成回答
    response = llm.invoke(messages)
    
    # 解析输出，查找工具调用
    output = response.content
    tool_calls = _parse_tool_calls(output)
    
    # 更新状态
    new_state = {
        **state,
        "messages": messages,
        "tool_calls": tool_calls
    }
    
    return new_state


def create_agent_executor(model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
    """
    创建LangGraph代理执行器
    
    Args:
        model_name: 使用的LLM模型名称
        temperature: 模型温度参数
        
    Returns:
        LangGraph执行器
    """
    # 初始化LLM
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature
    )
    
    # 创建 LangGraph
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("generate_response", lambda state: _generate_response(state, llm))
    workflow.add_node("process_tool_calls", _process_tool_calls)
    
    # 添加边和条件
    workflow.add_edge(START, "generate_response")
    workflow.add_conditional_edges(
        "generate_response",
        _should_use_tools,
        {
            "use_tools": "process_tool_calls",
            "finish": END
        }
    )
    workflow.add_edge("process_tool_calls", "generate_response")
    
    # 编译图
    app = workflow.compile()
    
    return app 