from fastapi.testclient import TestClient

def test_get_status(client: TestClient) -> None:
    """测试 /api/status 获取应用状态接口"""
    # 1. 客户端请求获取数据
    response = client.get("/api/status")
    data = response.json()

    # 2. 断言状态码和业务状态码
    assert response.status_code == 200
    assert data.get("code") == 200