# -*- coding: utf-8 -*-
"""Interpretation Engine（Phase 2）——解释挑战者 + 确定性校准

解决第二个核心问题: Agent 太擅长"证明一个漂亮观点", 不够擅长"检验这个观点"。

组件（结构级规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  InterpretationChallenger    解释型问题识别（只对 4 类启用）与多候选解读强制:
                              literary_interpretation / philosophical_interpretation /
                              cross_author_comparison / ambiguous_historical_interpretation
                              区分 supporting_evidence / challenging_evidence;
                              至少一次"什么材料会削弱我的主要解释"的反证尝试; 无反证允许 [] , 不得伪造
  ConfidenceCalibrator        解释置信度评分（内部, 默认不展示数字）+ 四档语言校准
  DepthPenalty                解释链深度惩罚: 每增加一次跨体系跳转, confidence 只降不升
                              （防"海明威→加缪→庄子→佛教→斯多葛"后断言"本质完全一样"）

Phase 2 边界（见任务书）:
  - confidence 数字仅内部记录/日志, 默认不展示（补正文本为措辞级, 不含数字）
  - 不改 Graph / Memory / Persona Snapshot / 矢量库 / 工具注册表 / 流式协议
  - 以"前置系统消息注入 + 应答后校验补正（token 事件）"的结构生效, 失败绝不影响主流程

用法（engine_langgraph.stream_agent 内, 与 epistemic_guard 同机制）:
  verdict = run_interpretation_engine(req_message, agent, language)
  for inj in verdict["injections"]: messages.append(SystemMessage(content=inj))
  ... 应答完成后: scan_interpretation(verdict, full_answer, language, tool_log)
  → 返回 appends（措辞级补正）, engine 以 token 事件尾补
"""
import json
import re
import threading
import time
from pathlib import Path

from epistemic_guard import _match_philosopher   # 复用哲学家匹配（单一真源）

BASE = Path(__file__).resolve().parent          # backend/
LOG_FILE = BASE / "data" / "interpretation_engine.jsonl"   # 运行时记录（backend/data 已 gitignore）


# ═══════════════════════════════════════════════════════
# 1. 解释型问题分类（只对 4 类启用, 其余问题不强制多解释）
# ═══════════════════════════════════════════════════════
INTERPRETATION_CATEGORIES = [
    "literary_interpretation",              # 文学解读（意象/情节/人物）
    "philosophical_interpretation",         # 哲学解读（概念/框架/立场）
    "cross_author_comparison",              # 跨作者比较（对比不同思想家）
    "ambiguous_historical_interpretation",  # 模糊历史解读（史料不足/存在分歧）
]

