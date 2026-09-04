# -*- coding: utf-8 -*-
"""记忆/创作工具域——agent 拆分模块 4/6（R2-2/S21, 2026-08-18 复审）

工具: write_essay / generate_image / philosopher_debate / thought_experiment / role_play（5 个）。
均为有状态（per-user 记忆槽持久化）或人格/创作类工具; 代码从 routes/agent.py 原样搬移
（不改逻辑）; 注册到 agent_core.TOOLS（import 本模块即注册）。
"""
import json, os, re, time, hashlib, urllib.request, threading
from pathlib import Path

from routes.agent_core import (
    TOOLS, register_tool, _int_arg,
    _mem_slot, _save_agent_memory, _find_essay_topic, get_philosophers,
    PUBLIC, PHILOSOPHER_DIR, AGNES_IMG_DIR, AI_DIR,
)
from routes.agent_llm import llm_chat

# ESSAY_PROMPT（2026-08-18 修复：原定义缺失，write_essay 新作文路径会 NameError；
# 占位符与 _essay_pipeline 的 format 调用一致）
ESSAY_PROMPT = (
    "请以「{genre}」体裁写一篇关于「{topic}」的作文（约 {word_count} 字）。\n"
    "参考素材（retrieval）：{retrieval}\n"
    "补充要求：{extra}\n"
    "要求：结构清晰、论据充分、有独到见解，直接输出正文。"
)

# ── 工具 7: write_essay（学生作文——注册为工具, 对话流意图触发; 支持多轮修改）──
# 多轮修改记忆: 持久化到文件（进程重启不丢）; 作文按题目记忆（避免跨主题串味）
# 2026-08-14 per-user 加固（P0）: 记忆按用户隔离（guard.user_memory_key）,
#   原子写（tmp+rename）防并发损坏; 旧单用户格式自动迁移到 default 槽
def _exec_write_essay(args):
    topic = args.get("topic") or args.get("query") or ""
    if not topic:
        return {"error": "缺少作文题目"}
    try:
        word_count = _int_arg(args, "word_count", 800, 100, 3000)
    except Exception:
        word_count = 800
    modify = (args.get("modify") or "").strip()
    # 自动检测修改意图（LLM 未显式传 modify 时）: 修改词 + 存在对应题目记忆 → 对上次作文修改
    if not modify:
        intent_text = f"{topic} {args.get('extra', '')} {args.get('genre', '')}"
        if any(w in intent_text for w in ("修改", "改一下", "重写", "调整", "改成", "换一个",
                                          "增加", "减少", "删掉", "美化", "润色", "改写", "扩展", "精简")):
            hit = _find_essay_topic(topic)
            if hit:
                modify = topic
                topic = hit
    reply, citations, tcl = _essay_pipeline(topic, args.get("genre", "议论文"),
                                            word_count, args.get("extra", ""), modify)
    _save_agent_memory()   # 持久化多轮修改记忆
    return {"essay": reply, "citations": citations, "steps": tcl}

register_tool(
    "write_essay",
    "根据题目写一篇哲学作文（议论文/读后感等）。自动检索原典原文支撑论据, 带引用标注。用户说'修改/重写/改一下作文'时传 modify='修改要求', 工具自动基于上次作文修改。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "作文题目（修改请求时可为修改要求）"},
        "genre": {"type": "string", "description": "文体: 议论文/读后感/论述"},
        "word_count": {"type": "integer", "description": "目标字数"},
        "extra": {"type": "string", "description": "附加要求"},
        "modify": {"type": "string", "description": "修改要求（修改上次作文时传, 如: 改成800字/换个开头/论点再强化）"}},
     "required": ["topic"]},
    _exec_write_essay,
)

