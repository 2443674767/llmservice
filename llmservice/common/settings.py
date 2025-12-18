import json
import os
import secrets
from datetime import date

import dotenv

# import rag.utils
# import rag.utils.es_conn
# import rag.utils.infinity_conn
# import rag.utils.ob_conn
# import rag.utils.opensearch_conn
from common.config_utils import decrypt_database_config, get_base_config
from common.constants import RAG_FLOW_SERVICE_NAME, Storage
from common.file_utils import get_project_base_directory
from rag.nlp import search

# from rag.utils.azure_sas_conn import RAGFlowAzureSasBlob
# from rag.utils.azure_spn_conn import RAGFlowAzureSpnBlob
# from rag.utils.minio_conn import RAGFlowMinio
# from rag.utils.opendal_conn import OpenDALStorage
# from rag.utils.s3_conn import RAGFlowS3
# from rag.utils.oss_conn import RAGFlowOSS

LLM_FACTORY = None
LLM_BASE_URL = None
CHAT_MDL = ""
EMBEDDING_MDL = ""
RERANK_MDL = ""
ASR_MDL = ""
IMAGE2TEXT_MDL = ""

# 本地
OLLAMA_API_KEY = None
OLLAMA_URL = None
EMBEDDING_OLLAMA_MODEL = None
TOOLS_OLLAMA_MODEL = None
DEEPSEEK_OLLAMA_MODEL = None

# MCP
MCP_HOST = ""
MCP_PORT = 0

CHAT_CFG = ""
EMBEDDING_CFG = ""
RERANK_CFG = ""
ASR_CFG = ""
IMAGE2TEXT_CFG = ""
API_KEY = None
PARSERS = None
HOST_IP = None
HOST_PORT = None
SECRET_KEY = None
FACTORY_LLM_INFOS = None
ALLOWED_LLM_FACTORIES = None

DATABASE_TYPE = os.getenv("DB_TYPE", "mysql")
DATABASE = decrypt_database_config(name=DATABASE_TYPE)

CLIENT_AUTHENTICATION = None
HTTP_APP_KEY = None
GITHUB_OAUTH = None
FEISHU_OAUTH = None
OAUTH_CONFIG = None
DOC_ENGINE = os.getenv('DOC_ENGINE', 'elasticsearch')
DOC_ENGINE_INFINITY = (DOC_ENGINE.lower() == "infinity")

docStoreConn = None

retriever = None
kg_retriever = None

# 1代表用户需要注册
REGISTER_ENABLED = 1

SANDBOX_HOST = None

# 从rag.setting中获取
ES = {}
INFINITY = {}
OB = {}
OS = {}
AZURE = {}
S3 = {}
MINIO = {}
OSS = {}

DOC_MAXIMUM_SIZE: int = 128 * 1024 * 1024
DOC_BULK_SIZE: int = 4
EMBEDDING_BATCH_SIZE: int = 16

STORAGE_IMPL_TYPE = os.getenv('STORAGE_IMPL', 'MINIO')
STORAGE_IMPL = None


def _get_or_create_secret_key():
    secret_key = os.environ.get("RAGFLOW_SECRET_KEY")
    if secret_key and len(secret_key) >= 32:
        return secret_key

    # Check if there's a configured secret key
    configured_key = get_base_config(RAG_FLOW_SERVICE_NAME, {}).get("secret_key")
    if configured_key and configured_key != str(date.today()) and len(configured_key) >= 32:
        return configured_key

    # Generate a new secure key and warn about it
    import logging

    new_key = secrets.token_hex(32)
    logging.warning("SECURITY WARNING: Using auto-generated SECRET_KEY.")
    return new_key


# class StorageFactory:
#     storage_mapping = {
#         Storage.MINIO: RAGFlowMinio,
#         Storage.AZURE_SPN: RAGFlowAzureSpnBlob,
#         Storage.AZURE_SAS: RAGFlowAzureSasBlob,
#         Storage.AWS_S3: RAGFlowS3,
#         Storage.OSS: RAGFlowOSS,
#         Storage.OPENDAL: OpenDALStorage
#     }
#
#     @classmethod
#     def create(cls, storage: Storage):
#         return cls.storage_mapping[storage]()


