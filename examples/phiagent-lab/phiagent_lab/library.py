"""原创教学材料：不是哲学家原文，不得当作学术引文。"""
import re
from pydantic import BaseModel, ConfigDict, Field

PASSAGES = {
    "demo-resentment": {
        "id": "demo-resentment", "title": "怨恨与价值判断", "source": "课程作者编写的教学材料",
        "text": "这是一段教学概述，不是尼采原文。怨恨问题可以从反应性评价入手：一个人可能先否定他者，再由这种否定确立自己的价值。理解这一问题需要区分情绪、评价方式和具体历史语境。",
    },
    "demo-freedom": {
        "id": "demo-freedom", "title": "自由与责任", "source": "课程作者编写的教学材料",
        "text": "这是一段教学概述，不是任何哲学家的原文。讨论自由时，可以分别考察选择能力、外部约束和责任归属。回答具体问题之前，应先说明使用的是哪一种自由概念。",
    },
    "demo-knowledge": {
        "id": "demo-knowledge", "title": "知识与证据", "source": "课程作者编写的教学材料",
        "text": "这是一段教学概述。一个论断听起来可信，不等于它已经获得证据支持。引用应指向能够核查的材料；材料存在，也不意味着它支持回答中的所有结论。",
    },
}

class SearchArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=3, ge=1, le=5)

class ReadArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    passage_id: str = Field(min_length=1, max_length=80)

def search_library(query: str, limit: int = 3):
    # Bigram matching is deliberately simple; this is NOT semantic retrieval.
    terms = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", query.lower())
    tokens = set()
    for term in terms:
        tokens.add(term)
        if re.search(r"[\u4e00-\u9fff]", term):
            tokens.update(term[i:i + 2] for i in range(len(term) - 1))
    ranked = []
    for item in PASSAGES.values():
        haystack = item["title"] + item["text"]
        score = sum(len(t) for t in tokens if t in haystack.lower())
        if score:
            ranked.append((score, item))
    ranked.sort(key=lambda row: (-row[0], row[1]["id"]))
    return [{"id": p["id"], "title": p["title"], "snippet": p["text"][:70]}
            for _, p in ranked[:limit]]

def read_passage(passage_id: str):
    if passage_id not in PASSAGES:
        raise ValueError("材料不存在")
    return dict(PASSAGES[passage_id])

REGISTRY = {
    "search_library": (SearchArgs, search_library, "按关键词搜索教学材料，返回候选 id。"),
    "read_passage": (ReadArgs, read_passage, "按候选 id 读取材料全文及出处。"),
}

def tool_specs():
    return [{"type": "function", "function": {
        "name": name, "description": description,
        "parameters": schema.model_json_schema(),
    }} for name, (schema, _, description) in REGISTRY.items()]

def execute_tool(name: str, arguments: dict):
    if name not in REGISTRY:
        raise ValueError("未知工具")
    schema, function, _ = REGISTRY[name]
    parsed = schema.model_validate(arguments)
    return function(**parsed.model_dump())