# 解释性动词/问法（触发"这是解释型问题"的强信号）
_INTERP_VERBS = [
    "意味着", "象征着", "象征", "隐喻", "寓意", "暗示", "解读", "读作", "代表", "体现出",
    "反映出", "反映", "潜台词", "言外之意", "深层含义", "背后的",
    "怎么理解", "如何理解", "作何理解", "怎么解读", "如何解读", "究竟象征", "到底象征",
]
# 文学对象线索（意象/文体/叙事元素）
_LITERARY_OBJ = [
    "梦", "梦见", "梦到", "狮子", "老虎", "老人", "小说", "故事", "人物", "主人公", "角色",
    "情节", "文学", "作品", "叙事", "意象", "结尾", "结局", "剧情", "寓言", "童话", "诗歌",
    "戏剧", "小说里", "象征物", "神话",
]
# 哲学对象线索（概念化词 + 抽象价值词; 命中即可能触发哲学解读）
_PHIL_OBJ = [
    "哲学", "思想", "理论", "概念", "观点", "主义", "框架", "意义", "存在", "荒诞", "自由",
    "虚无", "本质", "生命", "精神", "超验", "道德", "灵魂", "世界", "索取", "转化", "态度",
    "目的", "价值", "幸福", "理式", "理性", "意志",
]
# 跨作者对比线索（须与 ≥2 位哲学家同现, 宁漏勿误）
_COMPARISON_CUES = [
    "对比", "比较", "异同", "区别", "一样", "相同", "相通", "谁更", "类似", "类比",
    "是不是", "是否", "一不一样", "一回事", "相同点", "不同点", "共通", "契合", "对应", "联系起来",
]
# 历史模糊线索（史料不足/学界分歧）
_HISTORY_AMBIGUITY = [
    "众说纷纭", "存在争议", "有争议", "学界", "历来", "悬案", "谜团", "未解之谜",
    "史料不足", "史料缺乏", "无定论", "尚无定论", "解读不一", "分歧", "史家", "历史学家",
]
_HISTORY_OBJ = [
    "历史", "事件", "记载", "史料", "时代", "战争", "时期", "人物", "皇帝", "王朝",
    "起义", "变法", "革命", "辩论", "论战", "生平", "去世", "生平",
]
# Phase 4 新增读法线索（老人与海回归集 T1/T2 需要）:
#   框架读法: 从《某书》……看……（借一部作品的视角读另一对象）
_FRAMED_RE = re.compile(r"从《([^》]{1,40})》[^。！？]{0,24}看")
#   二选一读法: 是……还是……（"是逃避式希望，还是荒诞幸福"; 允许中间出现逗号）
_EITHER_OR_RE = re.compile(r"是[^。！？]{1,30}还是")


class InterpretationChallenger:
    """解释型问题识别 + 多候选解读/双面证据/反证尝试的结构要求

    check(message) → {"activated", "categories", "object", "hypothesis_min",
                      "evidence_requirement", "analogy_guard", "depth_guard"}
    """

    def check(self, message):
        msg = (message or "").strip()
        out = {
            "activated": False,
            "categories": [],
            "object": "",
            "hypothesis_min": 0,            # 至少几个候选解读（启用时 ≥2）
            "evidence_requirement": {"supporting": False, "challenging": False},
            "analogy_guard": False,         # 跨作者比较 → 类比≠等同强制
            "depth_guard": False,           # 解释链深度惩罚强制
            "question": msg,
        }
        if not msg:
            return out
        philo = _match_philosopher(msg)
        interp_cue = any(v in msg for v in _INTERP_VERBS) or bool(_FRAMED_RE.search(msg))
        lit_obj = any(v in msg for v in _LITERARY_OBJ)
        phil_obj = any(v in msg for v in _PHIL_OBJ) or bool(philo)
        # 二选一（"是A还是B"）与 是不是/是否 同等视为 是/否 型问题（Phase 4: T2 触发）
        yn = ("是不是" in msg) or ("是否" in msg) or bool(_EITHER_OR_RE.search(msg))
        # Phase S (S3): 概念级比较识别——"超人和逍遥是不是一回事"未点名哲学家,
        # 但 超人(尼采)/逍遥(庄子) 是归属明确的概念, 同样构成跨作者比较
        concept_hits = [sys_name for sys_name, aliases in CROSS_SYSTEMS.items()
                        if any(a in msg for a in aliases)]
        phil_obj = phil_obj or bool(concept_hits)

        cats = []
        # ── 跨作者比较: ≥2 位哲学家（或归属明确的概念体系）+ 比较措辞 ──
        if (len(set(philo)) >= 2 or len(concept_hits) >= 2) and any(c in msg for c in _COMPARISON_CUES):
            cats.append("cross_author_comparison")
        # ── 模糊历史解读: 分歧/史料不足线索 + 历史对象 ──
        if any(c in msg for c in _HISTORY_AMBIGUITY) and any(c in msg for c in _HISTORY_OBJ):
            cats.append("ambiguous_historical_interpretation")
        # ── 文学/哲学解读: 解释性动词 + 对应对象; 弱门槛（"是不是/是否"型对象问题）──
        if (interp_cue and lit_obj) or (yn and lit_obj):
            cats.append("literary_interpretation")
        if (interp_cue and phil_obj) or (yn and phil_obj):
            cats.append("philosophical_interpretation")

        if not cats:
            return out
        out["activated"] = True
        out["categories"] = cats
        out["hypothesis_min"] = 2
        out["evidence_requirement"] = {"supporting": True, "challenging": True}
        out["analogy_guard"] = "cross_author_comparison" in cats
        out["depth_guard"] = True
        out["object"] = self._extract_object(msg)
        return out

    @staticmethod
    def _extract_object(msg):
        """解释对象提取: 《作品》→ 知名意象短语（梦狮/蝴蝶梦/超人…）→ 空"""
        m = re.search(r"《([^》]{1,40})》", msg)
        if m:
            return m.group(1)
        for cue in ("老人梦狮", "梦狮", "蝴蝶梦", "超人", "逍遥", "梦中", "梦见的", "无何有之乡", "寓言"):
            if cue in msg:
                return cue
        return ""


