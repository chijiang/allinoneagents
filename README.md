# 多功能问答Agent系统

基于FastAPI和LangGraph构建的多功能问答Agent系统，具有工具调用功能。

## 功能

- 统一的工具管理框架
- 搜索引擎工具：搜索问题答案
- 知乎热榜工具：查询当日知乎热榜

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 设置环境变量
export OPENAI_API_KEY=your_api_key  # 在Windows中使用 set OPENAI_API_KEY=your_api_key

# 启动服务
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看API文档。

## 项目结构

```
.
├── app/                    # 应用代码
│   ├── main.py             # FastAPI主应用
│   │   └── agent/              # Agent相关代码
│   │   │   └── graph.py        # LangGraph定义
│   │   ├── tools/              # 工具集合
│   │   │   └── zhihu.py        # 知乎热榜工具
│   │   └── config.py           # 配置
│   ├── .env                    # 环境变量(需要自行创建)
│   ├── requirements.txt        # 依赖
│   └── README.md               # 项目说明
``` 