# -*- coding: utf-8 -*-
"""Evaluation Suite（Phase 4）——回答质量五维评分（纯规则, 不调 LLM; 离线评估工具）

O4 Cognitive Layer Collapse 注: 原 interpretation_engine.py / answer_composer.py /
semantic_obligations.py 是 runtime 内的第二套认知裁决层（Shadow Agent）, 已从生产引擎
删除。本评估套件是纯离线评分器（只在测试/回归中调用, 不在 stream_agent 请求路径上）,
其解释质量与回答体验维度所需的检测启发式以自带副本形式保留在本文件中
（O4 任务书: "把这两个函数 MOVE 进 evaluation_suite（自带副本）"）——它们不再对
任何运行时行为产生注入/补正/改写效果。

O4-RP1 注: 原生产前提核对模块已删除——PremiseVerifier（前提错误检出, 评分用）
以自带数据副本形式保留在本文件（离线评分, 不在请求路径上, 无注入效果）;
EpistemicClaimClassifier / _match_philosopher / PHILOSOPHER_ALIASES 迁入
evidence_contract（生产单源）, 本文件经 import 复用。

五个评分器都是确定性规则:

  evaluate_premise_accuracy    前提准确性: 错误数字 / 错误作者 / 错误书名 / 错误年代 /
                               错误概念归属 的检出、校正落实、校正是否破坏主体分析
  evaluate_epistemic_accuracy  知识论准确性: fact/quote/inference/interpretation/
                               counterfactual/speculation 的区分与措辞一致性
  evaluate_interpretation_quality  解释质量: confirmation bias / alternative explanation /
                               cross-framework overreach（类比≠等同）
  evaluate_evidence            证据: citation validity / citation used rate /
                               unsupported claim rate
  evaluate_answer_ux           回答体验: answer directness / redundancy / reasoning noise
  evaluate_answer              五维汇总（供运行时审计日志与测试断言）

用法（backend/tests/ 的 Evaluation Suite 用例与 regression_oldman_sea 回归集直接消费）:
  report = evaluate_answer(question, answer, tool_log=..., language="zh")
  每个维度返回 {score: 0..1, passed: bool, metrics: {...}, findings: [...]}
"""
import json
import re
from pathlib import Path

from evidence_contract import (build_evidence_contract, EpistemicClaimClassifier,
                               _match_philosopher, _norm_author, _strip_marks,
                               _load_philosophers, PHILOSOPHER_ALIASES)

BASE = Path(__file__).resolve().parent          # backend/


# ═══════════════════════════════════════════════════════
# 0. PremiseVerifier 离线评分副本（O4-RP1: 原生产版本随 guard 模块删除,
#    评分 API 面不变——只用于离线检出"回答是否落实了前提校正", 不注入不拦截）
# ═══════════════════════════════════════════════════════
def _load_books():
    """app/public/books.json（唯一正式书目, 409 本）→ {书名: {作者, 作者短名, id}}"""
    try:
        raw = json.load(open(BASE.parent / "app" / "public" / "books.json", encoding="utf-8"))
        out = {}
        for b in raw:
            t = _strip_marks(b.get("title") or "")
            a = b.get("author") or ""
            if t:
                out[t] = {"author": a, "author_short": _norm_author(a), "id": b.get("id")}
        return out
    except Exception:
        return {}


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

