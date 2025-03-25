import uvicorn
from app.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    print(f"启动服务器 - 监听：{HOST}:{PORT}, 调试模式：{'开启' if DEBUG else '关闭'}")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG) 