import unittest

from mcp_project.mcp_service import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_query_api(self):
        # 假设查询的字段为转速大于1300，扭矩大于1500
        payload = {"question": "存储外特性数据的表的数据是什么，请注意，sqllite的表需要使用[]包起来进行查询,只需要显示转速字段中值大于1300和扭矩字段中大于1500的记录"}
        response = self.app.post('/query', json=payload)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn("response", json_data)
        self.assertIn("转速", json_data['response'])
        self.assertIn("扭矩", json_data['response'])


if __name__ == "__main__":
    unittest.main()