# 可验证事实前提规则（手工精配, 只收"显著影响答案且必改"的常见错误;
# 每例: 主题词 + 错误数字 + 语境动词; 缺失其一即不触发——宁漏勿误）
PREMISE_RULES = [
    {
        "id": "oldman_84_days",
        "topic_keywords": ["老人与海", "圣地亚哥", "桑地亚哥", "老渔夫", "老人"],
        "number": {"wrong": "87", "right": "84", "unit": "天"},
        # 语境词覆盖"87天的执念"类表述（T3 回归题）, 不再只认"捕/鱼";
        # "困境"覆盖"从87天的困境到最后…"类无渔获动词的抽象指称
        "context_words": ["捕", "钓", "没有捕到", "鱼", "执念", "出海", "一无所获", "空手", "没捕", "困境"],
        "exclude_words": [],
        # 87 天必须判断用户所指事件, 不做简单数字替换——
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


class PremiseVerifier:
    """用户事实前提核对（离线评分用副本; 只检出, 不注入不拒绝）"""

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
            # 语义判定"87天"所指事件, 而非简单数字替换。
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
        # ── 错误书名规则（《西西弗斯》→《西西弗斯神话》）──
        titles = self._check_book_titles(msg)
        out.extend(titles)
        # ── 错误概念归属规则（权力意志→尼采 等）──
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
        """字符串规则（书名/概念）的裁决——与数字规则同构"""
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
        """判定错误数字所指事件（供 84/87 类双事实规则使用）

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
        """作品作者归属检查: 'X写的《Y》'、'《Y》里X认为/写到/论述' 且 X≠真实作者 → 检出"""
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
            "correction_note": f"《{work}》的作者是{real}而非{claimed}。",
            "matched": f"{claimed}的《{work}》",
        }

# ═══════════════════════════════════════════════════════
# 1. Premise Accuracy —— 错误数字/作者/书名/年代/概念归属
# ═══════════════════════════════════════════════════════
def _premise_category(rule_id):
    """rule_id → 错误类别（评估维度要求的五类）"""
    if rule_id.startswith("title:"):
        return "wrong_book_title"
    if rule_id.startswith("concept:"):
        return "wrong_concept_attribution"
    if rule_id.startswith("attribution:"):
        return "wrong_author"
    if rule_id == "oldman_84_days":
        return "wrong_number"
    if rule_id in ("antichrist_1888", "rebel_1951"):
        return "wrong_era"
    return "other"


def _correction_present(check, answer):
    """校正落实: 回答包含 corrected_value 中任一数字或前缀（多数字值逐个匹配, 防"19511942"拼接误判）"""
    fixed = check.get("corrected_value") or ""
    ans = answer or ""
    nums = re.findall(r"\d+", fixed)
    if nums and any(n in ans for n in nums):
        return True
    return bool(fixed and fixed[:6] in ans)


def _analysis_intact(check, answer):
    """校正是否破坏主体分析: 校正之后仍有实质内容（≥40 字）+ 无拒绝/敷衍"""
    ans = answer or ""
    if len(ans) < 80:
        return False
    if any(r in ans for r in ("无法回答", "不能回答", "拒绝回答", "我回答不了")):
        return False
    fixed = check.get("corrected_value") or ""
    digits = next((d for d in re.findall(r"\d+", fixed) if d in ans), "")
    rest = ans
    if digits:
        i = ans.find(digits)
        if i >= 0:
            rest = ans[i + len(digits):]
    return len(rest) >= 40


def evaluate_premise_accuracy(question, answer, checks=None, language="zh"):
    """前提准确性: 每个已检出矛盾 → 校正落实? 破坏主体分析?

    metrics: {detected, corrected, disruptive, categories: {类别: [rule_id]}}
    """
    checks = checks if checks is not None else PremiseVerifier().check(question)
    contrad = [c for c in checks if c.get("status") == "contradicted"]
    cases, categories = [], {}
    for c in contrad:
        cat = _premise_category(c.get("rule_id") or "")
        categories.setdefault(cat, []).append(c.get("rule_id"))
        corrected = _correction_present(c, answer or "")
        intact = _analysis_intact(c, answer or "")
        cases.append({
            "rule_id": c.get("rule_id"), "category": cat,
            "corrected": corrected, "analysis_intact": intact,
            "disruptive": corrected and not intact,
        })
    n = len(cases)
    passed = all(not x["disruptive"] and x["corrected"] for x in cases) if n else True
    score = 1.0 if n == 0 else sum(
        1.0 if x["corrected"] and x["analysis_intact"] else
        0.5 if x["corrected"] else 0.0 for x in cases) / n
    findings = []
    for x in cases:
        if not x["corrected"]:
            findings.append(f"correction_missing:{x['rule_id']}")
        elif x["disruptive"]:
            findings.append(f"correction_disrupted_analysis:{x['rule_id']}")
    return {
        "score": round(score, 2), "passed": passed,
        "metrics": {"detected": n, "corrected": sum(1 for x in cases if x["corrected"]),
                    "disruptive": sum(1 for x in cases if x["disruptive"]),
                    "categories": categories},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 2. Epistemic Accuracy —— fact/quote/inference/interpretation/counterfactual/speculation
# ═══════════════════════════════════════════════════════
_SPECULATION_MARKERS = ["或许", "可能", "也许", "推测", "猜测", "一种可能", "不妨设想"]
_COUNTERFACTUAL_ASSERT = re.compile(
    r"(一定会|肯定会|必定会|绝不会|必然认为|肯定认为|一定认为|无疑会)")
_QUOTE_CUE = re.compile(r"(原文写道|原文说|原话是|书上原话|直接引用)")
_CITE_MARKER = re.compile(r"【《[^》]+》[^】]*】")


def evaluate_epistemic_accuracy(answer, language="zh"):
    """知识论准确性: 回答的措辞与知识论层级一致

    findings:
      unhedged_assertion:{词}   未经证据支持的强化措辞（完全正确/毫无疑问/本质就是…）
      overclaim_unhedged        强模态 + 解释性判断（"一定完成了转变"≠ 原文所说）
      counterfactual_unbounded  作者反事实断言无边界（"加缪一定会认为…"无"没有证据表明"）
      quote_unlocatable         宣称原文引语但既无引号也无引用标注（无法定位）
      hedge_contradiction       同一句既用推测词又用强模态
    metrics: claim_types 计数（六类区分）; overclaim / unbounded / unlocatable
    """
    cl = EpistemicClaimClassifier()
    sents = cl.split_sentences(answer or "")
    claims = [cl.classify(s, extra=True) for s in sents if len(s.strip()) >= 8]
    findings = []
    # 未经证据支持的强化措辞（原 answer_composer 检测真源, O4 后为本文件自带副本）
    for w in strong_wording_hits(answer or ""):
        findings.append(f"unhedged_assertion:{w}")
    for c in claims:
        t = c["claim"]
        if any(m in t for m in _SPECULATION_MARKERS) and _STRONG_MODAL.search(t):
            findings.append(f"hedge_contradiction:{t[:24]}")
            break
        if c.get("strong_modal") and c["epistemic_type"] in (
                "TEXTUAL_INFERENCE", "CROSS_TEXT_INTERPRETATION", "SPECULATION"):
            findings.append(f"overclaim_unhedged:{t[:24]}")
            break
        if _QUOTE_CUE.search(t) and not re.search(r"[“\"『]", t) and not _CITE_MARKER.search(t):
            findings.append(f"quote_unlocatable:{t[:24]}")
    # 反事实断言无边界: 作者名 + 断言词, 但回答通篇没有"没有证据表明"
    authors = _match_philosopher(answer or "")
    unbounded = False
    if authors and "没有证据表明" not in (answer or ""):
        for a in authors[:1]:
            if re.search(rf"{a}[^。！？\n]{{0,20}}(一定会|绝不会|肯定认为|一定认为|必定会)", answer or ""):
                unbounded = True
                findings.append(f"counterfactual_unbounded:{a}")
                break
    types = {}
    for c in claims:
        types[c["epistemic_type"]] = types.get(c["epistemic_type"], 0) + 1
    score = 1.0
    score -= 0.3 * len([f for f in findings if f.startswith("unhedged_assertion")])
    if any(f.startswith("overclaim_unhedged") for f in findings):
        score -= 0.4
    if unbounded:
        score -= 0.3
    if any(f.startswith("quote_unlocatable") for f in findings):
        score -= 0.2
    if any(f.startswith("hedge_contradiction") for f in findings):
        score -= 0.2
    score = max(0.0, round(score, 2))
    return {
        "score": score, "passed": not findings,
        "metrics": {"claim_types": types, "claim_count": len(claims)},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 3. Interpretation Quality —— confirmation bias / alternative / overreach
# ═══════════════════════════════════════════════════════
def evaluate_interpretation_quality(question, answer, tool_log=None, language="zh"):
    """解释质量: 单候选（confirmation bias）/ 无替代解释 / 跨框架越级

    findings:
      confirmation_bias          解释型问题只给单候选（无替代读法/无反证痕迹）
      no_challenge_attempt       未主动设想削弱材料（absent 记为软性发现）
      cross_framework_overreach  越级断言（本质完全一样/毫无疑问/唯一解释 等）
    """
    verdict = InterpretationChallenger().check(question)
    scan = scan_interpretation(verdict, answer, language, tool_log)
    findings = []
    if not scan["activated"]:
        return {
            "score": 1.0, "passed": True,
            "metrics": {"activated": False, "categories": []},
            "findings": [],
        }
    if scan["overclaim"]:
        findings.append("cross_framework_overreach")
    if not scan["alternatives_offered"]:
        findings.append("confirmation_bias")
    if scan["challenging_evidence_trace"] == "absent":
        findings.append("no_challenge_attempt")
    score = 1.0 - 0.4 * findings.count("cross_framework_overreach") \
        - 0.4 * findings.count("confirmation_bias") - 0.2 * findings.count("no_challenge_attempt")
    return {
        "score": max(0.0, round(score, 2)), "passed": not findings,
        "metrics": {"activated": True, "categories": scan["categories"],
                    "alternatives_offered": scan["alternatives_offered"],
                    "challenging_trace": scan["challenging_evidence_trace"],
                    "overclaim": scan["overclaim"]},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 4. Evidence —— citation validity / used rate / unsupported claim rate
# ═══════════════════════════════════════════════════════
def evaluate_evidence(answer, contract=None, tool_log=None, language="zh"):
    """证据: 未核验引用 / 引用使用率 / 无支撑 Claim 率

    findings:
      unverified_citation:{书}  回答引用了检索池无法定位的原典
      low_used_rate             检索很多但回答几乎没用（used/retrieved < 0.2 且 retrieved ≥ 5）
      unsupported_claims         无 DIRECT evidence 支撑的断言占比 > 0.5
                                  （SPECULATION/UNKNOWN 除外——它们本就无需直接证据）
    """
    if contract is None:
        contract = build_evidence_contract(tool_log or [], answer, language=language)
    findings = []
    for u in contract["unverified_citations"]:
        findings.append(f"unverified_citation:{u.get('book')}")
    retrieved = contract["retrieved_count"]
    used = contract["used_count"]
    used_rate = round(used / retrieved, 2) if retrieved else None
    if retrieved >= 5 and used_rate is not None and used_rate < 0.2:
        findings.append("low_used_rate")
    claims = contract["claims"]
    assessable = [c for c in claims
                  if c["epistemic_type"] not in ("SPECULATION", "UNKNOWN")]
    unsupported = [c for c in assessable if not c["direct_evidence"]]
    unsupported_rate = round(len(unsupported) / len(assessable), 2) if assessable else 0.0
    if assessable and unsupported_rate > 0.5:
        findings.append("unsupported_claims")
    score = 1.0
    score -= 0.3 * len(contract["unverified_citations"])
    if "unsupported_claims" in findings:
        score -= 0.3
    score = max(0.0, round(score, 2))
    return {
        "score": score, "passed": not findings,
        "metrics": {"retrieved_count": retrieved, "used_count": used,
                    "used_rate": used_rate,
                    "unverified_count": len(contract["unverified_citations"]),
                    "unsupported_rate": unsupported_rate,
                    "claim_count": len(claims)},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 5. Answer UX —— directness / redundancy / reasoning noise
# ═══════════════════════════════════════════════════════
def evaluate_answer_ux(answer, composer_scan=None, language="zh"):
    """回答体验: 直接判断 / 冗余 / 推理噪音 / 默认骨架残留

    findings:
      process_leadin            首句是过程叙述而非直接判断
      reasoning_noise:{词}      过程叙述泄漏进正文（"让我检索…"）
      default_block:{词}        材料说明/检索过程/原典路径/再总结 等默认骨架残留
      redundancy:{详情}         重复句 / 总结连接词堆叠
    """
    scan = composer_scan if composer_scan is not None \
        else scan_composition({"activated": True}, answer, language)
    findings = []
    if scan["direct_judgment"] is False:
        findings.append("process_leadin")
    for p in scan["reasoning_noise"]:
        findings.append(f"reasoning_noise:{p}")
    for b in scan["banned_blocks"]:
        findings.append(f"default_block:{b}")
    for r in scan["redundancy"]:
        findings.append(f"redundancy:{r}")
    score = 1.0
    if scan["direct_judgment"] is False:
        score -= 0.3
    score -= 0.2 * len(scan["reasoning_noise"])
    score -= 0.2 * len(scan["banned_blocks"])
    score -= 0.2 * len(scan["redundancy"])
    return {
        "score": max(0.0, round(score, 2)), "passed": not findings,
        "metrics": {"direct_judgment": scan["direct_judgment"],
                    "structure": scan["structure_signals"]},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 6. 汇总: evaluate_answer
# ═══════════════════════════════════════════════════════
def evaluate_answer(question, answer, tool_log=None, language="zh"):
    """五维汇总评估（供运行时审计与测试断言）

    返回: {premise, epistemic, interpretation, evidence, ux, overall, passed_all}
    """
    report = {
        "premise": evaluate_premise_accuracy(question, answer, language=language),
        "epistemic": evaluate_epistemic_accuracy(answer, language=language),
        "interpretation": evaluate_interpretation_quality(question, answer, tool_log, language),
        "evidence": evaluate_evidence(answer, contract=None, tool_log=tool_log, language=language),
        "ux": evaluate_answer_ux(answer, language=language),
    }
    dims = ("premise", "epistemic", "interpretation", "evidence", "ux")
    scores = [report[k]["score"] for k in dims]
    report["overall"] = round(sum(scores) / len(scores), 2)
    report["passed_all"] = all(report[k]["passed"] for k in dims)
    return report


# 供 epistemic 评分复用的强模态（局部兜底, 与生产无耦合）
_STRONG_MODAL = re.compile(r"一定|必然|肯定|必定|毫无疑问|绝对")


# ═══════════════════════════════════════════════════════════════════════
# 以下为评估专用检测启发式（自带副本; O4 后生产引擎不含这些逻辑——
# 原 answer_composer.py / interpretation_engine.py / semantic_obligations.py 已删除,
# 二者对 runtime 只剩 prompt 注入与 done 遥测, 按 O4 delete-first 整体移除;
# 本文件是纯离线评分器, 不在请求路径上, 不对回答产生任何注入/补正/改写效果。）
# ═══════════════════════════════════════════════════════════════════════

# ── 副本 A（原 answer_composer）: 强化措辞 / 回答结构 / 推理噪音检测 ──
FORBIDDEN_STRONG = [
    "完全正确", "绝对正确", "绝对肯定", "毫无疑问", "毫无疑义",
    "本质就是", "本质上就是", "本质上是", "本质即", "说到底就是",
    "绝不会", "绝无可能", "一定是", "必然就是", "必然是", "必定是", "绝对是",
    "唯一正确", "唯一解释", "唯一读法", "唯一可能",
    "definitely", "absolutely", "without a doubt", "completely correct", "essentially the same",
]
_NEGATION_BEFORE = re.compile(r"(并非|不是|未必|不一定|并不|也不|不见得|难说|称不上|算不上)$")

BANNED_DEFAULT_BLOCKS = [
    "材料说明", "先说明材料", "先交代材料", "先说材料", "材料如下", "材料整理如下",
    "工具说明", "检索过程", "检索结果如下", "检索情况",
    "五层报告", "五层分析", "五层结构",
    "再总结", "总结一下刚才", "让我先说明",
]

REASONING_NOISE = [
    "让我检索", "让我读取", "让我查", "让我搜", "让我调用", "让我看看", "让我读一读",
    "我来检索", "我来查", "我来搜", "我先检索", "我先查", "先让我", "让我先",
    "现在我已经有材料", "我已经有材料", "我已经有足够的材料", "我已经查到了",
    "我已经找到了", "我调用了", "我查阅了", "我搜索了", "我检索了", "我读取了",
    "工具返回", "工具结果显示", "检索结果显示", "刚才的工具", "我看了下",
]

_PROCESS_LEADIN = re.compile(
    r"^(让我|我先|好的,?让我|嗯,?让我|等我|我需要先|关于这个问题,?让我|先说明|先交代|"
    r"先看材料|先检索|我检索了|我查了|我调用|我查阅|我搜索|我读取|经过检索|在检索|"
    r"材料说明|工具说明|检索过程|再总结|五层|原典路径)")
_EMPTY_LEADIN = re.compile(r"^(这是一个好问题|这确实是个好问题|好问题|谢谢你的问题|你的问题很有深度|关于(这个|你问的))$")

_CONCLUSION_STACK = ["综上", "总之", "总而言之", "总结", "结论是", "说到底"]


def _strong_hits(answer):
    """强化措辞命中列表（否定词须紧邻命中前才豁免——"并非完全正确"不误伤, "这完全正确"照报）"""
    t = answer or ""
    out = []
    for w in FORBIDDEN_STRONG:
        start = 0
        while True:
            i = t.find(w, start)
            if i < 0:
                break
            if not _NEGATION_BEFORE.search(t[max(0, i - 3):i]):
                out.append(w)
            start = i + len(w)
    return out


def strong_wording_hits(answer):
    """回答中的强化措辞命中（评估套件用; O4 后真源移至本文件）"""
    return _strong_hits(answer)


def _noise_hits(answer):
    return [p for p in REASONING_NOISE if p in (answer or "")]


def _block_hits(answer):
    return [b for b in BANNED_DEFAULT_BLOCKS if b in (answer or "")]


def _first_sentence(text):
    for s in re.split(r"[。！？；!?;\n]+", (text or "").strip()):
        if s.strip():
            return s.strip()
    return ""


def _is_direct(first):
    if not first:
        return False
    if _PROCESS_LEADIN.match(first):
        return False
    if _EMPTY_LEADIN.match(first):
        return False
    return True


def _structure_signals(answer):
    ans = answer or ""
    return {
        "evidence_marker": bool(re.search(r"【《[^》]+》[^】]*】", ans)),
        "reasons_enumerated": bool(re.search(r"(首先|其次|再次|最后|第一|第二|第三|其一|其二|理由[一二三四1234])", ans)),
        "counter_qualification": bool(re.search(r"(但|不过|然而|需要(注意|指出|限定)|另一种|局限|反方|值得怀疑|并非唯一|不一定)", ans)),
        "conclusion_marker": bool(re.search(r"(综上|总之|结论|说到底|因此|可见)", ans)),
    }


def _redundancy_findings(answer):
    """冗余: 归一化后完全重复的句子 / 总结连接词堆叠"""
    out = []
    sents = [s.strip() for s in re.split(r"[。！？；!?;\n]+", answer or "") if s.strip()]
    normed = [re.sub(r"[\s，,、：:]+", "", s) for s in sents]
    seen = {}
    for i, n in enumerate(normed):
        if len(n) >= 12:
            seen.setdefault(n, []).append(i)
    for n, idxs in seen.items():
        if len(idxs) >= 2:
            out.append(f"duplicated_sentence:{sents[idxs[0]][:24]}")
            break
    stack = sum(1 for m in _CONCLUSION_STACK if m in (answer or ""))
    if stack >= 3:
        out.append("conclusion_connector_stack")
    return out


def scan_composition(verdict, answer, language="zh", interpretation_scan=None, budget_scan=None):
    """应答后结构检测（评估用; 无 appends——runtime 不再有任何补正通道）:
    结构信号 / 默认骨架残留 / 强化措辞 / 推理噪音 / 冗余"""
    res = {
        "activated": bool(verdict.get("activated")),
        "direct_judgment": None,
        "structure_signals": {},
        "banned_blocks": [],
        "strong_wording": [],
        "reasoning_noise": [],
        "redundancy": [],
        "appends": [],
    }
    if not res["activated"]:
        return res
    ans = answer or ""
    res["direct_judgment"] = _is_direct(_first_sentence(ans))
    res["structure_signals"] = _structure_signals(ans)
    res["banned_blocks"] = _block_hits(ans)
    res["strong_wording"] = _strong_hits(ans)
    res["reasoning_noise"] = _noise_hits(ans)
    res["redundancy"] = _redundancy_findings(ans)
    return res


# ── 副本 B（原 interpretation_engine）: 解释型问题识别 / 越级断言 / 多候选检测 ──
# 解释性动词/问法（触发"这是解释型问题"的强信号）
_INTERP_VERBS = [
    "意味着", "象征着", "象征", "隐喻", "寓意", "暗示", "解读", "读作", "代表", "体现出",
    "反映出", "反映", "潜台词", "言外之意", "深层含义", "背后的",
    "怎么理解", "如何理解", "作何理解", "怎么解读", "如何解读", "究竟象征", "到底象征",
]
_LITERARY_OBJ = [
    "梦", "梦见", "梦到", "狮子", "老虎", "老人", "小说", "故事", "人物", "主人公", "角色",
    "情节", "文学", "作品", "叙事", "意象", "结尾", "结局", "剧情", "寓言", "童话", "诗歌",
    "戏剧", "小说里", "象征物", "神话",
]
_PHIL_OBJ = [
    "哲学", "思想", "理论", "概念", "观点", "主义", "框架", "意义", "存在", "荒诞", "自由",
    "虚无", "本质", "生命", "精神", "超验", "道德", "灵魂", "世界", "索取", "转化", "态度",
    "目的", "价值", "幸福", "理式", "理性", "意志",
]
_COMPARISON_CUES = [
    "对比", "比较", "异同", "区别", "一样", "相同", "相通", "谁更", "类似", "类比",
    "是不是", "是否", "一不一样", "一回事", "相同点", "不同点", "共通", "契合", "对应", "联系起来",
]
_HISTORY_AMBIGUITY = [
    "众说纷纭", "存在争议", "有争议", "学界", "历来", "悬案", "谜团", "未解之谜",
    "史料不足", "史料缺乏", "无定论", "尚无定论", "解读不一", "分歧", "史家", "历史学家",
]
_HISTORY_OBJ = [
    "历史", "事件", "记载", "史料", "时代", "战争", "时期", "人物", "皇帝", "王朝",
    "起义", "变法", "革命", "辩论", "论战", "生平", "去世",
]
_FRAMED_RE = re.compile(r"从《([^》]{1,40})》[^。！？]{0,24}看")
_EITHER_OR_RE = re.compile(r"是[^。！？]{1,30}还是")

# 跨体系计数: 系统名 → 别名
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

# 四档置信度语言（评估分层用）
TIERS = [
    ("strong", 0.85, "有很强文本依据"),
    ("moderate", 0.65, "相当有力的解释"),
    ("tentative", 0.40, "可成立但并非唯一的解释"),
    ("analogical", 0.0, "更适合作为启发性类比"),
]
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


class InterpretationChallenger:
    """解释型问题识别 + 多候选解读/双面证据/反证尝试的结构要求（评估用副本）

    check(message) → {"activated", "categories", "object", "hypothesis_min",
                      "evidence_requirement", "analogy_guard", "depth_guard"}
    """

    def check(self, message):
        msg = (message or "").strip()
        out = {
            "activated": False,
            "categories": [],
            "object": "",
            "hypothesis_min": 0,
            "evidence_requirement": {"supporting": False, "challenging": False},
            "analogy_guard": False,
            "depth_guard": False,
            "question": msg,
        }
        if not msg:
            return out
        philo = _match_philosopher(msg)
        interp_cue = any(v in msg for v in _INTERP_VERBS) or bool(_FRAMED_RE.search(msg))
        lit_obj = any(v in msg for v in _LITERARY_OBJ)
        phil_obj = any(v in msg for v in _PHIL_OBJ) or bool(philo)
        yn = ("是不是" in msg) or ("是否" in msg) or bool(_EITHER_OR_RE.search(msg))
        concept_hits = [sys_name for sys_name, aliases in CROSS_SYSTEMS.items()
                        if any(a in msg for a in aliases)]
        phil_obj = phil_obj or bool(concept_hits)

        cats = []
        if (len(set(philo)) >= 2 or len(concept_hits) >= 2) and any(c in msg for c in _COMPARISON_CUES):
            cats.append("cross_author_comparison")
        if any(c in msg for c in _HISTORY_AMBIGUITY) and any(c in msg for c in _HISTORY_OBJ):
            cats.append("ambiguous_historical_interpretation")
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


class ConfidenceCalibrator:
    """解释置信度校准（评估用副本; 数字仅内部评分, 不进入任何用户可见流）"""

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
        conf = 0.50
        if sig.get("primary_text_support"):
            conf += 0.15
        if sig.get("direct_quote"):
            conf += 0.10
        if sig.get("scholarly"):
            conf += 0.05
        if sig.get("overclaim"):
            conf -= 0.10
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


def scan_interpretation(verdict, answer, language="zh", tool_log=None):
    """解释型回答检测（评估用; 无 appends——runtime 不再有任何补正通道）:
    候选读法 / 越级断言 / 反证痕迹 / 置信度档位"""
    res = {
        "activated": bool(verdict.get("activated")),
        "categories": verdict.get("categories", []),
        "answer_signals": {},
        "confidence": None, "basis": [], "tier": None,
        "supporting_evidence_present": False,
        "challenging_evidence_trace": "absent",
        "alternatives_offered": False,
        "overclaim": False,
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
        "confidence": calib["confidence"],
        "basis": calib["basis"],
        "tier": calib["tier"],
        "supporting_evidence_present": sig["primary_text_support"] or sig["direct_quote"],
        "challenging_evidence_trace": _challenge_trace(ans, tool_log),
        "alternatives_offered": any(m in ans for m in _ALT_MARKERS),
        "overclaim": sig["overclaim"],
    })
    return res
