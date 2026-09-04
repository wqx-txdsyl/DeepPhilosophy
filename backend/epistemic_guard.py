# -*- coding: utf-8 -*-
"""Epistemic Guard（Phase 1）——结构级认识论护栏

三个 P0 组件（确定性规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  PremiseVerifier           用户事实前提抽取与校正（非阻塞: 先校正, 再回答）
  EpistemicClaimClassifier  Claim 知识论分级（9 类, 每类绑定表达强度模板）
  CounterfactualAuthorGuard 作者反事实识别: 历史证据 vs 反事实推演分离

Phase 1 边界（见任务书）:
  - confidence 恒为 null（完整 confidence engine 留 Phase 2）
  - 不改 Graph / Memory / Persona Snapshot / 矢量库 / 工具注册表 / 流式协议
  - 护栏以"前置系统消息注入 + 应答后校验补正"的结构生效, 失败绝不影响主流程

用法（engine_langgraph.stream_agent 内）:
  verdict = run_epistemic_guards(req_message, agent, language)
  for inj in verdict["injections"]: messages.append(SystemMessage(content=inj))
  ... 应答完成后: scan_answer(verdict, full_answer) → 校验/补正/记录
"""
import json
import re
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent          # backend/
ROOT = BASE.parent
LOG_FILE = BASE / "data" / "epistemic_guard.jsonl"   # 运行时记录（backend/data 已 gitignore）

# ═══════════════════════════════════════════════════════
# 1. 知识论类型定义（Phase 1 内部统一定义, 至少 9 类）
# ═══════════════════════════════════════════════════════
EPISTEMIC_TYPES = [
    "SOURCE_FACT",                # 文本明确写到的事实（带可核验出处）
    "DIRECT_QUOTE",              # 原文直接引语
    "TEXTUAL_INFERENCE",         # 对文本的解释性推断（文学/哲学解读）
    "CROSS_TEXT_INTERPRETATION", # 借用另一思想家框架的跨文本解读
    "SCHOLARLY_INTERPRETATION",  # 学界/研究界的解释
    "AUTHOR_COUNTERFACTUAL",     # 关于作者本人会怎么想的反事实推演
    "USER_PREMISE",              # 用户提出的前提/假设
    "SPECULATION",               # 推测（作者未表、亦无研究共识）
    "UNKNOWN",                   # 现有材料不足以判断
]

# 语言约束: 不同类型绑定不同表达强度（Phase 1 直接以模板绑定, 注入时引用）
EPISTEMIC_LANGUAGE = {
    "SOURCE_FACT": "文本明确写道……",
    "DIRECT_QUOTE": "原文写道……",
    "TEXTUAL_INFERENCE": "这可以理解为……",
    "CROSS_TEXT_INTERPRETATION": "若采用加缪的框架，可以把它读作……",
    "SCHOLARLY_INTERPRETATION": "某种研究解释认为……",
    "AUTHOR_COUNTERFACTUAL": "我们无法知道作者本人会如何评价；依据其现有思想……",
    "SPECULATION": "一种可能的解释是……",
    "UNKNOWN": "现有材料不足以判断……",
    "USER_PREMISE": "基于你提出的这个前提……",
}

# 反事实禁语（"作者一定/绝不会……"除非存在直接可靠史料）
COUNTERFACTUAL_FORBIDDEN = ["绝不会", "一定会", "肯定会", "必定会", "必然认为",
                            "他肯定会", "她肯定会", "一定会激动", "绝不会是"]
_STRONG_MODAL_RE = re.compile(r"(一定|必然|肯定|必定|想必|无疑|显然|绝不会|绝无可能)")


# ═══════════════════════════════════════════════════════
# 2. 数据源（懒惰加载: books.json（作品→作者） + philosophers.json（哲学家名单））
# ═══════════════════════════════════════════════════════
_books_cache, _philos_cache = None, None
_cache_lock = threading.Lock()


def _strip_marks(s):
    return (s or "").replace("《", "").replace("》", "").replace(" ", "").strip()


def _norm_author(s):
    """作者名归一化: 去中间点变体/全名, 留短名（海德格尔 / 马丁·海德格尔 → 海德格尔）"""
    t = (s or "").strip()
    for sep in ("·", ".", "·"):
        t = t.replace(sep, "·")
    if "·" in t and t.split("·")[-1]:
        return t.split("·")[-1].strip()
    return t


def _load_books():
    """app/public/books.json（唯一正式书目, 409 本）→ {书名: {作者, 作者短名, id}}"""
    global _books_cache
    if _books_cache is None:
        with _cache_lock:
            if _books_cache is None:
                try:
                    raw = json.load(open(ROOT / "app" / "public" / "books.json", encoding="utf-8"))
                    out = {}
                    for b in raw:
                        t = _strip_marks(b.get("title") or "")
                        a = b.get("author") or ""
                        if t:
                            out[t] = {"author": a, "author_short": _norm_author(a), "id": b.get("id")}
                    _books_cache = out
                except Exception:
                    _books_cache = {}
    return _books_cache


def _load_philosophers():
    """backend/data/philosophers.json（id→记录）→ {短名: 原名} + 原始短名集合"""
    global _philos_cache
    if _philos_cache is None:
        with _cache_lock:
            if _philos_cache is None:
                try:
                    raw = json.load(open(BASE / "data" / "philosophers.json", encoding="utf-8"))
                    vals = list(raw.values()) if isinstance(raw, dict) else raw
                    names = set()
                    for v in vals:
                        n = (v.get("name") or "").strip()
                        if n:
                            names.add(n)
                            names.add(_norm_author(n))
                    _philos_cache = names
                except Exception:
                    _philos_cache = set()
    return _philos_cache


# 常见别称: 哲学家短名 ↔ 全名/拉丁名（用户口语常用短名, 需匹配到")
PHILOSOPHER_ALIASES = {
    "尼采": "尼采", "弗里德里希·尼采": "尼采", "f·尼采": "尼采",
    "加缪": "加缪", "阿尔贝·加缪": "加缪",
    "叔本华": "叔本华", "亚瑟·叔本华": "叔本华",
    "康德": "康德", "伊曼努尔·康德": "康德",
    "黑格尔": "黑格尔", "格奥尔格·黑格尔": "黑格尔",
    "萨特": "萨特", "让-保罗·萨特": "萨特",
    "海德格尔": "海德格尔", "马丁·海德格尔": "海德格尔",
    "维特根斯坦": "维特根斯坦", "路德维希·维特根斯坦": "维特根斯坦",
    "柏拉图": "柏拉图", "苏格拉底": "苏格拉底", "亚里士多德": "亚里士多德",
    "马克思": "马克思", "卡尔·马克思": "马克思",
    "庄子": "庄子", "老子": "老子", "孔子": "孔子", "释迦牟尼": "释迦牟尼", "佛陀": "释迦牟尼",
}


