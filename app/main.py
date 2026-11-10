"""程序入口：创建 FastAPI 应用，并登记接口。

启动服务的命令是 uvicorn app.main:app，
意思是"运行 app/main.py 这个模块里名叫 app 的对象"。
"""

# 从第三方库 fastapi 导入 FastAPI 类。它负责把网址对应到函数、自动处理 JSON，
# 还会生成接口文档（服务启动后访问 /docs 就能看到）。
from fastapi import FastAPI

# 调用 FastAPI 类，创建应用对象，存进变量 app。title 是接口文档页面上显示的标题。
app = FastAPI(title="recruitment Delivery Agent")
# @app.get("/health") 是装饰器：把紧挨着的下一个函数登记成"GET /health"接口。
# 有人用 GET 方法访问 /health，FastAPI 就调用 health()，再把返回值转成 JSON 发回去。
# -> dict[str, str]：返回"键和值都是字符串"的字典；FastAPI 还会按这个类型检查返回值。
@app.get("/health")
def health() -> dict[str, str]:
    # 健康检查：能返回结果，就说明服务还活着。部署后，监控程序会定时访问它。
    return {"status": "ok"}