# ═══════════════════════════════════════════════════════
# 2. 置信度校准（内部评分 + 四档语言; 数字默认不展示）
# ═══════════════════════════════════════════════════════
# 四档语言分级（任务书原话; 用于注入指令与后置补正措辞）
TIERS = [
    ("strong", 0.85, "有很强文本依据"),
    ("moderate", 0.65, "相当有力的解释"),
    ("tentative", 0.40, "可成立但并非唯一的解释"),
    ("analogical", 0.0, "更适合作为启发性类比"),
]
TIER_KEYS = [t[0] for t in TIERS]
TIER_LANGUAGE_ZH = {
    "strong": "这是一种有很强文本依据的解释",
    "moderate": "这是一个相当有力的解释",
    "tentative": "这是一种可成立但并非唯一的解释",
    "analogical": "这种联系更适合作为启发性类比",
}
TIER_LANGUAGE_EN = {
    "strong": "This interpretation has very strong textual support",
    "moderate": "This is a fairly forceful interpretation",
    "tentative": "This is a defensible but not the only interpretation",
    "analogical": "This connection is better treated as a heuristic analogy",
}

# 跨体系计数: 系统名 → 别名（同一系统内去重; 常见通用词不入表, 防误计）
CROSS_SYSTEMS = {
    "加缪": ["加缪", "加缪主义", "荒诞哲学", "西西弗斯"],
    "尼采": ["尼采", "权力意志", "永恒轮回", "超人哲学", "超人"],
    "庄子": ["庄子", "庄周", "逍遥游", "逍遥", "齐物"],
    "老庄/道家": ["老庄", "道家", "老子", "道德经", "无为"],
    "佛教": ["佛教", "佛学", "佛陀", "释迦牟尼", "涅槃", "缘起", "空性"],
    "斯多葛": ["斯多葛", "斯多亚", "斯多噶", "塞涅卡", "爱比克泰德", "马可·奥勒留"],
    "基督教": ["基督教", "圣经", "奥古斯丁", "神学", "三位一体"],
    "儒家": ["儒家", "孔孟", "仁义", "论语"],
    "康德": ["康德", "义务论", "先验"],
    "黑格尔": ["黑格尔", "绝对精神", "辩证法"],
    "叔本华": ["叔本华", "意志主义", "表象世界"],
    "萨特": ["萨特", "自为存在"],
    "海德格尔": ["海德格尔", "此在", "存在之思"],
    "现象学": ["现象学", "胡塞尔"],
    "分析哲学": ["分析哲学", "语言分析", "维特根斯坦", "逻辑哲学论"],
    "实用主义": ["实用主义", "詹姆士", "杜威", "皮尔士"],
    "马克思主义": ["马克思", "马克思主义", "异化", "历史唯物主义"],
    "柏拉图": ["柏拉图", "理念论", "洞穴喻"],
    "亚里士多德": ["亚里士多德", "四因", "潜与现实"],
    "弗洛伊德/心理学": ["弗洛伊德", "精神分析", "潜意识", "心理学"],
    "伊壁鸠鲁": ["伊壁鸠鲁", "快乐主义", "享乐主义"],
    "犬儒主义": ["犬儒", "第欧根尼"],
    "斯宾诺莎": ["斯宾诺莎", "实体论"],
    "存在主义": ["存在主义", "荒谬主义"],
}

