"""Bounded locate-to-read completion for the general agent only."""
import re
from research_discipline import ResearchDiscipline, DISCIPLINE_RETRIEVAL_TOOLS, channel_of, _blocked
from agent_runtime import DuplicateGuard, call_fingerprint


def debate_action(args):
    action = str(args.get("action") or "start").strip().lower()
    if action != "start":
        return action
    topic = args.get("topic")
    if not isinstance(topic, str):
        return action
    command = topic.strip().strip("。.!！?？")
    prefix, suffix = r"(?:请|请你|我们)?", r"(?:吧|一下)?"
    if re.fullmatch(prefix + r"(?:继续(?:辩论|讨论)?|下一轮|接着(?:辩论|讨论)?|再来(?:一轮)?|加一轮|第[二三四五六七八九十]轮)" + suffix, command):
        return "continue"
    if re.fullmatch(prefix + r"(?:结束|总结|停止|裁决|收尾)(?:这场|本场|本次)?(?:辩论|讨论)?" + suffix, command):
        return "summary"
    return action


def is_debate_start(tool, args):
    if tool != "philosopher_debate" or debate_action(args) != "start":
        return False
    # The general tool also accepts conversational continuation commands. They
    # are stateful turns, not starts, even when action was omitted by the model.
    topic = args.get("topic") or ""
    if not isinstance(topic, str) or args.get("user_reply"):
        return False
    return True


class DeepDuplicateGuard(DuplicateGuard):
    def __init__(self):
        super().__init__()
        self.debate_starts = {}

    def decide(self, tool, args):
        if is_debate_start(tool, args):
            fingerprint, _ = call_fingerprint(tool, args)
            if fingerprint in self.debate_starts:
                return {"action": "reuse", "cls": "duplicate", "reason": "same debate start",
                        "prev": self.debate_starts[fingerprint]}
        return super().decide(tool, args)

    def record(self, tool, args, ok, result):
        super().record(tool, args, ok, result)
        if ok and is_debate_start(tool, args):
            self.debate_starts[call_fingerprint(tool, args)[0]] = result


class DeepResearchDiscipline(ResearchDiscipline):
    """General tool choices get three initial slots without invented declarations.

    Any declaration attempt restores the explicit protocol. At most two
    identified reads may use the existing reserve; it cannot authorize searches,
    fabricate source IDs, override closed gaps or hard limits.
    """
    def __init__(self, budgets=None):
        super().__init__(budgets)
        self.located_reads = set()
        self.read_reserve = []
        self.tool_choice_admissions = []

    def _tool_choice_open(self):
        return self.active_class is None and not self.declarations and not self.gap_filled

    def _soft_limit(self):
        return 3 if self._tool_choice_open() else super()._soft_limit()

    def gate(self, tool_name):
        if tool_name not in DISCIPLINE_RETRIEVAL_TOOLS:
            return None
        if self.gap_filled:
            return _blocked("EVIDENCE_GAP_FILLED_STOP", "证据缺口已声明闭合，后续检索不再执行。")
        if not self._tool_choice_open():
            return super().gate(tool_name)
        if self.retrieval_executed + self.pending_slots >= self._soft_limit():
            return _blocked("SOFT_BUDGET_REACHED", "尚未声明时的3次起始检索/读取额度已用完；如需继续，请正式登记研究需求及剩余缺口。",
                            {"soft_limit": self._soft_limit(), "executed": self.retrieval_executed})
        return None

    def record_tool_choice_admission(self, tool_name, args, call_id):
        """Record only research-gate admission, before hard admission or execution."""
        if self._tool_choice_open() and tool_name in DISCIPLINE_RETRIEVAL_TOOLS:
            self.tool_choice_admissions.append({"tool": tool_name, "channel": channel_of(tool_name),
                "call_id": call_id, "args_fingerprint": call_fingerprint(tool_name, args)[0],
                "basis": "main_tool_call", "stage": "research_gate_admitted"})

    @staticmethod
    def read_key(tool, args):
        if tool == "get_chapter" and args.get("book_id") and args.get("chapter_idx") is not None:
            return (tool, str(args["book_id"]), str(args["chapter_idx"]))
        if tool == "get_scholarly_source" and args.get("source_record_id"):
            return (tool, str(args["source_record_id"]))
        if tool == "websearch" and isinstance(args.get("url"), str) and args["url"].strip():
            return (tool, args["url"].strip())
        return None

    def record_locations(self, tool, result):
        if not isinstance(result, dict) or result.get("error"):
            return
        if tool == "get_book_detail":
            bid = result.get("book_id") or result.get("id")
            rows = result.get("chapters") or []
            # Only actual explicit chapter indexes are accepted. A legacy toc
            # title's position is not necessarily its physical chapter index.
            items = [{"book_id": bid, "chapter_idx": row.get("chapter_idx", row.get("index"))}
                     for row in rows if isinstance(row, dict)]
        elif tool == "concept_trace":
            items = result.get("timeline") or []
        elif tool == "websearch" and result.get("mode") == "read":
            items = [{"url": result.get(key)} for key in ("url", "requested_url")]
        else:
            items = result.get("results") or []
        for item in items[:1000]:
            if not isinstance(item, dict):
                continue
            if tool in {"search_books", "get_book_detail", "concept_trace"}:
                key = self.read_key("get_chapter", item)
            elif tool == "search_scholarship":
                key = self.read_key("get_scholarly_source", item)
            elif tool == "websearch":
                key = self.read_key("websearch", item)
            else:
                key = None
            if key:
                self.located_reads.add(key)

    def gate_query(self, tool_name, args):
        verdict = super().gate_query(tool_name, args)
        if verdict and verdict.get("error") == "SOFT_BUDGET_REACHED":
            key = self.read_key(tool_name, args)
            reservation = call_fingerprint(tool_name, args)[0]
            # A second window of the same identified chapter is a real read,
            # not a fabricated new source. Exact repetitions are handled by
            # DuplicateGuard; the reserve still caps actual new reads at two.
            if key in self.located_reads and len(self.read_reserve) < 2 and reservation not in self.read_reserve:
                self.read_reserve.append(reservation)
                return None
        return verdict

    def snapshot(self):
        return {**super().snapshot(), "read_reserve_used": len(self.read_reserve),
                "read_reserve_limit": 2, "tool_choice_limit": 3,
                "tool_choice_admissions": list(self.tool_choice_admissions)}