def _match_philosopher(text):
    """在文本中查找已知哲学家名（返回规范短名列表, 按出现顺序, 去重）"""
    pool = set()
    pool |= set(PHILOSOPHER_ALIASES.keys())
    pool |= _load_philosophers()
    found = []
    seen = set()
    # 长名优先（"弗里德里希·尼采" 先于 "尼采", 防短名吞长名）
    for name in sorted(pool, key=len, reverse=True):
        n = _norm_author(name)
        if n and n in text and n not in seen:
            seen.add(n)
            found.append(PHILOSOPHER_ALIASES.get(n) or PHILOSOPHER_ALIASES.get(name) or n)
    # 去重保序
    out = []
    for f in found:
        if f not in out:
            out.append(f)
    return out


# ═══════════════════════════════════════════════════════
# 3. PremiseVerifier —— 用户事实前提抽取与校正
# ═══════════════════════════════════════════════════════
# 可验证事实前提规则（Phase 1 手工精配, 只收"显著影响答案且必改"的常见错误;
# 每例: 主题词 + 错误数字 + 语境动词; 缺失其一即不触发——宁漏勿误）
PREMISE_RULES = [
    {
        "id": "oldman_84_days",
        "topic_keywords": ["老人与海", "圣地亚哥", "桑地亚哥", "老渔夫", "老人"],
        "number": {"wrong": "87", "right": "84", "unit": "天"},
        # Phase 4 扩充语境词: 覆盖"87天的执念"类表述（T3 回归题）, 不再只认"捕/鱼"
        # Phase S (S1): 补"困境"——"从87天的困境到最后…"类无渔获动词的抽象指称
        "context_words": ["捕", "钓", "没有捕到", "鱼", "执念", "出海", "一无所获", "空手", "没捕", "困境"],
        "exclude_words": [],
        # Phase S (S1): 87 天必须判断用户所指事件, 不做简单数字替换——
        #   小说开篇当前这次连续未捕到鱼 = 84 天; 老人回忆中过去那次 = 87 天。
        #   84 与 87 都可能正确, 语境词只判定"所指", 不再直接判定"对错"。
        "referent_current": ["开头", "开篇", "小说开头", "一开始", "刚开始", "现在", "目前",
                             "当前", "这次", "已经", "这轮"],
        "referent_historical": ["以前", "曾经", "有过", "曾", "早年", "上次", "过去", "之前",
                                "此前", "那时", "那段", "回忆", "记得", "想起", "年轻", "历史上"],
        # 歧义语境: 时间指向不明（"从…到…"叙事弧/困境/执念等抽象指称）
        "referent_ambiguous": [r"从.{0,8}87.{0,8}(到|开始)", "困境", "执念", "那件事", "那段日子"],
        "claim": "圣地亚哥在小说开篇连续87天没有捕到鱼",
        "claim_type": "textual_fact",
        "corrected_value": "84天",
        "evidence": [{"book": "老人与海", "chapter": "开篇",
                      "quote": "他已经连续八十四天没有捕到一条鱼了（第85天钓上大马林鱼）"}],
        "correction_note": "《老人与海》开篇写的是连续84天没有捕到鱼; 随后第85天圣地亚哥才钓到那条大马林鱼。",
    },
    {
        "id": "antichrist_1888",
        "topic_keywords": ["反基督", "反基督徒", "anti-christ", "敌基督"],
        "number": {"wrong": "1889", "right": "1888", "unit": "年"},
        "context_words": ["写", "创作", "完成", "著完", "写毕"],
        "exclude_words": ["出版", "刊发", "面世", "发表"],
        "claim": "尼采在1889年写《反基督》",
        "claim_type": "textual_fact",
        "corrected_value": "1888年写成（1889年出版）",
        "evidence": [{"book": "反基督", "chapter": "创作背景",
                      "quote": "《反基督》写于1888年, 1889年出版"}],
        "correction_note": "《反基督》写于1888年（1889年出版）——写与出版是两个时间点。",
    },
    {
        "id": "rebel_1951",
        "topic_keywords": ["《反抗者》"],
        "number": {"wrong": "1942", "right": "1951", "unit": "年"},
        "context_words": ["写", "创作", "完成", "著完", "写毕", "出版", "发表"],
        "exclude_words": [],
        "claim": "加缪在1942年写《反抗者》",
        "claim_type": "textual_fact",
        "corrected_value": "1951年（《西西弗斯神话》《局外人》才是1942年）",
        "evidence": [{"book": "反抗者", "chapter": "作品信息",
                      "quote": "《反抗者》出版于1951年"}],
        "correction_note": "《反抗者》写于1951年（1942年是《西西弗斯神话》《局外人》的年代）。",
    },
]

# 错误书名规则（用户以《》包裹的缩写书名 → 全名校正; 仅在《错名》成对出现时触发, 宁漏勿误）
BOOK_TITLE_RULES = [
    {
        "id": "book_sisyphus_full_title",
        "wrong": "西西弗斯", "right": "西西弗斯神话",
        "topic_keywords": ["加缪", "荒诞", "西西弗斯神话"],
        "claim": "加缪在《西西弗斯》中…",
        "claim_type": "textual_fact",
        "corrected_value": "《西西弗斯神话》（全名）",
        "evidence": [{"book": "西西弗斯神话", "chapter": "作品信息",
                      "quote": "加缪的哲学随笔全名为《西西弗斯神话》"}],
        "correction_note": "加缪这部随笔的全名是《西西弗斯神话》——《西西弗斯》是缩略说法。",
    },
    {
        "id": "book_zarathustra_full_title",
        "wrong": "查拉图斯特拉", "right": "查拉图斯特拉如是说",
        "topic_keywords": ["尼采", "查拉图斯特拉如是说"],
        "claim": "尼采在《查拉图斯特拉》中…",
        "claim_type": "textual_fact",
        "corrected_value": "《查拉图斯特拉如是说》（全名）",
        "evidence": [{"book": "查拉图斯特拉如是说", "chapter": "作品信息",
                      "quote": "尼采此书全名为《查拉图斯特拉如是说》"}],
        "correction_note": "尼采此书全名是《查拉图斯特拉如是说》——《查拉图斯特拉》是缩略说法。",
    },
]