# 越级断言（解释性回答中禁止的措辞; 先剥离否定式再匹配, 防"并非唯一"误伤）
_NEGATED_OVERCLAIM = ("并非唯一", "不是唯一", "并非必然", "不是必然", "非唯一",
                      "不是一个", "未必是", "不一定", "不是一回事", "并非一回事",
                      "not the only", "not necessarily", "not the same",
                      "not equivalent", "not identical")
_OVERCLAIM_RE = re.compile(
    r"完全正确|绝对正确|毫无疑问|显然是|显然就是|本质上完全一样|本质完全一样|本质相同|完全相同|"
    r"一模一样|是一回事|完全等同|必然如此|一定就是|唯一正确|唯一的解释|唯一的解读|唯一读法|唯一可能|"
    r"definitely|obviously|exactly the same|essentially the same|completely correct|identical")
_DIRECT_QUOTE_RE = re.compile(r"[“\"]([^”\"]{4,120})[”\"]")
_TEXT_CITE_RE = re.compile(r"【《[^》]+》[^】]*】")
_BOOK_QUOTE_RE = re.compile(r"《[^》]{2,30}》[^。]{0,60}(原文|写道|引文|说过|写到)")
_SCHOLARLY_RE = re.compile(r"研究|学界|有学者|文献(指出|认为)|评注者|权威解读")

# 干预措辞（答案已含这些表达 → 视为已多候选/已反证, 不再补正）
_ALT_MARKERS = [
    "并非唯一", "不是唯一", "另一种读法", "另一种理解", "另一种可能", "也可以读作", "也可以理解",
    "也可能被", "一种阅读", "一种读法", "其他读法", "不同读法", "alternative", "not the only",
    "another reading", "could also be read", "equally plausible",
]
_CHALLENGE_FOUND = ["削弱", "反证", "反驳", "质疑", "挑战证据", "challenging evidence", "counter-evidence"]
_CHALLENGE_EMPTY = [
    "未检索到足以削弱", "未找到反证", "没有发现反证", "没有找到削弱", "无削弱材料", "未检索到削弱",
    "no counter-evidence", "no evidence against", "nothing that weakens",
]
_INTERPRETIVE_ANSWER = [
    "意味着", "象征着", "隐喻", "寓意", "暗示", "解读", "读作", "代表", "体现", "反映",
    "本身", "本质", "精神", "意义", "可以说", "是一种", "可以理解", "相通", "象征",
]


