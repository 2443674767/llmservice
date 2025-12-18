"""Weather Agent 实现（示例）"""
import json
from typing import List, Any, Dict

from langchain.agents import create_agent
from langchain_classic.agents import AgentExecutor
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from loguru import logger

from graphmcp.agents.weather_agent.config import WeatherAgentConfig
from graphmcp.core.agent_base import AgentBase
# from graphmcp.core.compat import create_agent


@tool
def get_weather_tool(city: str) -> str:
    """
    查询指定城市的即时天气信息。

    :param city: 必要参数，字符串类型，表示要查询天气的城市名称。
                 注意：中国城市需使用其英文名称，如 "Beijing" 表示北京。
    :return: 返回 OpenWeather API 的响应结果，URL 为
             https://api.openweathermap.org/data/2.5/weather。
             响应内容为 JSON 格式的字符串，包含详细的天气数据。
    """
    # 模拟天气数据
    if city.lower() == "beijing":
        response = {
            "coord": {"lon": 116.4074, "lat": 39.9042},
            "weather": [{"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d"}],
            "base": "stations",
            "main": {"temp": 12.5, "feels_like": 11.9, "temp_min": 12.5, "temp_max": 12.5, "pressure": 1012,
                     "humidity": 52},
            "visibility": 6000,
            "wind": {"speed": 3.6, "deg": 80},
            "clouds": {"all": 23},
            "dt": 1671673146,
            "sys": {"type": 1, "id": 9246, "country": "CN", "sunrise": 1671650426, "sunset": 1671693807},
            "timezone": 28800,
            "id": 1816670,
            "name": "Beijing",
            "cod": 200
        }
    elif city.lower() == "shanghai":
        response = {
            "coord": {"lon": 121.4737, "lat": 31.2304},
            "weather": [{"id": 802, "main": "Clouds", "description": "scattered clouds", "icon": "03d"}],
            "base": "stations",
            "main": {"temp": 18.2, "feels_like": 17.8, "temp_min": 18.2, "temp_max": 18.2, "pressure": 1010,
                     "humidity": 72},
            "visibility": 5000,
            "wind": {"speed": 4.1, "deg": 150},
            "clouds": {"all": 38},
            "dt": 1671673146,
            "sys": {"type": 1, "id": 9261, "country": "CN", "sunrise": 1671650044, "sunset": 1671692578},
            "timezone": 28800,
            "id": 1796236,
            "name": "Shanghai",
            "cod": 200
        }
    else:
        response = {
            "error": "city_not_found",
            "message": "城市未找到，请输入有效城市名称"
        }

    logger.info(f"查询天气结果：{response}")
    return json.dumps(response, ensure_ascii=False)


class WeatherAgent(AgentBase):
    """天气查询 Agent"""

    def __init__(self, llm: BaseChatModel):
        """
        初始化 Weather Agent

        :param llm: 语言模型实例
        """
        super().__init__(
            llm=llm,
            name="weather_agent",
            description="天气查询助手，可以查询指定城市的即时天气信息"
        )
        self.config = WeatherAgentConfig()

    def get_tools(self) -> List[Any]:
        """
        获取天气工具列表

        :return: 工具列表
        """
        return [get_weather_tool]

    def create_agent(self) -> AgentExecutor:
        """
        创建 Weather Agent 执行器

        :return: AgentExecutor 实例
        """
        tools = self.get_tools()
        system_prompt = "你是一个天气查询助手，可以帮助用户查询城市的天气信息。"

        agent = create_agent(
            self.llm,
            tools,
            system_prompt=system_prompt,
        )

        logger.info("Weather Agent 创建成功")
        return agent