# 错误概念归属规则（X 提出/主张/创造了 concept, 而 concept 实属 real_owner;
# 仅在"已知哲学家 ≠ 真实归属"且带归属动词时触发, 宁漏勿误）
CONCEPT_OWNER_RULES = [
    {
        "id": "concept_will_to_power",
        "concept": "权力意志", "real_owner": "尼采",
        "wrong_owners": ["叔本华", "康德", "黑格尔", "马克思", "弗洛伊德", "斯宾诺莎"],
        "context_words": ["提出", "认为", "主张", "的概念", "的学说", "创立", "发明", "属于"],
        "claim": "权力意志是叔本华提出的概念",
        "claim_type": "textual_fact",
        "corrected_value": "权力意志是尼采的核心概念",
        "evidence": [{"book": "查拉图斯特拉如是说", "chapter": "概念信息",
                      "quote": "权力意志（Wille zur Macht）是尼采思想的核心概念"}],
        "correction_note": "权力意志是尼采的概念（《权力意志》为其遗稿整理）——归属他人是常见误记。",
    },
    {
        "id": "concept_eternal_return",
        "concept": "永恒轮回", "real_owner": "尼采",
        # 赫拉克利特/斯多葛的循环说属可辩护的前史表述, 不触发（宁漏勿误）
        "wrong_owners": ["叔本华", "柏拉图", "黑格尔"],
        "context_words": ["提出", "认为", "主张", "的概念", "的学说", "创立", "发明", "属于", "最早"],
        "claim": "永恒轮回是叔本华提出的概念",
        "claim_type": "textual_fact",
        "corrected_value": "永恒轮回是尼采的核心思想（有其古希腊前史）",
        "evidence": [{"book": "快乐的科学", "chapter": "第341节",
                      "quote": "尼采在《快乐的科学》第341节提出永恒轮回的思想实验"}],
        "correction_note": "永恒轮回作为哲学命题由尼采在《快乐的科学》第341节明确提出（古希腊有轮回观念的先行形态）。",
    },
    {
        "id": "concept_ubermensch",
        "concept": "超人", "real_owner": "尼采",
        "wrong_owners": ["叔本华", "康德", "黑格尔"],
        "context_words": ["提出", "认为", "主张", "的概念", "的学说", "创立", "发明", "属于"],
        "claim": "超人是叔本华提出的概念",
        "claim_type": "textual_fact",
        "corrected_value": "超人是尼采的概念",
        "evidence": [{"book": "查拉图斯特拉如是说", "chapter": "前言",
                      "quote": "查拉图斯特拉宣称：人是应当被超越的——超人"}],
        "correction_note": "超人是尼采在《查拉图斯特拉如是说》中提出的概念。",
    },
    {
        "id": "concept_absolute_spirit",
        "concept": "绝对精神", "real_owner": "黑格尔",
        "wrong_owners": ["康德", "谢林", "费希特", "柏拉图", "亚里士多德", "斯宾诺莎"],
        "context_words": ["提出", "认为", "主张", "的概念", "的学说", "创立", "发明", "属于"],
        "claim": "绝对精神是康德提出的概念",
        "claim_type": "textual_fact",
        "corrected_value": "绝对精神是黑格尔的概念",
        "evidence": [{"book": "精神现象学", "chapter": "序言",
                      "quote": "绝对精神是黑格尔《精神现象学》的核心概念"}],
        "correction_note": "绝对精神（der absolute Geist）是黑格尔《精神现象学》的核心概念。",
    },
    {
        "id": "concept_being_toward_death",
        "concept": "向死而生", "real_owner": "海德格尔",
        "wrong_owners": ["尼采", "萨特", "雅斯贝尔斯", "克尔凯郭尔"],
        "context_words": ["提出", "认为", "主张", "的概念", "的学说", "创立", "发明", "属于"],
        "claim": "向死而生是尼采提出的概念",
        "claim_type": "textual_fact",
        "corrected_value": "向死而生是海德格尔的概念（《存在与时间》）",
        "evidence": [{"book": "存在与时间", "chapter": "第2篇",
                      "quote": "海德格尔在《存在与时间》中以向死而生（Sein zum Tode）刻画此在"}],
        "correction_note": "向死而生（Sein zum Tode）是海德格尔《存在与时间》中的概念。",
    },
    {
        "id": "concept_dasein",
        "concept": "此在", "real_owner": "海德格尔",
        "wrong_owners": ["萨特", "尼采", "胡塞尔", "雅斯贝尔斯"],
        "context_words": ["提出", "认为", "主张", "的概念", "的学说", "创立", "发明", "属于"],
        "claim": "此在是萨特提出的概念",
        "claim_type": "textual_fact",
        "corrected_value": "此在是海德格尔的概念（《存在与时间》）",
        "evidence": [{"book": "存在与时间", "chapter": "导论",
                      "quote": "海德格尔以 Dasein（此在）称呼人之存在方式"}],
        "correction_note": "此在（Dasein）是海德格尔《存在与时间》中的基础概念。",
    },
    {
        "id": "concept_hell_is_others",
        "concept": "他人即地狱", "real_owner": "萨特",
        "wrong_owners": ["加缪", "海德格尔", "尼采", "波伏娃"],
        "context_words": ["提出", "认为", "主张", "的名言", "的话", "说过", "属于", "说"],
        "claim": "他人即地狱是加缪提出的说法",
        "claim_type": "textual_fact",
        "corrected_value": "他人即地狱是萨特《禁闭》中的台词",
        "evidence": [{"book": "禁闭", "chapter": "剧中",
                      "quote": "《禁闭》结尾台词：他人即地狱"}],
        "correction_note": "“他人即地狱”出自萨特的剧作《禁闭》，不是加缪。",
    },
    {
        "id": "concept_theory_of_ideas",
        "concept": "理念论", "real_owner": "柏拉图",
        "wrong_owners": ["亚里士多德", "康德", "苏格拉底", "黑格尔"],
        "context_words": ["提出", "认为", "主张", "的概念", "的学说", "创立", "发明", "属于"],
        "claim": "理念论是亚里士多德提出的学说",
        "claim_type": "textual_fact",
        "corrected_value": "理念论（理式论）是柏拉图的核心学说",
        "evidence": [{"book": "理想国", "chapter": "卷六至卷七",
                      "quote": "柏拉图的理念论（理式论）在《理想国》中系统展开"}],
        "correction_note": "理念论（理式论）是柏拉图的核心学说，亚里士多德恰是它的批评者。",
    },
]

# 手工精配的"作品→作者"表（books.json 之外的经典异名/译名, 优先级最高）
CURATED_WORK_AUTHORS = {
    "存在与时间": ["马丁·海德格尔", "海德格尔"],
    "存在与虚无": ["让-保罗·萨特", "萨特"],
    "查拉图斯特拉如是说": ["弗里德里希·尼采", "尼采"],
    "快乐的科学": ["弗里德里希·尼采", "尼采"],
    "反基督": ["弗里德里希·尼采", "尼采"],
    "西西弗斯神话": ["阿尔贝·加缪", "加缪"],
    "反抗者": ["阿尔贝·加缪", "加缪"],
    "局外人": ["阿尔贝·加缪", "加缪"],
    "鼠疫": ["阿尔贝·加缪", "加缪"],
    "理想国": ["柏拉图"],
    "纯粹理性批判": ["伊曼努尔·康德", "康德"],
    "实践理性批判": ["伊曼努尔·康德", "康德"],
    "判断力批判": ["伊曼努尔·康德", "康德"],
    "作为意志和表象的世界": ["亚瑟·叔本华", "叔本华"],
    "哲学研究": ["路德维希·维特根斯坦", "维特根斯坦"],
    "逻辑哲学论": ["路德维希·维特根斯坦", "维特根斯坦"],
    "存在主义是一种人道主义": ["让-保罗·萨特", "萨特"],
    "共产党宣言": ["卡尔·马克思", "马克思"],
    "资本论": ["卡尔·马克思", "马克思"],
    "尼各马可伦理学": ["亚里士多德"],
    "形而上学": ["亚里士多德"],
    "忏悔录": ["奥古斯丁"],
    "上帝之城": ["奥古斯丁"],
    "人是机器": ["拉美特利"],
}