class ConfidenceCalibrator:
    """解释置信度校准（规则版; 数字仅内部日志, 默认不出现在回答里）

    detect_signals(answer) → 证据信号（原典引证/直接引语/学界共识/越级断言/跨体系阶数）
    calibrate(text=None, signals=None) → {"confidence": float, "basis": [labels], "tier": key}
    """

    # ── 跨体系计数 → 解释链阶数（0=纯文本内部; 1=文本→某框架 一阶; 2=再跳一体系 二阶…）──
    @staticmethod
    def count_cross_systems(text):
        if not text:
            return 0
        found = []
        for name, aliases in CROSS_SYSTEMS.items():
            if any(a in (text or "") for a in aliases):
                found.append(name)
        return len(found)

    @staticmethod
    def interpretation_order(text_or_signals):
        return text_or_signals.get("interpretation_order", 0) if isinstance(text_or_signals, dict) \
            else ConfidenceCalibrator.count_cross_systems(text_or_signals)

    @staticmethod
    def depth_penalty(order):
        """深度惩罚: 阶数 ≥2 后, 每多一次跨体系跳转扣 0.05（只降不升, 绝对量有下限）"""
        return 0.05 * max(0, order - 1)

    def detect_signals(self, text):
        t = text or ""
        t_clean = t
        for neg in _NEGATED_OVERCLAIM:
            t_clean = t_clean.replace(neg, "")
        order = self.count_cross_systems(t)
        return {
            "primary_text_support": bool(_TEXT_CITE_RE.search(t) or _BOOK_QUOTE_RE.search(t)),
            "direct_quote": bool(_DIRECT_QUOTE_RE.search(t)) and ("《" in t),
            "scholarly": bool(_SCHOLARLY_RE.search(t)),
            "overclaim": bool(_OVERCLAIM_RE.search(t_clean)),
            "interpretation_order": order,
        }

    def calibrate(self, text=None, signals=None):
        sig = signals if signals is not None else self.detect_signals(text or "")
        conf = 0.50                                    # 基线: 无新证据的解释性判断
        if sig.get("primary_text_support"):
            conf += 0.15
        if sig.get("direct_quote"):
            conf += 0.10
        if sig.get("scholarly"):
            conf += 0.05
        if sig.get("overclaim"):
            conf -= 0.10                               # 越级断言扣分（语言与证据不符）
        conf -= self.depth_penalty(sig.get("interpretation_order", 0))
        conf = round(max(0.05, min(0.95, conf)), 2)
        basis = []
        if sig.get("primary_text_support"):
            basis.append("primary_text_support")
        if sig.get("direct_quote"):
            basis.append("direct_quote")
        if sig.get("scholarly"):
            basis.append("scholarly_consensus")
        if not sig.get("primary_text_support") and not sig.get("direct_quote"):
            basis.append("cross_text_inference")
        if sig.get("interpretation_order", 0) >= 2:
            basis.append("framework_chain")
        if sig.get("overclaim"):
            basis.append("overclaim_detected")
        return {"confidence": conf, "basis": basis, "tier": self.tier_of(conf), "signals": sig}

    @staticmethod
    def tier_of(confidence):
        for key, threshold, _ in TIERS:
            if confidence >= threshold:
                return key
        return "analogical"

    @staticmethod
    def tier_language(tier, language="zh"):
        return TIER_LANGUAGE_ZH.get(tier, TIER_LANGUAGE_ZH["tentative"]) if language == "zh" \
            else TIER_LANGUAGE_EN.get(tier, TIER_LANGUAGE_EN["tentative"])


