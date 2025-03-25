import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# API 配置
API_TITLE = "多功能问答Agent API"
API_VERSION = "0.1.0"
API_DESCRIPTION = "基于FastAPI和LangGraph构建的多功能问答Agent系统，具有工具调用功能"

# LLM 配置
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t") 