# 归属误判语境动词（"《作品》里作者X 认为/写了…" → 判归属; 无动词不判）
_ATTRIB_VERBS = "认为|提出|写道|写到|说|主张|论证|指出|论述|表示|谈论|讨论|说过"


class PremiseVerifier:
    """用户事实前提核对（非阻塞: 只校正, 不拒绝; 只查会显著影响答案的可验证事实）"""

    def __init__(self, rules=None, work_authors=None):
        self.rules = rules if rules is not None else PREMISE_RULES
        self.work_authors = work_authors if work_authors is not None else None   # 懒加载覆盖

    # ── 作品→作者全表（curated + books.json, 惰性合并）──
    def _work_author_map(self):
        if self.work_authors is not None:
            return self.work_authors
        m = dict(CURATED_WORK_AUTHORS)
        for title, info in _load_books().items():
            if title not in m and info.get("author"):
                m[title] = [info["author"], info.get("author_short") or info["author"]]
        self.work_authors = m
        return m

    def check(self, message):
        """返回前提核验结果列表（[]=无事实矛盾）

        每条: {status, claim, claim_type, verification_required, corrected_value,
               evidence, evidence_ids, nonblocking, rule_id, correction_note}
        """
        msg = message or ""
        out = []
        if not msg.strip():
            return out

        # ── 数字/日期前提规则 ──
        numbers = set(re.findall(r"(\d+)", msg))
        for rule in self.rules:
            num = rule["number"]
            if num["wrong"] not in numbers:
                continue
            if not any(k in msg for k in rule["topic_keywords"]):
                continue
            if not any(c in msg for c in rule["context_words"]):
                continue
            if any(e in msg for e in rule.get("exclude_words", [])):
                continue
            # 触发: 错误数字 + 主题词 + 语境动词 同现（数字须贴近主题词, 防"1889年"误伤无关句）
            if not self._near_num(msg, rule):
                continue
            # Phase S (S1): 语义判定"87天"所指事件, 而非简单数字替换。
            #   84 与 87 都可能正确: 开篇当前这次=84天, 过去那次=87天。
            #   historical → 87 属实, 只确认不纠正（防 LLM 反向误纠）;
            #   ambiguous → 只辨析, 不机械纠错。
            if rule.get("referent_current") or rule.get("referent_historical"):
                mode = self._classify_referent(msg, rule)
                if mode == "historical":
                    c = self._build_contradiction(rule, num, msg)
                    c["status"] = "confirmed"
                    c["referent_mode"] = "historical"
                    c["claim"] = "老人过去曾有87天没捕到鱼的经历"
                    c["corrected_value"] = "87天（历史经历, 属实）"
                    c["correction_note"] = (
                        "《老人与海》中男孩确实提到老人曾连续87天没有捕到鱼（这是过去那次经历）；"
                        "开篇当前这次才是连续84天。用户说的'87天'若指过去那次则无需纠正。")
                    out.append(c)
                    continue
                c = self._build_contradiction(rule, num, msg)
                c["referent_mode"] = mode
                if mode == "ambiguous":
                    c["claim"] = "老人'87天'未捕到鱼（未指明是开篇当前这次还是过去那次经历）"
                    c["corrected_value"] = "84天（开篇当前这次）/ 87天（他此前的经历）"
                    c["correction_note"] = (
                        "《老人与海》需要区分两个数字：开篇的当前这次是连续84天没有捕到鱼；"
                        "老人回忆中的过去那次才是87天。你提到的'87天'若指开篇这次则应是84天——"
                        "请按你实际所指区分这两段经历，不要混淆。")
                out.append(c)
                continue
            out.append(self._build_contradiction(rule, num, msg))

        # ── 作品归属规则（数据驱动: 用户把某作品误归于别的哲学家）──
        attr = self._check_attribution(msg)
        out.extend(attr)
        # ── 错误书名规则（《西西弗斯》→《西西弗斯神话》; Phase 4 新增规则类）──
        titles = self._check_book_titles(msg)
        out.extend(titles)
        # ── 错误概念归属规则（权力意志→尼采 等; Phase 4 新增规则类）──
        concepts = self._check_concept_owners(msg)
        out.extend(concepts)
        return out

    def _check_book_titles(self, msg):
        """错误书名: 《缩写名》成对出现 + 主题词邻近（宁漏勿误——只认《》包裹的书名形态）"""
        out = []
        for rule in BOOK_TITLE_RULES:
            marker = f"《{rule['wrong']}》"
            if marker not in msg:
                continue
            if not any(k in msg for k in rule["topic_keywords"]):
                continue
            if not self._near_str(msg, marker, rule["topic_keywords"]):
                continue
            out.append(self._build_str_contradiction(rule, marker, msg, f"title:{rule['id']}"))
        return out

    def _check_concept_owners(self, msg):
        """错误概念归属: concept 与 已知哲学家（≠ 真实归属）邻近 + 归属动词同现"""
        out = []
        for rule in CONCEPT_OWNER_RULES:
            concept = rule["concept"]
            if concept not in msg:
                continue
            if not any(c in msg for c in rule["context_words"]):
                continue
            i = msg.find(concept)
            for owner in rule["wrong_owners"]:
                j = msg.find(owner)
                if j >= 0 and abs(i - j) <= 40:
                    out.append(self._build_str_contradiction(
                        rule, f"{owner}·{concept}", msg, f"concept:{rule['id']}"))
                    break
        return out

    @staticmethod
    def _near_str(msg, marker, keywords):
        """标记（《错名》/概念）须与任一主题词邻近（±40 字符窗口）——防全句偶然同现"""
        i = msg.find(marker)
        if i < 0:
            return False
        for kw in keywords:
            j = msg.find(kw)
            if j >= 0 and abs(i - j) <= 40:
                return True
        return False

    def _build_str_contradiction(self, rule, matched, msg, rule_id):
        """字符串规则（书名/概念）的裁决——与数字规则同构（build_guard_injections 无需改动）"""
        return {
            "status": "contradicted",
            "claim": rule["claim"],
            "claim_type": rule["claim_type"],
            "verification_required": True,
            "corrected_value": rule["corrected_value"],
            "evidence": rule["evidence"],
            "evidence_ids": [f"{rule_id}:evidence:{i}" for i in range(len(rule["evidence"]))],
            "nonblocking": True,
            "rule_id": rule_id,
            "correction_note": rule["correction_note"],
            "matched": matched,
        }

    def _near_num(self, msg, rule):
        """错误数字须出现在任一主题词附近（±30 字符窗口内）——防全句偶然同现"""
        for kw in rule["topic_keywords"]:
            i = msg.find(kw)
            while i >= 0:
                window = msg[max(0, i - 30): i + len(kw) + 30]
                if rule["number"]["wrong"] in window:
                    return True
                i = msg.find(kw, i + 1)
        return False

    @staticmethod
    def _classify_referent(msg, rule):
        """S1: 判定错误数字所指事件（供 84/87 类双事实规则使用）

        current     指开篇当前这次（→ 数字错误, 校正为 84 天）
        historical  指过去那次经历（→ 87 天本身正确, 不得纠正）
        ambiguous   时间指向不明（→ 只辨析两个事实, 不机械纠错）

        判据: 数字 ±20 字符窗口内的语境词; 历史语境词单独出现 → historical;
        当前语境词出现（无论是否混有历史词）→ current（当前语境更具体, 优先）;
        仅"从…到…/困境/执念"等抽象指称 → ambiguous; 裸陈述默认 current
        （最常见误记: 把开篇 84 天记成 87 天）。
        """
        num = rule["number"]["wrong"]
        windows, start = [], 0
        while True:
            i = msg.find(num, start)
            if i < 0:
                break
            windows.append(msg[max(0, i - 20): i + len(num) + 20])
            start = i + len(num)
        if not windows:
            return "ambiguous"
        hist = any(any(c in w for c in rule.get("referent_historical", [])) for w in windows)
        if hist and not any(any(c in w for c in rule.get("referent_current", [])) for w in windows):
            return "historical"
        if any(any(c in w for c in rule.get("referent_current", [])) for w in windows):
            return "current"
        for w in windows:
            for pat in rule.get("referent_ambiguous", []):
                if pat.startswith("从") and re.search(pat, w):
                    return "ambiguous"
                if pat in w:
                    return "ambiguous"
        return "current"

    def _build_contradiction(self, rule, num, msg):
        return {
            "status": "contradicted",
            "claim": rule["claim"],
            "claim_type": rule["claim_type"],
            "verification_required": True,
            "corrected_value": rule["corrected_value"],
            "evidence": rule["evidence"],
            "evidence_ids": [f"{rule['id']}:evidence:{i}" for i in range(len(rule["evidence"]))],
            "nonblocking": True,
            "rule_id": rule["id"],
            "correction_note": rule["correction_note"],
            "matched": num["wrong"],
        }

    def _check_attribution(self, msg):
        """作品作者归属检查: 'X写的《Y》'、'《Y》里X认为/写到/论述' 且 X≠真实作者 → 校正"""
        out = []
        authors_known = set()
        authors_known |= set(PHILOSOPHER_ALIASES.keys())
        authors_known |= set(_load_philosophers())
        wam = self._work_author_map()
        for work, real_authors in wam.items():
            if work not in msg:
                continue
            real_short = {_norm_author(a) for a in real_authors}
            # 模式1: 作者名 + 的 + 《作品》 → "尼采的《存在与时间》"
            for m in re.finditer(rf"([\w·\-—\u4e00-\u9fff]{{1,12}})的《{re.escape(work)}》", msg):
                claimed = _norm_author(m.group(1))
                if claimed in real_short:
                    continue
                if claimed in authors_known or self._is_common_name(claimed, msg):
                    out.append(self._attr_contradiction(work, claimed, real_authors, msg, "owner"))
                    break
            # 模式2: 《作品》里/中/内 作者名 + 断言动词 → "《存在与时间》里尼采认为"
            for m in re.finditer(rf"《{re.escape(work)}》(里|中|内|里面|当中)([\w·\u4e00-\u9fff]{{1,12}}?)(?:的|(?:{_ATTRIB_VERBS}))", msg):
                claimed = _norm_author(m.group(2))
                if claimed in real_short:
                    continue
                if claimed in authors_known:
                    out.append(self._attr_contradiction(work, claimed, real_authors, msg, "intext"))
                    break
        return out

    @staticmethod
    def _is_common_name(s, msg):
        """未入名单的疑似人名兜底: 常见姓氏 + 出现在'的《作品》'前, 仍可判（如'张'）"""
        return len(s) >= 2 and s[-1] in ("尔", "斯", "尼", "尔", "克", "夫", "德") and (s in msg)

    def _attr_contradiction(self, work, claimed, real_authors, msg, pattern):
        real = real_authors[0]
        return {
            "status": "contradicted",
            "claim": f"《{work}》的作者是{claimed}",
            "claim_type": "textual_fact",
            "verification_required": True,
            "corrected_value": f"《{work}》的作者是{real}",
            "evidence": [{"book": work, "chapter": "作品信息", "quote": f"《{work}》由{real}著"}],
            "evidence_ids": [f"attr:{work}:evidence:0"],
            "nonblocking": True,
            "rule_id": f"attribution:{work}",
            "correction_note": f"《{work}》的作者是{real}而非{claimed}——先校正这一归属, 再继续回答。",
            "matched": f"{claimed}的《{work}》",
        }