# ═══════════════════════════════════════════════════════
# 3. 前置注入（build_interpretation_injections）
# ═══════════════════════════════════════════════════════
def build_interpretation_injections(verdict, language="zh"):
    """由裁决生成系统提示注入（解释型问题才产生; 任何异常不影响主流程）"""
    if not verdict.get("activated"):
        return []
    obj = verdict.get("object") or "这个对象"
    cats = verdict.get("categories", [])
    en = language == "en"
    inj = []
    if en:
        inj.append(
            f"[System interpretation · multi-hypothesis] You are handling an interpretation question "
            f"(object: {obj}). Follow strictly: ① separate 'what the text explicitly states' from "
            f"'interpretation'; ② offer at least two defensible readings (H1/H2…) and mark which parts have "
            f"direct textual support and which are framework-driven; ③ present evidence as "
            f"supporting_evidence and challenging_evidence; ④ attempt at least once to ask 'what material "
            f"would weaken my main reading?' — look for counterexamples, alternative readings, or scholarly "
            f"criticism; ⑤ if you find no challenging material, write 'I found no direct material that weakens "
            f"this reading' and set challenging_evidence to [] — NEVER invent a counterview; ⑥ conclude with "
            f"'this is one reading' wording, not 'completely correct / the only interpretation'.")
        if "cross_author_comparison" in cats:
            inj.append(
                "[System cross-author · analogy != equivalence] This is a cross-author comparison. "
                "Distinguish two levels of assertion: ① direct agreement/influence/equivalence (requires "
                "primary-text or historical evidence); ② structural similarity/analogy (premises, contexts, "
                "targets may differ). Without direct evidence, never say 'essentially the same / they are one "
                "and the same'; use 'there is a valuable analogy' or 'comparable in some sense'.")
        if verdict.get("depth_guard"):
            inj.append(
                "[System interpretation depth] If your reading spans multiple systems (e.g. text → Camus → "
                "Zhuangzi → Buddhism → Stoicism), each additional cross-system jump may only keep or lower, "
                "never raise, your confidence that they are 'the same'. The more jumps, the more the "
                "conclusion must be framed as heuristic analogy, not essential identity.")
    else:
        inj.append(
            f"【解释型问题·多候选解读（系统）】你正在处理一个解释型问题（解释对象: {obj}）。"
            "请严格遵守: ①先区分'原文明确陈述的事实'与'解读'; ②至少提出两种可成立的候选解读（H1/H2…），"
            "并标明哪些内容有文本直接支持、哪些是借框架的演绎; ③把文本材料分成 supporting_evidence "
            "（支持你主要解读的证据）与 challenging_evidence（可能削弱它的证据）两部分呈现; "
            "④至少主动设想一次'什么材料会削弱我的主要解读'——可以检索反例、替代读法或学界对其的批评; "
            "⑤若检索/思考后找不到挑战材料, 明确写'未检索到足以削弱这一解读的直接材料'并把 "
            "challenging_evidence 置为 []——绝不编造反方观点; ⑥主要结论用'这是一种理解/一种读法'收尾, "
            "不要以'完全正确/唯一解释'作结。")
        if "literary_interpretation" in cats:
            inj.append(
                "【文学解读（系统）】对文学意象/情节的解读至少覆盖两个层面: ①文本内部层面（人物心理、"
                "情节功能、结构）; ②语境层面（作者生平、时代、创作意图）。若要借哲学框架（如加缪的荒诞）"
                "解读, 必须明确这是'借框架的读法'——不是原文直接写出的含义; 同一意象也可能支持基于文本"
                "自身的读法。")
        if "philosophical_interpretation" in cats:
            inj.append(
                "【哲学解读（系统）】请区分: ①概念分析（概念如何定义/使用/推演）; ②文本依据（原文真正"
                "怎么说）; ③框架借用（借另一位思想家的框架进行演绎——须标注为框架演绎而非原文事实）。"
                "三者混同会高估解释的确定性。")
        if "ambiguous_historical_interpretation" in cats:
            inj.append(
                "【历史解读（系统）】该问题存在史料模糊或解读分歧。明确标出: 现有史料直接支持什么、"
                "哪些是推演、学界是否存在公认分歧; 对分歧给出至少两种立场, 不要以单一叙述收尾。")
        if verdict.get("analogy_guard"):
            inj.append(
                "【跨作者对比·类比≠等同（系统）】这是一次跨思想家的对比辨析。必须区分两种断言的证据要求: "
                "①'直接认同/影响/等同'（需要史料或原典直接证据）; ②'结构相似/类比'（前提、语境、目标不同, "
                "只是形式相近）。未经文本与史料证明时, 严禁说'本质完全一样/是一回事/完全相同'; "
                "请使用'存在可资借鉴的类比(analogy)''在某种意义上相通'等措辞。")
        if verdict.get("depth_guard"):
            inj.append(
                "【解释链深度（系统）】若你的解读跨多个思想体系（如: 文本→加缪→庄子→佛教→斯多葛），"
                "每增加一次跨体系跳转, 你对'它们是一回事'的置信度只允许保持或降低, 不允许升高。"
                "跳转越多, 结论越应定位为'启发性类比/有趣的联系', 而不是'本质相同'——这是深度惩罚机制。")
        inj.append(
            "【确定性语言（系统）】解释性措辞必须与证据强度匹配: 证据很直接（多个原文引证可定位、无替代"
            "读法）→'有很强文本依据……'; 有文本依据但存在替代读法→'这是相当有力的解释……'; 主要借框架"
            "构建、文本直接支持弱→'这是一种可成立但并非唯一的解释……'; 仅结构/气质相似、无文本依据→"
            "'这种联系更适合作为启发性类比……'。禁用与证据强度不符的断言（如'完全正确''本质完全一样'"
            "'显然必须是'）。")
    return inj


