"""
Scripts 共享工具模块 — 消除 40+ 脚本中的重复代码
用法: from _lib import ROOT, load_json, save_json, get_deepseek_client, ...
"""
import os
import json
import sys

# ============================================================
# 路径常量
# ============================================================
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
APP_DIR = os.path.join(ROOT, "app")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
PUBLIC_DIR = os.path.join(APP_DIR, "public")

# 核心数据文件
PHILOSOPHERS_FILE = os.path.join(DATA_DIR, "philosophers.json")
ALIASES_FILE = os.path.join(DATA_DIR, "name_aliases.json")
SUMMARIES_FILE = os.path.join(DATA_DIR, "book_summaries.json")
BOOKS_CACHE_FILE = os.path.join(DATA_DIR, "books_cache.json")

# 前端关键文件
SCHOOL_DETAIL_PAGE = os.path.join(APP_DIR, "src", "pages", "SchoolDetailPage.jsx")
GENEALOGY_PAGE = os.path.join(APP_DIR, "src", "pages", "GenealogyPage.jsx")
SCHOOLS_DIR = os.path.join(PUBLIC_DIR, "schools")
PHILOSOPHER_IMG_DIR = os.path.join(PUBLIC_DIR, "philosopher")


# ============================================================
# JSON 读写
# ============================================================
def load_json(path, default=None):
    """读取 JSON 文件，不存在则返回 default"""
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """写入 JSON 文件（自动创建目录）"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# API Key 加载 — 统一入口，优先环境变量
# ============================================================
def _load_api_keys_json():
    """加载 scripts/api_keys.json（仅本地开发回退，不提交到 Git）"""
    keys_path = os.path.join(SCRIPTS_DIR, "api_keys.json")
    if os.path.exists(keys_path):
        return load_json(keys_path)
    return {}


def get_deepseek_key():
    """获取 DeepSeek API Key（优先级: 环境变量 > api_keys.json 回退）"""
    env_key = os.getenv("DEEPSEEK_API_KEY", "")
    if env_key:
        return env_key
    # 回退：尝试从 api_keys.json（仅本地开发）
    keys = _load_api_keys_json()
    if keys.get("deepseek"):
        return keys["deepseek"]
    return ""


def get_agnes_key():
    """获取 Agnes AI API Key（优先级: 环境变量 > api_keys.json 回退）"""
    env_key = os.getenv("AGNES_API_KEY", "")
    if env_key:
        return env_key
    # 回退：尝试从 api_keys.json（仅本地开发）
    keys = _load_api_keys_json()
    return keys.get("agnes", "")


def get_github_token():
    """获取 GitHub Token"""
    return os.getenv("GITHUB_TOKEN", "")


# ============================================================
# DeepSeek API 客户端
# ============================================================
def create_deepseek_client(api_key=None):
    """创建 DeepSeek/OpenAI 兼容客户端"""
    from openai import OpenAI
    key = api_key or get_deepseek_key()
    if not key:
        raise ValueError(
            "未找到 DeepSeek API Key！请设置环境变量 DEEPSEEK_API_KEY，\n"
            "或在 scripts/api_keys.json 中添加 {\"deepseek\": \"sk-xxx\"}（仅本地开发）")
    return OpenAI(api_key=key, base_url="https://api.deepseek.com")


def create_agnes_client(api_key=None):
    """创建 Agnes AI API 客户端（返回 (api_key, text_api, img_api, text_model, img_model)）"""
    key = api_key or get_agnes_key()
    if not key:
        raise ValueError(
            "未找到 Agnes AI API Key！请设置环境变量 AGNES_API_KEY，\n"
            "或在 scripts/api_keys.json 中添加 {\"agnes\": \"sk-xxx\"}（仅本地开发）")
    TEXT_API = "https://apihub.agnes-ai.com/v1/chat/completions"
    IMG_API = "https://apihub.agnes-ai.com/v1/images/generations"
    TEXT_MODEL = "agnes-2.0-flash"
    IMG_MODEL = "agnes-image-2.1-flash"
    return key, TEXT_API, IMG_API, TEXT_MODEL, IMG_MODEL


def ask_deepseek(prompt, model="deepseek-chat", temperature=0.7, max_tokens=2048,
                 api_key=None, system_prompt=None):
    """调用 DeepSeek Chat 并返回文本回答"""
    client = create_deepseek_client(api_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=model, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


# ============================================================
# 数据操作
# ============================================================
def load_philosophers():
    """加载哲学家数据（返回 {name: info} 字典）"""
    return load_json(PHILOSOPHERS_FILE)


def save_philosophers(data):
    """保存哲学家数据"""
    save_json(PHILOSOPHERS_FILE, data)


def load_aliases():
    """加载人名别名映射"""
    return load_json(ALIASES_FILE)


def save_aliases(data):
    """保存人名别名映射"""
    save_json(ALIASES_FILE, data)


def load_summaries():
    """加载书籍标签摘要"""
    return load_json(SUMMARIES_FILE)


def save_summaries(data):
    """保存书籍标签摘要"""
    save_json(SUMMARIES_FILE, data)