# ═══════════════════════════════════════════════════════
# 4. EpistemicClaimClassifier —— Claim 知识论分级
# ═══════════════════════════════════════════════════════
# 具体 → 一般 顺序匹配（首个命中即定级; 全部未中 → UNKNOWN）
_CLAIM_CUES = [
    ("DIRECT_QUOTE", r"原文写道|原文说|书上原话|引文\s*[\"“]|直接引用|原文是|今引|原话是"),
    ("SOURCE_FACT", r"文本明确写道|明确记载|书中明确|文本明确|原文明确|史料记载|史实是"),
    ("CROSS_TEXT_INTERPRETATION", r"若采用.{0,12}的框架|以.{0,10}的(视角|框架|立场).{0,8}(读作|来解|看)|用.{0,10}的框架"),
    ("SCHOLARLY_INTERPRETATION", r"某种研究解释认为|有研究(表明|认为|指出)|学界(普遍|一般认为|认为)|有学者(认为|指出)|学术研究认为"),
    ("AUTHOR_COUNTERFACTUAL", r"会(怎么|如何|怎样)(看|想|评价|说)|如果.{0,10}(活到|活在|来到|穿越|见到).{0,8}(今天|今日|现代|当世|当代|现在)|活到今天|想必会|一定会认为|绝不会认为"),
    ("USER_PREMISE", r"你(提出|提到|说|认为|假设|的前提|说的前提)|正如你(所说|认为|提到)|你问的是"),
    ("SPECULATION", r"一种可能的解释是|或许是|也许|可能|大概|猜测|推测|不妨设想"),
    ("UNKNOWN", r"无法(确定|判断|知道)|现有材料(不足|无法)|尚无定论|没有证据表明|不清楚|无从判断"),
]