def _essay_pipeline(topic, genre="议论文", word_count=800, extra="", modify=""):
    """作文生成/修改——返回 (reply, citations, tool_calls_log)
    多轮修改: modify 非空且存在对应题目记忆 → 基于上次文本改写（沿用原论点与原典引用, 不重新检索）"""
    tool_calls_log = []
    slot = _mem_slot()
    prev = slot["essays"].get(topic)
    if modify and prev:
        prompt = (f"用户要求修改作文。修改要求: {modify}\n\n"
                  f"上次作文题目: {topic}\n"
                  f"上次作文（{prev.get('genre', '')}, 目标{prev.get('word_count', '')}字）:\n"
                  f"---\n{prev['text']}\n---\n\n"
                  f"请按要求修改: 保持原作文的论点与原典引用, 只做要求的调整; 输出修改后的完整作文（目标{word_count}字）。")
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.75,
                        max_tokens=min(word_count * 2 + 500, 4000))
        reply = (resp["choices"][0]["message"].get("content") or "").strip() or "（修改失败，请重试）"
        slot["essays"][topic] = {"text": reply, "genre": genre, "word_count": word_count}
        return reply, [], tool_calls_log
    query = re.sub(r"[？?！!。，,、\s]+", " ", topic)[:50]
    result = TOOLS["search_books"]["execute"]({"query": query, "limit": 6})
    tool_calls_log.append({"name": "search_books", "args": {"query": query},
                           "result_summary": str(result)[:200], "result_full": result,
                           "thought": f"作文需原典支撑, 检索「{query}」"})
    retrieval = json.dumps(result, ensure_ascii=False)[:6000]
    # 联网补充论据（避免拘泥于知识库: 当代观点/时事背景/其他学者论述）
    web_text = ""
    try:
        web = TOOLS["websearch"]["execute"]({"query": query, "max_results": 5})
        if isinstance(web, dict) and web.get("results"):
            web_text = json.dumps(web["results"], ensure_ascii=False)[:2500]
            tool_calls_log.append({"name": "websearch", "args": {"query": query},
                                   "result_summary": str(web)[:200], "result_full": web,
                                   "thought": f"联网补充「{query}」的当代论据与背景"})
    except Exception:
        web_text = ""
    # ESSAY_PROMPT（2026-08-18 修复：拆分前即无定义，write_essay 新作文路径会 NameError）
    prompt = ESSAY_PROMPT.format(genre=genre, topic=topic, word_count=word_count,
                                 extra=extra or "无", retrieval=retrieval)
    if web_text:
        prompt += (f"\n\n联网检索结果（当代论据/时事背景/其他论述——用于丰富论据层次, "
                   f"引用时以[标题](链接)标注来源; 若与题目无关可忽略）:\n{web_text}")
    messages = [{"role": "user", "content": prompt}]
    resp = llm_chat(messages, temperature=0.75, max_tokens=min(word_count * 2 + 500, 4000))
    reply = (resp["choices"][0]["message"].get("content") or "").strip() or "（生成失败，请重试）"
    citations = [{"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                  "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")}
                 for item in result.get("results", [])[:4]]
    for tc in tool_calls_log:
        tc.pop("result_full", None)
    slot["essays"][topic] = {"text": reply, "genre": genre, "word_count": word_count}
    return reply, citations, tool_calls_log

# ── 工具 8: generate_image（生图——Agnes Image 2.1 Flash, 文生图; 免费档 $0/张; 支持多轮修改）──
AGNES_API_URL = "https://apihub.agnes-ai.com/v1/images/generations"
AGNES_MODEL = "agnes-image-2.1-flash"
# 内置哲学风格系统提示词: 全局视觉规范（象征/色彩/构图/质感）
AGNES_PHILO_STYLE = (
    "这是哲学概念可视化图像, 必须遵循哲学插图美学: "
    "①象征与隐喻优先——光、阶梯、深渊、圆环、面具、闪电等意象承载思想; "
    "②色彩克制而深刻——低饱和暖调或黑白基调, 至多一个强调色; "
    "③构图庄重——对称或纵深透视, 适当留白, 像古典思想史铜版画或书籍插页; "
    "④质感写实——布面油画颗粒、铜版画刻线、黑白木刻或电影级写实; "
    "⑤拒绝直白图解——保留可诠释的暗示与张力。高信息密度, 细节丰富。"
)
# 主题→风格方向匹配（哲学概念 → 艺术风格; 未命中用默认哲学插图风）
AGNES_STYLE_HINTS = [
    (["洞穴", "理想国", "寓言", "囚徒"], "古典主义油画, 明暗对比, 柏拉图式光影寓言"),
    (["永恒轮回", "轮回", "圆环", "环"], "衔尾蛇与循环几何, 超现实主义, 神秘象征"),
    (["超人", "查拉图斯特拉", "山峰", "闪电", "攀登"], "浪漫主义崇高风景画, 垂直构图, 剪影与光"),
    (["存在", "荒诞", "虚无", "西西弗", "孤独", "荒原"], "表现主义, 粗粝笔触, 存在主义的孤寂感"),
    (["权力意志", "尼采", "酒神", "日神", "悲剧"], "德国浪漫主义铜版画, 深色基调金色勾勒"),
    (["辩证法", "正反合", "扬弃", "黑格尔"], "三重视觉结构与螺旋构图, 抽象几何"),
    (["斯多葛", "节制", "坚忍", "罗马"], "古典雕塑与静物, 大理石质感, 平静庄重"),
    (["虚空", "禅", "道家", "无为", "老子", "庄子"], "水墨画, 留白意境, 极简山水的空灵"),
    (["仁", "礼", "孔子", "儒家"], "宋代山水与文人画, 卷轴构图, 温润墨色"),
    (["启蒙", "理性", "光", "自由", "卢梭"], "新古典主义, 晨光穿透云层, 崇高理性之光"),
]

def _agnese_enhance_prompt(prompt):
    """哲学风格增强: 主题风格匹配 + 全局视觉规范 + 高密度要求"""
    style = None
    for keywords, hint in AGNES_STYLE_HINTS:
        if any(k in prompt for k in keywords):
            style = hint
            break
    head = f"主题: {prompt}。风格: {style or '哲学概念插图, 古典与现代融合'}。"
    return f"{head}{AGNES_PHILO_STYLE}"

# 无代理 opener（避免 urllib 代理检测触发反向 DNS 11s 超时——与 admin.py 同款修复）
_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def _download_image(url, save_to):
    req = urllib.request.Request(url, headers={"User-Agent": "PhiAgent/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:   # 走系统代理（Agnes 存储域国内需代理）
        data = r.read()
    with open(save_to, "wb") as f:
        f.write(data)
    return len(data)

def _wiki_search_image(query):
    """维基百科搜参考图（pageimages 原创图 URL）——中文优先, 英文兜底"""
    import urllib.parse as _up
    for lang in ("zh", "en"):
        url = (f"https://{lang}.wikipedia.org/w/api.php?action=query&generator=search"
               f"&gsrsearch={_up.quote(query)}&gsrlimit=4&gsrnamespace=0"
               f"&prop=pageimages&piprop=original&format=json&origin=*")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PhiAgent/1.0"})
            with _NO_PROXY.open(req, timeout=20) as r:
                data = json.loads(r.read().decode())
            for pid, page in (data.get("query", {}).get("pages", {}) or {}).items():
                for key in ("original", "thumbnail"):
                    src = page.get(key, {}).get("source")
                    if src:
                        return src
        except Exception:
            continue
    return None

def _local_reference_image(name):
    """本地哲学家肖像（DP 数据 617 张）: 括号前基础名或包含匹配"""
    if not PHILOSOPHER_DIR.exists():
        return None
    for f in os.listdir(PHILOSOPHER_DIR):
        if not f.endswith((".webp", ".jpg", ".png")):
            continue
        base = Path(f).stem.split(" (")[0].strip()
        if base and (base == name or (name and base in name) or (name and name in base)):
            return str(PHILOSOPHER_DIR / f)
    return None

def _detect_reference(prompt):
    """自动判断是否需要参考图: 本地肖像文件名匹配 > 常见别名 > 明确参考意图"""
    # 1) 本地哲学家肖像（DP 数据, 617 张——比网络搜索更可靠的参考图源）
    if PHILOSOPHER_DIR.exists():
        for f in os.listdir(PHILOSOPHER_DIR):
            if not f.endswith((".webp", ".jpg", ".png")):
                continue
            base = Path(f).stem.split(" (")[0].strip()
            if base and len(base) <= 12 and base in prompt:
                return base
    # 2) 常见别名（本地无文件时, 用于 wiki 兜底检索）
    for alias in ("苏格拉底", "柏拉图", "亚里士多德", "尼采", "康德", "黑格尔", "叔本华", "马克思",
                  "维特根斯坦", "海德格尔", "萨特", "笛卡尔", "斯宾诺莎", "休谟", "卢梭",
                  "老子", "庄子", "孔子", "孟子", "福柯", "德里达", "克尔凯郭尔"):
        if alias in prompt:
            return alias
    # 3) 明确参考意图（非人物, 概念图带参考词）
    if any(w in prompt for w in ("参考", "肖像", "写真", "画像", "写实人像", "长相")):
        return prompt[:60]
    return None

def _exec_generate_image(args):
    slot = _mem_slot()
    prompt = (args.get("prompt") or "").strip()
    if not prompt:
        return {"error": "缺少图像描述 prompt"}
    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        return {"error": "服务端未配置 AGNES_API_KEY"}
    size = args.get("size") or "1K"
    ratio = args.get("ratio") or "1:1"
    enhanced = _agnese_enhance_prompt(prompt)   # 内置哲学风格 system prompt
    body = {"model": AGNES_MODEL, "prompt": enhanced, "size": size, "ratio": ratio,
            "extra_body": {"response_format": "url"}}
    reference = {"used": False}
    # 多轮修改: 修改意图词 + 存在上次生成图 → 图生图修改（直接对上一轮结果改）
    MODIFY_HINTS = ("修改", "改成", "换成", "调整", "重画", "美化", "换个", "加上", "去掉",
                    "放大", "缩小", "夜景", "日景", "换个角度", "重新画", "优化", "调色", "改一下")
    if slot["image"] and any(w in prompt for w in MODIFY_HINTS):
        prev_path = PUBLIC / slot["image"]["local"].lstrip("/")
        if prev_path.exists():
            try:
                with open(prev_path, "rb") as f:
                    prev_data = f.read()
                if prev_data and len(prev_data) < 8 * 1024 * 1024:
                    import base64
                    body["extra_body"]["image"] = ["data:image/jpeg;base64," + base64.b64encode(prev_data).decode()]
                    reference = {"used": True, "query": f"修改上一张图（{slot['image']['local']}）",
                                 "source": slot["image"]["local"]}
            except Exception:
                pass  # 读取上次图失败 → 降级文生图
    # 参考图绑定: 哲学家肖像/参考意图 → 本地肖像优先, 维基百科兜底 → Agnes 图生图（形象准确）
    ref_q = _detect_reference(prompt)
    if ref_q and not body["extra_body"].get("image"):
        img_data = None
        ref_src = None
        # 1) 本地哲学家肖像（DP 数据, 离线可靠）
        local_path = _local_reference_image(ref_q)
        if local_path:
            try:
                with open(local_path, "rb") as f:
                    img_data = f.read()
                ref_src = local_path
            except Exception:
                img_data = None
        # 2) 维基百科兜底（本地无肖像时）
        if not img_data:
            src = _wiki_search_image(ref_q)
            if src:
                try:
                    img_req = urllib.request.Request(src, headers={"User-Agent": "PhiAgent/1.0"})
                    with _NO_PROXY.open(img_req, timeout=30) as r:
                        img_data = r.read()
                    ref_src = src
                except Exception:
                    img_data = None
        if img_data and len(img_data) < 8 * 1024 * 1024:
            import base64
            body["extra_body"]["image"] = ["data:image/jpeg;base64," + base64.b64encode(img_data).decode()]
            reference = {"used": True, "query": ref_q, "source": ref_src}
    req = urllib.request.Request(AGNES_API_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {api_key}"})
    try:
        # Agnes 需走系统代理（国内直连被 RST）; 首次代理检测有 ~1s 开销, 可接受
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"Agnes HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}"}
    except Exception as e:
        return {"error": f"Agnes 请求失败: {str(e)[:120]}", "hint": "Apihub 需网络代理（国内直连被墙）——请开启系统代理后重试"}
    items = resp.get("data") or []
    if not items or not items[0].get("url"):
        return {"error": "Agnes 未返回图像", "raw": str(resp)[:200]}
    url = items[0]["url"]
    AGNES_IMG_DIR.mkdir(parents=True, exist_ok=True)
    fn = hashlib.md5(f"{prompt}|{time.time()}".encode()).hexdigest()[:12] + ".png"
    save_to = AGNES_IMG_DIR / fn
    try:
        size_bytes = _download_image(url, save_to)
    except Exception as e:
        return {"error": f"图像下载失败: {str(e)[:120]}", "remote_url": url}
    local = f"/agent_images/{fn}"
    slot["image"] = {"prompt": prompt, "local": local}
    _save_agent_memory()   # 持久化多轮修改记忆（per-user）
    return {"image_url": local, "prompt": prompt, "size": f"{size} {ratio}", "bytes": size_bytes,
            "reference": reference,
            "note": f"生成成功。回答中请以 ![{prompt[:20]}]({local}) 引用该图"}

register_tool(
    "generate_image",
    "生成哲学艺术图像（Agnes 生图: 概念插画/肖像/意境图）。人物肖像自动绑定本地参考图; '修改/改成/调整/重画刚才的图'时基于上次结果图生图修改。触发: '生成图片/画一张画/概念插画/画像/艺术图'。**星图/脑图/关系图/结构图/地图不是本工具职责——那是 conceptual_map 的。**",
    {"type": "object", "properties": {"prompt": {"type": "string", "description": "图像描述（可中文, 建议: 主体+场景+风格+构图）"}, "size": {"type": "string", "description": "档位 1K/2K/3K/4K（默认 1K）"}, "ratio": {"type": "string", "description": "宽高比 1:1/16:9/9:16/4:3/3:4 等（默认 1:1）"}}, "required": ["prompt"]},
    _exec_generate_image,
)

def _auto_visualize(prompt):
    """自动可视化: 生一张哲学风格概念图（失败不阻断主流程）"""
    try:
        img = _exec_generate_image({"prompt": prompt, "size": "1K"})
        if img and img.get("image_url"):
            return img["image_url"]
    except Exception:
        pass
    return None

# ── 工具 19: role_play（扮演——人格/记忆层: AIAuthor 数字作者数据）──
# 数据源: PhiAgent/data/ai_author/（AIAuthor 六大库镜像: persona 模型 + 时期快照
#         + 风格词库 + 矛盾规则 + 564 条五维记忆 + 野史轶事）
_persona_bundle = None
_persona_lock = threading.Lock()

def _load_persona_bundle():
    """加载尼采人格包（带缓存, 缺文件容错）"""
    global _persona_bundle
    if _persona_bundle is None:
        with _persona_lock:
            if _persona_bundle is None:
                b = {}
                for key, rel in {
                    "persona": "persona/persona_model.json",
                    "snapshots": "persona/persona_snapshots.json",
                    "style": "persona/style_lexicon.json",
                    "rules": "persona/contradiction_rules.json",
                    "memories": "memory/nietzsche_memories.json",
                    "anecdotes": "memory/anecdotes.json",
                }.items():
                    p = AI_DIR / rel
                    if p.exists():
                        try:
                            b[key] = json.load(open(p, encoding="utf-8"))
                        except Exception:
                            b[key] = {}
                _persona_bundle = b
    return _persona_bundle

def _recall_memories(query, limit=6):
    """记忆召回: 字符 bigram 重叠计分（event 字段加权 2×, significance/description 1×）"""
    bundle = _load_persona_bundle()
    memories = bundle.get("memories", {}).get("memories", [])
    q = (query or "").replace(" ", "").strip()
    if len(q) < 2 or not memories:
        return memories[:limit]
    def grams(t):
        t = t.replace(" ", "")
        return {t[i:i + 2] for i in range(len(t) - 1)}
    qg = grams(q)
    scored = []
    for m in memories:
        event = str(m.get("event", ""))
        sig = str(m.get("significance", ""))
        desc = str(m.get("description", ""))
        s = len(grams(event) & qg) * 2 + len(grams(sig) & qg) + len(grams(desc) & qg)
        if s > 0:
            scored.append((s, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:limit]] or memories[:limit]

def _exec_role_play(args):
    name = (args.get("philosopher") or args.get("persona") or args.get("name") or "").strip()
    if name and "尼采" not in name:
        return {"error": f"人格层暂未覆盖「{name}」（当前仅尼采, 数据来自 AIAuthor 数字作者系统）",
                "hint": "可改用 get_philosopher 查资料 / query_graph 查思想关联"}
    query = (args.get("question") or args.get("topic") or args.get("query") or "").strip()[:80]
    bundle = _load_persona_bundle()
    persona = bundle.get("persona", {})
    snapshots = bundle.get("snapshots", {})
    style = bundle.get("style", {})
    rules = bundle.get("rules", {})
    # 时期快照: 未指定时期 → 晚期成熟尼采（1883-1888）; fallback 仅是指示字段
    late = ((snapshots.get("snapshots") or {}).get("late") or {}) if isinstance(snapshots.get("snapshots"), dict) else {}
    snap = late or snapshots.get("fallback", {})
    memories = _recall_memories(query, 6)
    anecdotes = (bundle.get("anecdotes", {}).get("memories", []) or [])[:2]
    # 精简组装（工具结果注入 LLM 上下文截断 4000 字符, 优先保人格核心）
    reasoning = persona.get("reasoning_rules", {})
    reasoning_rules = reasoning.get("rules", []) if isinstance(reasoning, dict) else []
    style_model = persona.get("style_model", {})
    style_pref = ""
    if isinstance(style_model, dict):
        style_pref = (f"形式偏好: {json.dumps(style_model.get('形式偏好', {}), ensure_ascii=False)}; "
                      f"核心修辞: {json.dumps((style_model.get('核心修辞') or [])[:4], ensure_ascii=False)}")[:300]
    glossary = persona.get("concept_glossary", {})
    glossary_entries = (glossary.get("entries", []) if isinstance(glossary, dict) else [])[:3]
    constraints = ((persona.get("output_constraints") or {}).get("constraints", [])) if isinstance(persona.get("output_constraints"), dict) else []
    values = ((persona.get("value_model") or {}).get("values", {})) if isinstance(persona.get("value_model"), dict) else {}
    return {
        "role": "扮演人格包（弗里德里希·尼采）",
        "instruction": ("用户要求以尼采第一人称回答。以下人格包来自 AIAuthor 数字作者系统（23 本语料+图谱 v7+564 条记忆构建）。"
                        "必须: ①以'我'自称, 以尼采口吻与世界观作答; ②遵守输出约束（知识边界, 引用须诚实）; ③风格贴近 style 要点; "
                        "④可调用 memories 真实生平记忆作支撑; ⑤超范围问题以尼采的批判态度回应, 不编造事实。"),
        "identity": ((persona.get("meta") or {}).get("description") or "")[:400],
        "values": [{"v": k, "w": v} for k, v in list(values.items())[:8]],
        "reasoning_rules": [{"id": r.get("id"), "trigger": r.get("trigger"), "path": (r.get("path") or "")[:120]}
                            for r in reasoning_rules[:3]],
        "output_constraints": [{"rule": c.get("rule"), "detail": (c.get("detail") or "")[:80]} for c in constraints[:6]],
        "emotion_baseline": json.dumps((persona.get("emotional_model") or {}).get("baseline", {}), ensure_ascii=False)[:300],
        "style": style_pref,
        "concept_anchors": [{"term": e.get("term"), "canon": (e.get("canon") or "")[:80]} for e in glossary_entries],
        "period": {"name": snap.get("name"), "range": snap.get("range"), "age": snap.get("age"),
                   "identity": (snap.get("identity") or "")[:100], "dimensions": snap.get("dimensions"),
                   "signature": (snap.get("signature") or "")[:150],
                   "speech_markers": (snap.get("speech_markers") or [])[:5]},
        "contradiction_rules": [{"id": r.get("id"), "conflict": r.get("conflict")} for r in (rules.get("rules") or [])[:3]],
        "memories": [{"type": m.get("type"), "event": m.get("event"), "year": m.get("year"),
                      "period": m.get("period"), "significance": (m.get("significance") or "")[:80]} for m in memories],
        "anecdotes": [{"event": (m.get("event") or "")[:120], "credibility": m.get("credibility")} for m in anecdotes],
    }

register_tool(
    "role_play",
    "扮演哲学家（人格层）——以尼采第一人称回答。persona/记忆来自 AIAuthor 数字作者系统, 自动召回相关生平记忆。触发: 用户要求'扮演尼采/如果你是尼采/尼采会怎么看/以尼采的口吻'。",
    {"type": "object", "properties": {"philosopher": {"type": "string", "description": "哲学家名（当前人格层仅覆盖尼采）"}, "question": {"type": "string", "description": "用户的问题/话题"}}, "required": ["question"]},
    _exec_role_play,
)

# ── 交互式辩论: auto（一次性）/ step（逐轮, 用户触发）/ vs_user（用户参与）──
# 会话状态 per-user 化（2026-08-14 P0）: 存 _mem_slot()["debate"], 不再全局共享

def _philosopher_profile(name):
    """哲学家思想档案（辩论人格注入层）——尼采走 AIAuthor 完整人格包, 其他哲学家走资料库。
    LoRA 接入点: 未来各哲学家 LoRA 就绪时, 在此处返回 LoRA 模型标识/加载对应模型发言。"""
    if "尼采" in name:
        b = _load_persona_bundle()
        persona = b.get("persona", {}) or {}
        snaps = b.get("snapshots", {}) or {}
        late = ((snaps.get("snapshots") or {}).get("late") or {}) if isinstance(snaps.get("snapshots"), dict) else {}
        meta = persona.get("meta", {}) or {}
        values = list(((persona.get("value_model") or {}).get("values", {}) or {}).items())[:5]
        parts = []
        if meta.get("description"):
            parts.append(f"身份: {meta['description'][:150]}")
        if late.get("identity"):
            parts.append(f"晚期尼采(1883-1888): {late['identity']}")
        if late.get("signature"):
            parts.append(f"核心思想: {late['signature']}")
        if values:
            parts.append("价值观: " + "; ".join(f"{k}(权重{v})" for k, v in values))
        return "；".join(parts) or None
    phils = get_philosophers()
    entry = None
    if isinstance(phils, dict):
        entry = phils.get(name)
        if not entry:
            for k, v in phils.items():
                if k and (name in k or k in name):
                    entry = v
                    break
    if entry and isinstance(entry, dict):
        parts = []
        if entry.get("era"):
            parts.append(f"年代: {entry['era']}")
        if entry.get("school"):
            parts.append(f"流派: {entry['school']}")
        if entry.get("bio"):
            parts.append(f"简介: {entry['bio'][:180]}")
        books = entry.get("books")
        if isinstance(books, list) and books:
            names = [b.get("title") if isinstance(b, dict) else str(b) for b in books[:3]]
            parts.append("代表作: " + "、".join(str(n) for n in names))
        return "；".join(parts) or None
    return None

def _debate_map_text(d_text):
    """辩论 → mermaid 观点演变图"""
    try:
        map_prompt = (f"将以下哲学辩论提炼为 mermaid flowchart 观点演变图（只输出 flowchart 代码本身, 不要 ``` 围栏）:\n"
                      f"规则: 节点=各哲学家的核心立场（10字内）; 箭头=反驳/回应关系, 用 '-->|反驳|' 或 '-->|回应|'; 最后加一个'合题/未决'节点。\n\n"
                      f"辩论:\n{d_text[:2500]}")
        mresp = llm_chat([{"role": "user", "content": map_prompt}], temperature=0.5, max_tokens=600)
        mt = (mresp["choices"][0]["message"].get("content") or "").strip()
        mt = re.sub(r"^```(?:mermaid)?\s*", "", mt)
        mt = re.sub(r"\s*```$", "", mt)
        if mt.startswith(("flowchart", "graph")):
            return f"```mermaid\n{mt}\n```"   # 带围栏返回, 前端直接渲染
        return None
    except Exception:
        return None

def _debate_round(sp_list, topic, ctx, round_no, user_speech=None):
    """生成一轮辩论发言（每人一次）; user_speech 非空时要求回应它"""
    round_out = []
    for sp in sp_list:
        profile = _philosopher_profile(sp)   # 人格注入: 思想档案（尼采=完整人格包, 其他=资料库）
        inject = f"\n思想档案（保持其真实思想与风格, 发言必须体现档案中的思想特征）:\n{profile}" if profile else ""
        prompt = (f"你是哲学家{sp}。针对论题「{topic}」，发表你的立场与论证（200字内）。{inject}"
                  f"辩论纪律（高阶）: ①反驳必须攻击对方体系的真正软肋（如先验演绎的循环性、范畴与内容的关系、必然性的根基）, "
                  f"避免打在对方体系外的无效反驳——先准确复述对方立场再攻击; ②涉及对方体系时忠实其原意, 不歪曲; "
                  f"③若为最终结论, 明确区分'体系内立场'与'后康德综合立场'。"
                  f"这是辩论第{round_no}轮。{'可回应前一位发言。' if ctx else '请先亮明核心立场。'}"
                  + (f"\n已有发言:\n{ctx}" if ctx else "")
                  + (f"\n用户的当前发言（必须正面回应, 并指出其逻辑漏洞或接受其合理处）:\n{user_speech}" if user_speech else ""))
        msgs = [{"role": "system", "content": f"你是{sp}——保持其真实思想风格, 用中文发言。"},
                {"role": "user", "content": prompt}]
        resp = llm_chat(msgs, temperature=0.9, max_tokens=400)
        speech = (resp["choices"][0]["message"].get("content") or "").strip()
        round_out.append(f"{sp}: {speech}")
    return round_out

def _exec_debate(args):
    slot = _mem_slot()
    topic = (args.get("topic") or "").strip()
    speakers = args.get("speakers") or "尼采、柏拉图"
    sp_list = [s.strip() for s in speakers.replace("和", "、").replace("与", "、").split("、") if s.strip()][:3] or ["尼采", "柏拉图"]
    mode = args.get("mode") or "auto"
    action = (args.get("action") or "start").strip().lower()
    user_speech = (args.get("user_reply") or "").strip()
    # 意图自动检测（LLM 未显式传 action 时）
    if action == "start":
        if any(w in topic for w in ("结束", "总结", "停止", "裁决", "收尾")):
            action = "summary"
        elif any(w in topic for w in ("继续", "下一轮", "接着", "再来", "加一轮", "第二轮", "第三轮")):
            action = "continue"
    # ── 结束辩论: 总结 + 演变图 ──
    if action == "summary" and slot["debate"]:
        sess = slot["debate"]
        d_text = "\n".join(sess["history"])
        prompt = (f"辩论结束, 请总结（400字内）: ①各方核心立场 ②最强交锋点（谁对谁的哪一点构成实质威胁）"
                  f"③是否达成共识/合题（明确标注'体系内'还是'后康德综合'视角）。\n\n辩论记录:\n{d_text[:4000]}")
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=900)
        summary = (resp["choices"][0]["message"].get("content") or "").strip()
        slot["debate"] = None
        _save_agent_memory()
        return {"debate_summary": summary, "map_text": _debate_map_text(d_text),
                "note": "辩论已结束。可发起新辩论。"}
    # ── 用户参与模式: 用户发言 → 哲学家回应 ──
    if user_speech and slot["debate"] and slot["debate"].get("mode") == "vs_user":
        sess = slot["debate"]
        ctx = "\n".join(sess["history"][-4:])
        round_out = _debate_round(sess["speakers"], sess["topic"], ctx, sess["rounds_done"] + 1, user_speech)
        sess["history"] += [f"用户: {user_speech}"] + round_out
        sess["rounds_done"] += 1
        _save_agent_memory()
        return {"debate": round_out, "note": "你可以继续反驳或提问, 或说'结束辩论'让我总结。"}
    # ── 逐轮模式: 继续下一轮 ──
    if action == "continue" and slot["debate"]:
        sess = slot["debate"]
        ctx = "\n".join(sess["history"][-4:])
        round_out = _debate_round(sess["speakers"], sess["topic"], ctx, sess["rounds_done"] + 1)
        sess["history"] += round_out
        sess["rounds_done"] += 1
        _save_agent_memory()
        return {"debate": round_out, "note": f"第{sess['rounds_done']}轮结束。说'继续'进入下一轮, '结束辩论'总结。"}
    # ── step / vs_user: 初始化会话 + 第一轮 ──
    if mode in ("step", "vs_user"):
        slot["debate"] = {"topic": topic, "speakers": sp_list, "mode": mode,
                           "rounds_done": 1, "history": []}
        round_out = _debate_round(sp_list, topic, "", 1)
        slot["debate"]["history"] = round_out
        _save_agent_memory()
        note = ("辩论开始（逐轮模式）。说'继续'进入下一轮, '结束辩论'总结。" if mode == "step"
                else "辩论开始（你参与）。请反驳或提问, 哲学家会回应你。")
        return {"debate": round_out, "note": note}
    # ── auto: 一次性生成全部轮次（默认, 原逻辑）──
    rounds = _int_arg(args, "rounds", 2, 1, 3)
    debate = []
    for r in range(rounds):
        debate.extend(_debate_round(sp_list, topic, "\n".join(debate[-3:]), r + 1))
    ret = {"topic": topic, "debate": debate}
    img = _auto_visualize(f"哲学辩论: {topic}——多位思想者围绕同一论题的象征性对峙, 讲台与光影交错")
    if img:
        ret["image_url"] = img
        ret["note"] = f"回答末尾请以 ![辩论图]({img}) 引用该图"
    ret["map_text"] = _debate_map_text("\n".join(debate))
    return ret

register_tool("philosopher_debate",
    "哲学家辩论——三种模式: auto=一次性多轮（默认）; step=逐轮（用户说'继续'触发下一轮, '结束辩论'总结）; vs_user=用户参与（用户发言后传 user_reply=用户的话, 哲学家回应）。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "论题（'继续'/'结束辩论'等指令也放这里）"},
        "speakers": {"type": "string", "description": "哲学家, 逗号分隔"},
        "mode": {"type": "string", "enum": ["auto", "step", "vs_user"], "description": "辩论模式"},
        "action": {"type": "string", "enum": ["start", "continue", "summary"], "description": "逐轮模式: continue=下一轮, summary=结束总结"},
        "user_reply": {"type": "string", "description": "vs_user 模式: 用户的发言"}},
     "required": ["topic"]},
    _exec_debate)