# ═══════════════════════════════════════════════════════
# 4. 编排: run_interpretation_engine / scan_interpretation / 日志
# ═══════════════════════════════════════════════════════
def run_interpretation_engine(message, agent="general", language="zh"):
    """前置: 识别解释型问题并生成注入（纯计算, 不调 LLM）

    返回: {activated, categories, object, hypothesis_min, evidence_requirement,
           analogy_guard, depth_guard, injections}
    """
    verdict = InterpretationChallenger().check(message)
    verdict["injections"] = build_interpretation_injections(verdict, language)
    _log_record({"phase": "pre", "agent": agent, "language": language,
                 "message": (message or "")[:500],
                 "activated": verdict["activated"],
                 "categories": verdict["categories"],
                 "analogy_guard": verdict["analogy_guard"],
                 "depth_guard": verdict["depth_guard"],
                 "injections": len(verdict["injections"])})
    return verdict


# 后置补正措辞（措辞级, 不含置信度数字; 永不编造具体反方材料）
AVE_HEDGE_ZH = ("需要补充一句：这里应当区分类比(analogy)与等同(equivalence)——两个思想家的概念即便在结构上"
                "相近，其论证前提、语境归属与文本证据也各不相同。'相似'不等于'本质相同'；更稳妥的表述是："
                "两者之间存在可资借鉴的类比，而非概念等同。")
AVE_HEDGE_EN = ("One clarification: analogy should be distinguished from equivalence — even when two thinkers' "
                "concepts are structurally close, their argumentative premises, contexts, and textual evidence "
                "differ. 'Similar' does not mean 'essentially the same'; the safer formulation is that there is "
                "a valuable analogy, not conceptual equivalence.")
_TIER_HEDGE_ZH = {
    "strong": "（补充：这是一种有很强文本依据的解释；但它仍是一种读法，文本中的其他线索也可能支持不同理解。）",
    "moderate": "（补充：这是一个相当有力的解释，但并非唯一——文本中的其他线索也可能支持另一条读法。）",
    "tentative": "（补充：这是一种可成立但并非唯一的解释——它的强度依赖于所采用的框架，换个框架会呈现不同的面貌。）",
    "analogical": "（补充：这种联系更适合作为启发性类比，而非思想等同或直接文本依据。）",
}
_TIER_HEDGE_EN = {
    "strong": "(One note: this interpretation has very strong textual support, yet it remains one reading — "
              "other clues may support a different understanding.)",
    "moderate": "(One note: this is a fairly forceful interpretation, but not the only one — other clues in the "
                 "text may support another reading.)",
    "tentative": "(One note: this is a defensible but not the only interpretation — its strength depends on the "
                  "framework chosen; another framework would yield a different picture.)",
    "analogical": "(One note: this connection is better treated as a heuristic analogy than as conceptual "
                   "equivalence or direct textual evidence.)",
}