# 文本意义类解读词（"意味着/象征/隐喻/转变" 等 → 解释性推断, 不是文本事实）
_INTERPRETIVE_RE = re.compile(r"意味着|象征着|隐喻|象征|暗示|反映出|体现了|代表了|说明了|表明|表达了|完成了(?=.*转变)|转变|寓意|读作|解读为|可以理解为")
# 强模态（"一定/必然/毫无疑问" → 即便涉及文本, 也降级为解释/推测, 禁止 SOURCE_FACT）
_STRONG_MODAL_IN_TEXT = re.compile(r"一定|必然|毫无疑问|绝对|无疑|显然是")


class EpistemicClaimClassifier:
    """Claim 分级器（Phase 1 规则版; confidence 恒 None, Phase 2 再补完整 confidence engine）

    classify(text) → {"claim", "epistemic_type", "confidence": None, "evidence_ids": []}
    """

    def classify(self, text, extra=False):
        t = (text or "").strip()
        ctype = self._cue_match(t)
        strong_modal = bool(_STRONG_MODAL_IN_TEXT.search(t)) and bool(_INTERPRETIVE_RE.search(t))
        # 强模态的文本解读 → 解释性判断, 而非文本事实（"一定完成了转变" ≠ 原文所说）
        if ctype in ("TEXTUAL_INFERENCE",) and strong_modal:
            ctype = "TEXTUAL_INFERENCE"
        evidence_ids = self._evidence_ids(t)
        out = {"claim": t, "epistemic_type": ctype, "confidence": None, "evidence_ids": evidence_ids}
        if extra:
            out["strong_modal"] = strong_modal
        return out

    def _cue_match(self, t):
        if not t:
            return "UNKNOWN"
        for ctype, pat in _CLAIM_CUES:
            if re.search(pat, t):
                return ctype
        # 文本意义类解读（无引文/出处标记, 但有"意味着/隐喻/象征…"）→ 解释性推断
        if _INTERPRETIVE_RE.search(t):
            return "TEXTUAL_INFERENCE"
        return "UNKNOWN"

    def _evidence_ids(self, t):
        """Phase 1: 从文本提取可核验出处锚点（《书名》/章节引号块）"""
        ids = []
        for m in re.finditer(r"《([^》]{1,40})》", t):
            ids.append(f"book:{_strip_marks(m.group(1))}")
        for m in re.finditer(r"[“\"]([^”\"]{4,80})[”\"]", t):
            ids.append(f"quote:{m.group(1)[:20]}")
        return ids[:8]

    @staticmethod
    def language_bound(ctype):
        """类型 → 表达强度模板（语言约束的落地形式）"""
        return EPISTEMIC_LANGUAGE.get(ctype, EPISTEMIC_LANGUAGE["UNKNOWN"])

    def split_sentences(self, text):
        """按句末切分（供遍历用户消息中的每个断言）"""
        return [s for s in re.split(r"[。！？；!?;\n]", text or "") if s.strip()]


# ═══════════════════════════════════════════════════════
# 5. CounterfactualAuthorGuard —— 作者反事实识别与历史/反事实分离
# ═══════════════════════════════════════════════════════
# 作者生平/思想覆盖的**当代对象**（无直接史料 → 一律按反事实处理）
_CONTEMPORARY_OBJECT_RE = re.compile(r"\b(AI|人工智能|互联网|智能手机|短视频|元宇宙|区块链|比特币|推特|微博|抖音|微信|电脑|手机|社交媒体|VR|元宇宙)\b|AI|人工智能|互联网|智能手机|短视频|元宇宙|区块链|大语言模型")

# 反事实提问句式（"会怎么看/会如何评价/如果活到今天"等——不具备历史答案的时态）
_CQ_QUESTION = re.compile(r"会\s*(怎么|如何|怎样)(看待|看|想|评价|说)|会不会(认为|觉得)|会\s*怎么\s*说|怎么\s*看|怎么\s*说来|如何(看待|评价)|怎么看待")
_CQ_LIVENESS = re.compile(r"如果(?:他|她)?.{0,14}(活到|活在|来到|穿越到|身处|出生在|生在|生活在|看到|看见|接触|知道).{0,10}(今天|今日|现代|当世|当代|现在|信息时代|这个时代)|活到今天|若(是)?(今天|活在今天)|穿越到(今天|现代)")
_CQ_MODAL = re.compile(r"一定|必然|肯定会|绝不会|必定|想必|无疑会|显然会|一定会")

# 已载入史料的主题（有直接史料 → 可按 TEXTUAL_INFERENCE / SOURCE_FACT 正常回答）
DOCUMENTED_TOPICS = {
    "尼采": ["瓦格纳", "苏格拉底", "基督教", "耶稣", "上帝", "叔本华", "康德", "虚无主义",
             "道德", "艺术", "悲剧", "查拉图斯特拉", "权力意志", "永恒轮回", "超人", "启蒙",
             "科学", "女人", "犹太人", "历史", "国家", "格言"],
    "加缪": ["荒诞", "自杀", "西西弗斯", "反抗", "正义", "死刑", "阿尔及利亚", "孤独", "鼠疫",
             "共产主义", "暴力"],
    "叔本华": ["意志", "表象", "音乐", "艺术", "悲观主义", "痛苦", "生存", "佛教", "康德"],
    "萨特": ["自由", "存在主义", "他者", "虚无", "二战", "责任", "意识", "肮脏说", "共产主义"],
    "黑格尔": ["辩证法", "绝对精神", "历史", "自我意识", "国家", "精神", "宗教", "艺术"],
    "康德": ["理性", "道德", "先验", "自由", "审美", "义务", "物自体", "判断力", "国际联盟"],
    "马克思": ["资本主义", "异化", "劳动", "共产主义", "阶级斗争", "历史唯物主义", "费尔巴哈"],
    "维特根斯坦": ["语言", "逻辑", "意义", "沉默", "私人语言", "逻辑哲学论", "数学", "日常语言"],
    "海德格尔": ["存在", "死亡", "沉沦", "此在", "技术", "语言", "梵高", "荷尔德林", "纳粹"],
    "柏拉图": ["理想国", "洞穴", "理念", "灵魂", "苏格拉底", "正义", "诗", "回忆"],
    "亚里士多德": ["逻辑", "四因", "伦理学", "中庸", "幸福", "形而上学", "实体", "悲剧", "城邦"],
    "奥古斯丁": ["时间", "自我", "上帝之城", "忏悔", "自由意志", "三位一体"],
    "休谟": ["经验", "因果", "自我", "道德", "宗教", "怀疑"],
    "庄子": ["逍遥", "齐物", "生死", "自然", "蝴蝶梦", "无用"],
    "老子": ["道", "无为", "自然", "阴阳", "道德经"],
    "孔子": ["仁", "礼", "君子", "孝", "中庸", "学而"],
    "释迦牟尼": ["苦", "无常", "涅槃", "八正道", "缘起", "空"],
}


