mcp-agent-platform/
├── README.md
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── mcp_services.yaml
│   └── agents_config.yaml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── agent_manager.py
│   │   ├── tool_registry.py
│   │   └── graph_builder.py
│   ├── mcp_services/
│   │   ├── __init__.py
│   │   ├── base_service.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── sqlite_service.py
│   │   │   ├── mysql_service.py
│   │   │   └── postgres_service.py
│   │   ├── weather_service.py
│   │   └── service_factory.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── database_agent.py
│   │   ├── weather_agent.py
│   │   └── agent_factory.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── config_loader.py
│   │   └── validation.py
│   └── api/
│       ├── __init__.py
│       ├── routes.py
│       └── schemas.py
├── tests/
│   ├── __init__.py
│   ├── test_mcp_services.py
│   ├── test_agents.py
│   └── test_integration.py
└── scripts/
    ├── start_platform.sh
    ├── add_mcp_service.py
    └── health_check.py