def init_settings():
    """
    作用:
    初始化系统关键配置，包括数据库类型、LLM工厂、Doc引擎、存储配置、认证信息、SMTP邮件配置等全局变量。该函数读取环境变量、配置文件，或根据默认值设置参数，确保各模块能够按需调用全局配置信息，支撑服务启动与运行。
    """
    # 初始化数据库类型和数据库配置
    global DATABASE_TYPE, DATABASE
    dotenv.load_dotenv()
    DATABASE_TYPE = os.getenv("DB_TYPE", "mysql")   # 默认为mysql
    DATABASE = decrypt_database_config(name=DATABASE_TYPE)

    # 初始化LLM相关配置
    global ALLOWED_LLM_FACTORIES, LLM_FACTORY, LLM_BASE_URL
    llm_settings = get_base_config("user_default_llm", {}) or {}
    llm_default_models = llm_settings.get("default_models", {}) or {}
    LLM_FACTORY = llm_settings.get("factory", "") or ""
    LLM_BASE_URL = llm_settings.get("base_url", "") or ""
    ALLOWED_LLM_FACTORIES = llm_settings.get("allowed_factories", None)

    # 本地模型
    global EMBEDDING_OLLAMA_MODEL, TOOLS_OLLAMA_MODEL, DEEPSEEK_OLLAMA_MODEL
    EMBEDDING_OLLAMA_MODEL = os.getenv("EMBEDDING_OLLAMA_MODEL", "")
    TOOLS_OLLAMA_MODEL = os.getenv("TOOLS_OLLAMA_MODEL", "")
    DEEPSEEK_OLLAMA_MODEL = os.getenv("DEEPSEEK_OLLAMA_MODEL", "")
    MCP_HOST = os.getenv("MCP_HOST", "")
    MCP_PORT = os.getenv("MCP_PORT", "")

    # 注册功能是否开启
    global REGISTER_ENABLED
    try:
        REGISTER_ENABLED = int(os.environ.get("REGISTER_ENABLED", "1"))
    except Exception:
        pass

    # LLM工厂信息列表
    global FACTORY_LLM_INFOS
    try:
        with open(os.path.join(get_project_base_directory(), "conf", "llm_factories.json"), "r") as f:
            FACTORY_LLM_INFOS = json.load(f)["factory_llm_infos"]
    except Exception:
        FACTORY_LLM_INFOS = []

    # LLM服务API KEY
    global API_KEY
    API_KEY = llm_settings.get("api_key")

    # 解析器相关配置
    global PARSERS
    PARSERS = llm_settings.get(
        "parsers", "naive:General,qa:Q&A,resume:Resume,manual:Manual,table:Table,paper:Paper,book:Book,laws:Laws,presentation:Presentation,picture:Picture,one:One,audio:Audio,email:Email,tag:Tag"
    )

    # 主要模型名称初始化
    global CHAT_MDL, EMBEDDING_MDL, RERANK_MDL, ASR_MDL, IMAGE2TEXT_MDL
    chat_entry = _parse_model_entry(llm_default_models.get("chat_model", CHAT_MDL))
    embedding_entry = _parse_model_entry(llm_default_models.get("embedding_model", EMBEDDING_MDL))
    rerank_entry = _parse_model_entry(llm_default_models.get("rerank_model", RERANK_MDL))
    asr_entry = _parse_model_entry(llm_default_models.get("asr_model", ASR_MDL))
    image2text_entry = _parse_model_entry(llm_default_models.get("image2text_model", IMAGE2TEXT_MDL))

    # 主要模型详细配置初始化
    global CHAT_CFG, EMBEDDING_CFG, RERANK_CFG, ASR_CFG, IMAGE2TEXT_CFG
    CHAT_CFG = _resolve_per_model_config(chat_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    EMBEDDING_CFG = _resolve_per_model_config(embedding_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    RERANK_CFG = _resolve_per_model_config(rerank_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    ASR_CFG = _resolve_per_model_config(asr_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    IMAGE2TEXT_CFG = _resolve_per_model_config(image2text_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)

    # 赋值模型名称变量
    CHAT_MDL = CHAT_CFG.get("model", "") or ""
    EMBEDDING_MDL = os.getenv("TEI_MODEL", "BAAI/bge-small-en-v1.5") if "tei-" in os.getenv("COMPOSE_PROFILES", "") else ""
    RERANK_MDL = RERANK_CFG.get("model", "") or ""
    ASR_MDL = ASR_CFG.get("model", "") or ""
    IMAGE2TEXT_MDL = IMAGE2TEXT_CFG.get("model", "") or ""

    # 服务ip端口设置
    global HOST_IP, HOST_PORT
    HOST_IP = get_base_config(RAG_FLOW_SERVICE_NAME, {}).get("host", "127.0.0.1")
    HOST_PORT = get_base_config(RAG_FLOW_SERVICE_NAME, {}).get("http_port")

    # 密钥初始化
    global SECRET_KEY
    SECRET_KEY = _get_or_create_secret_key()

    # 身份认证相关配置
    authentication_conf = get_base_config("authentication", {})

    global CLIENT_AUTHENTICATION, HTTP_APP_KEY, GITHUB_OAUTH, FEISHU_OAUTH, OAUTH_CONFIG
    # 客户端认证配置
    CLIENT_AUTHENTICATION = authentication_conf.get("client", {}).get("switch", False)
    HTTP_APP_KEY = authentication_conf.get("client", {}).get("http_app_key")
    GITHUB_OAUTH = get_base_config("oauth", {}).get("github")
    FEISHU_OAUTH = get_base_config("oauth", {}).get("feishu")
    OAUTH_CONFIG = get_base_config("oauth", {})

    # 文档存储引擎类型配置
    global DOC_ENGINE, DOC_ENGINE_INFINITY, docStoreConn, ES, OB, OS, INFINITY
    DOC_ENGINE = os.environ.get("DOC_ENGINE", "elasticsearch")
    # DOC_ENGINE_INFINITY = (DOC_ENGINE.lower() == "infinity")
    # lower_case_doc_engine = DOC_ENGINE.lower()
    # if lower_case_doc_engine == "elasticsearch":
    #     ES = get_base_config("es", {})          # es配置
    #     docStoreConn = rag.utils.es_conn.ESConnection()
    # elif lower_case_doc_engine == "infinity":
    #     INFINITY = get_base_config("infinity", {"uri": "infinity:23817"})
    #     docStoreConn = rag.utils.infinity_conn.InfinityConnection()
    # elif lower_case_doc_engine == "opensearch":
    #     OS = get_base_config("os", {})
    #     docStoreConn = rag.utils.opensearch_conn.OSConnection()
    # elif lower_case_doc_engine == "oceanbase":
    #     OB = get_base_config("oceanbase", {})
    #     docStoreConn = rag.utils.ob_conn.OBConnection()
    # else:
    #     raise Exception(f"Not supported doc engine: {DOC_ENGINE}")

    # 对象存储相关初始化
    global AZURE, S3, MINIO, OSS
    if STORAGE_IMPL_TYPE in ['AZURE_SPN', 'AZURE_SAS']:
        AZURE = get_base_config("azure", {})
    elif STORAGE_IMPL_TYPE == 'AWS_S3':
        S3 = get_base_config("s3", {})
    elif STORAGE_IMPL_TYPE == 'MINIO':
        MINIO = decrypt_database_config(name="minio")
    elif STORAGE_IMPL_TYPE == 'OSS':
        OSS = get_base_config("oss", {})

    # 存储实现工厂实例
    # global STORAGE_IMPL
    # STORAGE_IMPL = StorageFactory.create(Storage[STORAGE_IMPL_TYPE])

    # 检索器与知识图谱检索器配置
    global retriever, kg_retriever
    retriever = search.Dealer(docStoreConn)

    # from graphrag import search as kg_search  # 导入知识图谱搜索模块
    # kg_retriever = kg_search.KGSearch(docStoreConn)

    # 沙盒主机配置
    # global SANDBOX_HOST
    # if int(os.environ.get("SANDBOX_ENABLED", "0")):
    #     SANDBOX_HOST = os.environ.get("SANDBOX_HOST", "sandbox-executor-manager")

    # 邮件配置相关
    # global SMTP_CONF
    # SMTP_CONF = get_base_config("smtp", {})  # 邮件服务相关配置
    #
    # global MAIL_SERVER, MAIL_PORT, MAIL_USE_SSL, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, MAIL_FRONTEND_URL
    # MAIL_SERVER = SMTP_CONF.get("mail_server", "")  # SMTP服务地址
    # MAIL_PORT = SMTP_CONF.get("mail_port", 000)  # SMTP端口
    # MAIL_USE_SSL = SMTP_CONF.get("mail_use_ssl", True)  # 是否启用SSL
    # MAIL_USE_TLS = SMTP_CONF.get("mail_use_tls", False)  # 是否启用TLS
    # MAIL_USERNAME = SMTP_CONF.get("mail_username", "")  # 邮箱用户名
    # MAIL_PASSWORD = SMTP_CONF.get("mail_password", "")  # 邮箱密码
    # mail_default_sender = SMTP_CONF.get("mail_default_sender", [])  # 默认发件人(名称, 邮箱)
    # if mail_default_sender and len(mail_default_sender) >= 2:
    #     MAIL_DEFAULT_SENDER = (mail_default_sender[0], mail_default_sender[1])  # 设置默认发件人
    # MAIL_FRONTEND_URL = SMTP_CONF.get("mail_frontend_url", "")  # 前端链接用于邮件模板

    # 文档与向量化批量处理相关设置
    global DOC_MAXIMUM_SIZE, DOC_BULK_SIZE, EMBEDDING_BATCH_SIZE
    DOC_MAXIMUM_SIZE = int(os.environ.get("MAX_CONTENT_LENGTH", 128 * 1024 * 1024))  # 单文档最大体积
    DOC_BULK_SIZE = int(os.environ.get("DOC_BULK_SIZE", 4))  # 文档批量上传数量
    EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", 16))  # 向量化批次大小


def _parse_model_entry(entry):
    if isinstance(entry, str):
        return {"name": entry, "factory": None, "api_key": None, "base_url": None}
    if isinstance(entry, dict):
        name = entry.get("name") or entry.get("model") or ""
        return {
            "name": name,
            "factory": entry.get("factory"),
            "api_key": entry.get("api_key"),
            "base_url": entry.get("base_url"),
        }
    return {"name": "", "factory": None, "api_key": None, "base_url": None}


def _resolve_per_model_config(entry_dict, backup_factory, backup_api_key, backup_base_url):
    name = (entry_dict.get("name") or "").strip()
    m_factory = entry_dict.get("factory") or backup_factory or ""
    m_api_key = entry_dict.get("api_key") or backup_api_key or ""
    m_base_url = entry_dict.get("base_url") or backup_base_url or ""

    if name and "@" not in name and m_factory:
        name = f"{name}@{m_factory}"

    return {
        "model": name,
        "factory": m_factory,
        "api_key": m_api_key,
        "base_url": m_base_url,
    }