class CounterfactualAuthorGuard:
    """识别'作者会怎么看'类问题; 有直接史料 → historical（正常回答）;
    无 → counterfactual（注入反事实边界, 禁止'X 一定/绝不会'断言）"""

    def check(self, message):
        msg = (message or "").strip()
        result = {
            "mode": "historical", "authors": [], "author": None, "object": "",
            "direct_evidence": [], "requires_guard": False,
            "boundary_text": "", "claim": msg,
            "epistemic_type": "TEXTUAL_INFERENCE",
            "cues": [],
        }
        if not msg:
            return result
        authors = _match_philosopher(msg)
        if not authors:
            return result
        author = authors[0]
        result["authors"] = authors
        result["author"] = author
        # ── 反事实信号采集（question/liveness/modal 仅作观测 cue）──
        cues = []
        if _CQ_QUESTION.search(msg):
            cues.append("question")
        if _CQ_LIVENESS.search(msg):
            cues.append("liveness")
        if _CQ_MODAL.search(msg):
            cues.append("modal")
        contemporary = bool(_CONTEMPORARY_OBJECT_RE.search(msg))
        if contemporary:
            cues.append("contemporary_object")
        result["cues"] = cues

        # ── 直接史料判定 ──
        evidence = []
        wam = self._work_author_map()
        real_short = set()
        for work, real_authors in wam.items():
            if f"《{work}》" in msg and any(_norm_author(a) == author for a in real_authors):
                real_short.add(work)
        if real_short:
            evidence.append({"kind": "own_work", "work": sorted(real_short)})
        # 作者自己的思想/哲学/学说 → 本身即有史料
        if re.search(rf"{author}的(哲学|思想|学说|著作|观点|立场)", msg):
            evidence.append({"kind": "own_thought"})
        # 已载入史料的主题
        topics = DOCUMENTED_TOPICS.get(author, [])
        hit_topics = [t for t in topics if t in msg]
        if hit_topics:
            evidence.append({"kind": "documented_topic", "topics": hit_topics})
        # 当代对象（作者生前不存在的对象 → 即便句式属"看"也按反事实）
        if contemporary:
            evidence = [e for e in evidence if e["kind"] != "documented_topic"]

        result["direct_evidence"] = evidence

        # ── Patch 1.1 (P4): 反事实边界非侵入收紧 ──
        # 仅当问题真正"无历史文本事实可直接回答"时才触发:
        #   ① 哲学家面对其死后对象（当代对象: AI/算法/互联网…）
        #   ② 未实际发生的会面/事件（活到今天/穿越/如果看到今天）
        #   ③ "X 会怎么评价 Y"且 Y 既非已载史料话题、也非另一位已知哲学家
        #      （另一位哲学家在场 → 是思想史关系问题, 有文本事实可答）
        # 普通 "A 如何回应 B / A 与 B 理论差异 / B 受到 A 什么影响 / A 是否反驳 B"
        # → 一律 historical, guard 完全静默（不注入、不尾补）。
        # 单独的强模态词（引文/概念表述中的"必然性/一定"）绝不构成触发——
        # F06 误触发根因: "经验不能给出必然性" 命中 _CQ_MODAL。
        multi_author = len(authors) >= 2
        triggered = (
            "liveness" in cues
            or (contemporary and cues)
            or ("question" in cues and not evidence and not multi_author)
        )
        if triggered:
            result["mode"] = "counterfactual"
            result["requires_guard"] = True
            result["epistemic_type"] = "AUTHOR_COUNTERFACTUAL"
            result["boundary_text"] = (
                f"没有证据表明{author}本人评论过这一对象；以下是依据其已知思想框架进行的反事实推演。")
            result["boundary_text_en"] = (
                f"There is no evidence that {author} personally commented on this object; the following is a "
                f"counterfactual extrapolation based on his known intellectual framework.")
        else:
            result["mode"] = "historical"
            result["epistemic_type"] = "TEXTUAL_INFERENCE"
        return result

    def _work_author_map(self):
        return PremiseVerifier()._work_author_map()

    @staticmethod
    def boundary_present(answer, author):
        """应答后校验: 答案是否已含反事实边界（'没有证据表明' + 作者名）"""
        if not answer:
            return False
        return "没有证据表明" in answer and author in answer


# ═══════════════════════════════════════════════════════
# 6. 编排：run_epistemic_guards / build_guard_injections / scan_answer / 日志
# ═══════════════════════════════════════════════════════
def run_epistemic_guards(message, agent="general", language="zh"):
    """汇总三个组件的裁决（纯计算, 不调 LLM）

    返回:
      premise_checks: PremiseVerifier.check(...)
      counterfactual: CounterfactualAuthorGuard.check(...)
      claim_annotations: 用户消息中的断言标注（启用 EpistemicClaimClassifier 的证据）
      injections: 应注入到消息列表的系统提示（字符串列表）
    """
    checks = PremiseVerifier().check(message)
    counterfactual = CounterfactualAuthorGuard().check(message)
    classifier = EpistemicClaimClassifier()

    annotations = []
    for sent in classifier.split_sentences(message):
        c = classifier.classify(sent, extra=True)
        if c["epistemic_type"] in ("USER_PREMISE", "TEXTUAL_INFERENCE") or c.get("strong_modal"):
            if sent.strip():
                annotations.append(c)

    injections = build_guard_injections(checks, counterfactual, annotations, language)
    verdict = {
        "premise_checks": checks,
        "counterfactual": counterfactual,
        "claim_annotations": annotations,
        "injections": injections,
    }
    _log_record({"phase": "pre", "agent": agent, "language": language,
                 "message": (message or "")[:500],
                 "premise_checks": [{"id": c.get("rule_id"), "status": c.get("status"),
                                     "corrected_value": c.get("corrected_value")} for c in checks],
                 "counterfactual": {k: counterfactual.get(k) for k in
                                    ("mode", "author", "requires_guard", "direct_evidence", "cues")},
                 "claim_types": [a["epistemic_type"] for a in annotations],
                 "injections": len(injections)})
    return verdict


