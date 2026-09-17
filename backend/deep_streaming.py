"""Presentation-only helpers for the general agent; persona paths stay unchanged."""
import re

_EMOJI = re.compile(
    r"[0-9#*]\ufe0f?\u20e3|"
    r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u231a\u231b\u23e9-\u23f3\u23f8-\u23fa\ufe0e\ufe0f\u200d]"
)


def clean_public_text(text):
    return _EMOJI.sub("", text or "")


def wants_suggestions(message):
    """Honor explicit requests to omit follow-ups, without classifying question intent."""
    return not re.search(
        r"(?:不要|不需要|无需|别|不加|不附|不提供)[^。！？;；\n，,]{0,40}"
        r"(?:追问|延伸|后续|建议|推荐)|"
        r"(?:no|without|do not|don't)\s+(?:(?:add(?:ing)?|includ(?:e|ing)|giv(?:e|ing)|offer(?:ing)?|any|more)\s+)*"
        r"(?:follow[- ]?ups?|suggestions?|further questions)",
        message or "", re.I)


def complete_paragraph_prefix(text):
    """Return a closed paragraph boundary, holding unfinished markup and quotes."""
    boundary = text.rfind("\n\n")
    if boundary < 0:
        return ""
    prefix = text[:boundary + 2]
    if prefix.count("```") % 2 or prefix.count("~~~") % 2:
        return ""
    if prefix.count("`") % 2:
        return ""
    for left, right in (("“", "”"), ("「", "」"), ("『", "』"), ("【", "】")):
        if prefix.count(left) != prefix.count(right):
            return ""
    if len(re.findall(r'(?<!\\)"', prefix)) % 2:
        return ""
    if prefix.rstrip().splitlines()[-1].lstrip().startswith(">"):
        return ""  # A trailing source label can still belong to this quotation.
    return prefix


class PublicNoteParser:
    """Stream only explicitly public rationale, never provider reasoning fields.

    Partial tags are held across arbitrary transport boundaries. An unfinished
    note is never reclassified as the final answer at EOF.
    """
    opening = "<rationale>"
    closing = "</rationale>"

    def __init__(self, max_note=600):
        self.buf = ""
        self.in_note = False
        self.note_chars = 0
        self.max_note = max_note

    def push(self, text):
        self.buf += text
        prose, notes = [], []
        while self.buf:
            marker = self.closing if self.in_note else self.opening
            pos = self.buf.find(marker)
            if pos >= 0:
                body, self.buf = self.buf[:pos], self.buf[pos + len(marker):]
                self._append(body, prose, notes)
                self.in_note = not self.in_note
                if self.in_note:
                    self.note_chars = 0
                continue
            hold = next((n for n in range(min(len(marker) - 1, len(self.buf)), 0, -1)
                         if self.buf.endswith(marker[:n])), 0)
            body = self.buf[:-hold] if hold else self.buf
            self.buf = self.buf[-hold:] if hold else ""
            self._append(body, prose, notes)
            break
        return "".join(prose), notes

    def _append(self, body, prose, notes):
        if self.in_note:
            shown = clean_public_text(body[:max(0, self.max_note - self.note_chars)])
            self.note_chars += len(body)
            if shown:
                notes.append(shown)
        else:
            prose.append(body)

    def finish(self):
        tail = "" if self.in_note or self.opening.startswith(self.buf) else self.buf
        self.buf = ""
        self.in_note = False
        return tail


class AnswerEnvelopeParser:
    """Separate an explicitly terminal answer from model work notes.

    Legacy unwrapped model responses remain supported, but are held for the
    whole-answer validator. Only an explicit opening opts in to early delivery.
    """
    def __init__(self):
        self.buf = ""
        self.opened = False
        self.closed = False

    def push(self, text):
        if self.closed:
            return ""
        self.buf += text
        if not self.opened:
            pos = self.buf.find("<answer>")
            if pos < 0:
                return ""  # May still be a legacy answer or a plain work note.
            self.buf = self.buf[pos + len("<answer>"):]
            self.opened = True
        out = []
        while self.buf:
            marker = "</answer>" if self.opened else "<answer>"
            pos = self.buf.find(marker)
            repeat = self.buf.find("<answer>")
            if repeat >= 0 and (pos < 0 or repeat < pos):
                raise ValueError("ANSWER_ENVELOPE_ERROR")
            if pos >= 0:
                out.append(self.buf[:pos])
                self.buf = self.buf[pos + len(marker):]
                if self.opened:
                    self.closed = True
                    self.buf = ""
                    break
                self.opened = True
                continue
            hold = max((n for tag in (marker, "<answer>")
                        for n in range(1, min(len(tag) - 1, len(self.buf)) + 1)
                        if self.buf.endswith(tag[:n])), default=0)
            out.append(self.buf[:-hold] if hold else self.buf)
            self.buf = self.buf[-hold:] if hold else ""
            break
        return "".join(out)

    def finish(self):
        tail, self.buf = self.buf, ""
        return "" if tail.startswith("<") else tail


def tool_status(result, budget_class="", reused=False):
    if budget_class in {"discipline_blocked", "ceiling"}:
        return "blocked"
    if isinstance(result, dict) and (result.get("error") or result.get("accepted") is False):
        return "error"
    if reused or budget_class == "duplicate":
        return "reused"
    if isinstance(result, dict):
        for key in ("results", "items", "sources", "books", "timeline"):
            if key in result and result[key] == []:
                return "empty"
    return "success"


def public_tool_summary(name, result, status, language="zh"):
    en = language == "en"
    if status == "blocked":
        return "This call did not run." if en else "本次调用未执行。"
    if status == "error":
        return "The tool could not complete this request." if en else "这一步未能完成。"
    if status == "empty":
        return "No matching material was found." if en else "未找到匹配的材料。"
    if status == "reused":
        return "Reused the result already retrieved." if en else "已复用本轮取得的结果。"
    if name == "get_chapter":
        return "Chapter text retrieved." if en else "已读取章节原文。"
    if isinstance(result, dict):
        for key in ("results", "items", "sources", "books"):
            if isinstance(result.get(key), list):
                n = len(result[key])
                return f"Returned {n} candidates." if en else f"返回 {n} 条候选材料。"
    return "Completed." if en else "已完成。"
