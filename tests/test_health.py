"""测试 /health 接口：确认服务能正常响应。"""

# TestClient 是 FastAPI 提供的"测试用浏览器"：不用真的启动服务器，就能在测试里发请求。
# 它底层用 httpx 库发请求，所以 requirements.txt 里装了 httpx。
from fastapi.testclient import TestClient

# 导入 app/main.py 里创建的应用对象 app。
from app.main import app

# 把应用交给测试客户端。之后 client.get(...) 就相当于用浏览器访问这个应用。
client = TestClient(app)


# 函数名以 test 开头，pytest 才会把它当成测试来运行。
# -> None 表示测试函数不返回值，只用 assert 检查结果。
def test_health_returns_ok() -> None:
    # 发请求：用 GET 方法访问 /health，拿到响应对象 response。
    response = client.get("/health")

    # assert 后面的条件必须成立，否则测试失败。200 是 HTTP 状态码，意思是"请求成功"。
    assert response.status_code == 200
    # response.json() 把响应里的 JSON 文本转回 Python 字典，再和期望的字典比较。
    assert response.json() == {"status": "ok"}