def build_guard_injections(checks, counterfactual, annotations, language="zh"):
    """由裁决生成系统提示注入（每句为一条 SystemMessage; 任何一类失败都不影响他类）"""
    inj = []
    # ── 1. 前提校正（非阻塞: 先简短校正, 再回答用户真正的问题）──
    for c in checks:
        if c.get("status") == "confirmed":
            # S1 历史类: 87 天属实（过去那次经历）——只确认, 不纠正（防 LLM 反向误纠）
            if language == "en":
                inj.append(
                    f"[System premise check] The user's '87 days' refers to the old man's PAST streak, "
                    f"which is true in the novel (the boy reminds him he once went 87 days without a fish); "
                    f"the opening streak of the current trip is 84 days. Do NOT correct this number — "
                    f"you may briefly confirm the distinction.")
            else:
                inj.append(
                    f"【前提确认（系统）】用户提到的'87天'指老人过去的经历——小说中男孩确实提到"
                    f"老人曾连续87天没有捕到鱼（开篇当前这次才是连续84天）。这一数字属实，不要纠正它；"
                    f"如需区分，可顺带点明当前84天与历史87天两段经历。"
                    f"正确表述: {c.get('correction_note') or ''}")
            continue
        if c.get("status") == "contradicted":
            evidence = ""
            for e in c.get("evidence", [])[:2]:
                quote = e.get("quote") or ""
                book = e.get("book") or ""
                evidence += f"（{book}: {quote}）" if quote else f"（{book}）"
            if c.get("referent_mode") == "ambiguous":
                # S1 歧义类: 84/87 都可能正确——只辨析两个事实, 不机械纠错
                if language == "en":
                    inj.append(
                        f"[System premise check] The user's premise involves '87 days' ambiguously: in "
                        f"The Old Man and the Sea the current opening streak is 84 days without a fish, "
                        f"while the old man's remembered past streak was 87 days. Both numbers can be "
                        f"correct depending on which event is meant. Open with one or two sentences "
                        f"distinguishing the two, then continue answering the real question — do NOT "
                        f"mechanically assert 'it is 84' or 'it is 87'.")
                else:
                    inj.append(
                        f"【前提辨析（系统）】用户提到的'87天'存在歧义：《老人与海》里有两个数字需要区分——"
                        f"开篇的当前这次是连续84天没有捕到鱼，老人回忆中的过去那次才是87天。"
                        f"回答第一句先点明这一区分（一两句话即可），然后继续回答用户真正的问题；"
                        f"不要武断断言'就是84天'或'就是87天'，也不要反复纠缠。"
                        f"正确表述: {c.get('correction_note') or ''}")
                continue
            if language == "en":
                inj.append(
                    f"[System premise check] The user's question contains a factual premise error: "
                    f"{c['claim']} — actually {c['corrected_value']} (evidence: {evidence or 'corpus'}). "
                    "Correct it briefly in 1-2 sentences FIRST, then continue answering the user's real question. "
                    "Do not refuse the question because of this small error.")
            else:
                inj.append(
                    f"【前提校验（系统）】用户的问题中包含一个事实前提错误: {c['claim']}——实际是{c['corrected_value']}"
                    f"{evidence}. 回答的第一句必须先简短纠正这一错误（一两句话说明正确事实即可, 给出出处）；"
                    f"然后继续回答用户真正的问题，不要因此拒绝回答，也不要反复纠缠这个细节。" +
                    f"正确表述: {c.get('correction_note') or ''}")
    # ── 2. 反事实边界 ──
    if counterfactual.get("requires_guard"):
        author = counterfactual.get("author") or ""
        if language == "en":
            inj.append(
                f"[System counterfactual boundary] The user's question is a counterfactual hypothesis about "
                f"{author}. There is no evidence that {author} personally commented on this object. "
                f"Begin the answer with: 'There is no evidence that {author} personally commented on this object; "
                f"the following is a counterfactual extrapolation based on his known intellectual framework.' "
                f"Do NOT use assertions like '{author} would definitely / would never …'.")
        else:
            inj.append(
                f"【反事实边界（系统）】用户的问题是反事实假设（{author} 本人对这一对象并无直接史料）。"
                f"回答必须开头写入: '没有证据表明{author}本人评论过这一对象；以下是依据其已知思想框架进行的反事实推演。'"
                f"并禁止使用'{author}绝不会/一定会/肯定会……'这类零证据断言。")
    # ── 3. 用户强断言解释性声明（不得当文本事实）──
    for a in annotations:
        if a.get("strong_modal") and a.get("epistemic_type") in ("TEXTUAL_INFERENCE", "USER_PREMISE"):
            bound = EPISTEMIC_LANGUAGE["TEXTUAL_INFERENCE"]
            if language == "en":
                inj.append(
                    f"[System epistemic level] The user asserts: \"{a['claim'][:80]}\" — this is an interpretation "
                    f"of the text, not an explicit textual fact. When addressing it, distinguish 'the text clearly "
                    f"states…' from '{bound}'; do not treat this interpretation as a source fact.")
            else:
                inj.append(
                    f"【认知层级（系统）】用户断言『{a['claim'][:80]}』——这是对文本的解释性解读（相当于'"
                    f"{bound}'），并非原文明确写的文本事实。回答涉及这一判断时，请区分'文本明确写道'与'"
                    f"{bound}'，不要把这一解读当作原典事实引用。")
    return inj


def _correction_present_in_answer(check, answer):
    """校正落实: 回答包含 corrected_value 中任一数字或前缀（多数字值逐个匹配, 防"19511942"拼接误判）"""
    fixed = check.get("corrected_value") or ""
    ans = answer or ""
    nums = re.findall(r"\d+", fixed)
    if nums and any(n in ans for n in nums):
        return True
    return bool(fixed and fixed[:6] in ans)


def build_missing_correction_appends(verdict, answer, language="zh"):
    """Phase S (S2): Final Answer Composer 重新消费 epistemic findings

    answer_retract 只撤销已流出的 draft text, 不得撤销已经建立的 epistemic findings。
    前提校正义务若在最终可见正文中未落实（可能因为: 校正随 draft 被撤回 / LLM 忽略注入 /
    回答被工具轮打断）→ 返回应补发的校正文本; engine 以 token 事件尾补, 计入最终正文。
    """
    out = []
    for c in (verdict or {}).get("premise_checks") or []:
        if c.get("status") != "contradicted":
            continue
        if _correction_present_in_answer(c, answer or ""):
            continue
        note = c.get("correction_note") or f"实际是{c.get('corrected_value')}"
        if language == "en":
            out.append(f"(Note: correcting a premise in your question — {note})")
        else:
            out.append(f"（补充：先纠正一个前提——{note}）")
    return out


def scan_answer(verdict, answer, language="zh"):
    """应答后校验: 是否落实校正/边界（只记录, 返回补正文本——engine 决定是否补发）"""
    result = {"premise_checks": [], "counterfactual_boundary": None, "boundary_applied": False}
    checks = verdict.get("premise_checks") or []
    ans = answer or ""
    for c in checks:
        # S1: 双值 corrected_value（"84天（当前）/ 87天（历史）"）按逐数字匹配落实判定
        present = _correction_present_in_answer(c, ans)
        result["premise_checks"].append({"rule_id": c.get("rule_id"), "correction_present": present})
    cv = verdict.get("counterfactual") or {}
    if cv.get("requires_guard"):
        author = cv.get("author") or ""
        if CounterfactualAuthorGuard.boundary_present(ans, author):
            result["counterfactual_boundary"] = "present"
        else:
            result["counterfactual_boundary"] = "missing"
            result["boundary_applied"] = True
    _log_record({"phase": "post", "author_scan": result})
    return result


# ── 运行时记录（backend/data/ 已 gitignore, 纯观察/审计用; 失败静默）──
_log_lock = threading.Lock()


def _log_record(rec):
    try:
        rec = dict(rec)
        rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with _log_lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