# Phase T（T7/T2）: thought_experiment 产物结构化（设定/多立场推演/揭示的问题）。
# O4: engine 侧重入治理（SkillReentryTracker）已删除——同一实验是否值得再次调用
# 由 Main Agent 依系统提示的技能重入纪律自主判断。
def _exec_thought_exp(args):
    from tool_contracts import scaffold_result, extract_json
    slot = _mem_slot()
    base = (args.get("base") or "").strip()
    if not base:
        return {"error": "缺少思想实验基础设定"}
    prev_exp = slot.get("experiment")
    # 变体迭代: 用户明确要求变体（修改词）+ 存在上次实验 → 基于上次重推演, 对比立场变化
    if prev_exp and any(w in base for w in ("改", "换成", "变体", "如果", "假设", "变化", "不同", "加", "减")):
        prompt = (f"用户对上次思想实验提出变体: 「{base}」\n"
                  f"上次实验:\n{str(prev_exp.get('text', ''))[:1500]}\n\n"
                  f"请重新推演该变体, 只输出 JSON（不要围栏）:\n"
                  f'{{"setting": "新设定（100字内）",\n'
                  f' "stance_projections": [{{"stance": "哲学立场名", "projection": "该立场在此变体下的推演（50字）", "shift": "与上次实验相比结论的变化"}}],\n'
                  f' "revealed_problem": "变体揭示的哲学问题（1-2句）"}}')
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.9, max_tokens=1000)
        data = extract_json(resp["choices"][0]["message"].get("content"))
        if not isinstance(data, dict) or not data.get("setting"):
            data = {"setting": (resp["choices"][0]["message"].get("content") or "").strip()[:600],
                    "stance_projections": [], "revealed_problem": ""}
        reply = data.get("setting", "")
        slot["experiment"] = {"base": base, "text": json.dumps(data, ensure_ascii=False)[:1500]}
        _save_agent_memory()
        return scaffold_result("thought_experiment_scaffold",
                               "变体推演脚手架: 新设定 + 多立场推演对比 + 揭示的问题",
                               confidence=0.7,
                               presentation_hint="主 Agent 以连续叙述呈现实验场景, 不逐条罗列 JSON 字段",
                               **data)
    prompt = (f"基于「{base}」设计一个哲学思想实验, 只输出 JSON（不要围栏）:\n"
              f'{{"setting": "实验设定（100字内, 场景具体可想象）",\n'
              f' "stance_projections": [{{"stance": "哲学立场名", "projection": "该立场下的推演（50字）"}}],\n'
              f' "revealed_problem": "它揭示的哲学问题（1-2句）"}}\n'
              f"3 个立场推演。用中文。")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.9, max_tokens=800)
    data = extract_json(resp["choices"][0]["message"].get("content"))
    if not isinstance(data, dict) or not data.get("setting"):
        raw = (resp["choices"][0]["message"].get("content") or "").strip()
        data = {"setting": raw[:600] or base, "stance_projections": [], "revealed_problem": ""}
    slot["experiment"] = {"base": base, "text": json.dumps(data, ensure_ascii=False)[:1500]}
    _save_agent_memory()
    return scaffold_result("thought_experiment_scaffold",
                           "思想实验脚手架: 设定 + 多立场推演 + 揭示的问题——场景叙述与判断由主 Agent 完成",
                           confidence=0.7,
                           presentation_hint="主 Agent 以连续叙述呈现实验场景并回答用户之问, 不逐条罗列 JSON 字段",
                           **data)

register_tool("thought_experiment",
    "设计/推演哲学思想实验（电车难题变体/洞穴比喻现代版）——返回设定/多立场推演/揭示问题的结构化脚手架; 用户明确要求变体时（'改成/换成/如果'）基于上次实验迭代。同一实验的重复调用受重入策略约束——除非用户要求迭代或前次结果不可用。",
    {"type": "object", "properties": {"base": {"type": "string", "description": "思想实验基础设定（变体迭代时描述变化点）"}}, "required": ["base"]},
    _exec_thought_exp)