def scan_interpretation(verdict, answer, language="zh", tool_log=None):
    """应答后校验: 解释型回答是否给出候选读法/有没有越级断言; 需要时返回措辞级补正

    返回: {activated, categories, answer_signals, confidence, basis, tier,
           supporting_evidence_present, challenging_evidence_trace, alternatives_offered,
           overclaim, appends}
    原则: ①默认不展示置信度数字（appends 只有措辞）; ②永不编造具体反方材料;
          ③仅对"解释型问题且答案确含解释性判断且未有多候选痕迹"时补正, 避免干扰事实类回答。
    """
    res = {
        "activated": bool(verdict.get("activated")),
        "categories": verdict.get("categories", []),
        "answer_signals": {},
        "confidence": None, "basis": [], "tier": None,
        "supporting_evidence_present": False,
        "challenging_evidence_trace": "absent",   # found / empty / absent
        "alternatives_offered": False,
        "overclaim": False,
        "obligations": [],                        # Phase S (S3): 义务履行状态
        "appends": [],
    }
    if not res["activated"]:
        return res
    ans = answer or ""
    cal = ConfidenceCalibrator()
    sig = cal.detect_signals(ans)
    calib = cal.calibrate(signals=sig)
    res.update({
        "answer_signals": sig,
        "confidence": calib["confidence"],          # 内部记录, 不展示
        "basis": calib["basis"],
        "tier": calib["tier"],
        "supporting_evidence_present": sig["primary_text_support"] or sig["direct_quote"],
        "challenging_evidence_trace": _challenge_trace(ans, tool_log),
        "alternatives_offered": any(m in ans for m in _ALT_MARKERS),
        "overclaim": sig["overclaim"],
    })
    # 补正条件: 解释型问题 + 答案含解释性判断（或检出越级断言）;
    # Phase S (S3): 追加与否由 semantic obligation 状态决定——只有
    #   REQUIRED + UNSATISFIED 的义务才允许补正; 同一义务一旦已由正文履行
    #   （"不是一回事/不能等同/二者有本质区别/只能类比/相似不意味着同一…"均为
    #   analogy boundary 的等价履行），不得因措辞不同重复追加。
    from semantic_obligations import derive_obligations, assess_obligations
    obligations = assess_obligations(derive_obligations(None, verdict), ans)
    res["obligations"] = obligations
    # Phase T (T13-C): 高层语义义务（alternative_interpretation/uncertainty_disclosure/
    # analogy_boundary）未命中关键词现在记 UNKNOWN 而非 UNSATISFIED——补正触发相应改为
    # 只依赖结构性信号（overclaim = 越级断言检出; alternatives_offered = 替代解读缺席）,
    # 不再用关键词命中与否决定追加, 也不新增正文 Guard。
    unsat_types = {o["type"] for o in obligations if o["status"] == "UNSATISFIED"}
    interpretive = any(m in ans for m in _INTERPRETIVE_ANSWER)
    if interpretive or sig["overclaim"]:
        if "cross_author_comparison" in res["categories"] and (
                sig["overclaim"] or "analogy_boundary" in unsat_types):
            # 类比≠等同义务未履行（含正文声称"本质完全一样"的越级断言）→ 补一次
            res["appends"].append(AVE_HEDGE_EN if language == "en" else AVE_HEDGE_ZH)
        elif not res["alternatives_offered"]:
            hedge = (_TIER_HEDGE_EN if language == "en" else _TIER_HEDGE_ZH)
            res["appends"].append(hedge.get(calib["tier"], hedge["tentative"]))
    _log_record({"phase": "post", "agent": "scan", "language": language,
                 "activated": res["activated"], "categories": res["categories"],
                 "confidence": res["confidence"], "tier": res["tier"],
                 "basis": res["basis"], "overclaim": sig["overclaim"],
                 "alternatives_offered": res["alternatives_offered"],
                 "challenging_evidence_trace": res["challenging_evidence_trace"],
                 "obligations": [{"type": o.get("type"), "status": o.get("status")}
                                 for o in res.get("obligations") or []],
                 "appends": len(res["appends"])})
    return res


def _challenge_trace(ans, tool_log):
    """挑战证据痕迹: found=答案/检索中见反证; empty=明确宣称无削弱材料（允许）; absent=未提及"""
    if any(m in (ans or "") for m in _CHALLENGE_FOUND):
        return "found"
    if any(m in (ans or "") for m in _CHALLENGE_EMPTY):
        return "empty"
    quest = [str(tc.get("args", {}).get("query", "")) for tc in (tool_log or [])
             if isinstance(tc, dict) and tc.get("name") in ("search_books", "websearch", "concept_trace")]
    if any(any(k in q for k in ("反例", "异议", "批评", "质疑", "不同读法", "削弱")) for q in quest):
        return "found"
    return "absent"


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
