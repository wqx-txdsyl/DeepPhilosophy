"""General-only mechanical checks for success-shaped empty tool artifacts.

These checks do not judge a position, topic, argument's truth or writing quality.
They inspect each tool's actual content fields and exact built-in fallback
signatures. Valid results are returned untouched; callers install this gate
inside the tool function so a state transaction can roll back a failed artifact.
"""
import re


CHECKED_TOOLS = frozenset({
    "compare_views", "advisor_council", "dialectic", "confrontation",
    "socratic_tutor", "thought_experiment", "philosopher_debate", "write_essay", "agent_council",
})
_MOVEMENT_FIELDS = (
    "initial_concept", "internal_tension", "self_negation", "transformation",
    "new_determination", "residual_tension",
)
_DIALECTIC_FAILURE = "辩证运动生成失败——请主 Agent 直接自行剖析"
_ESSAY_FAILURES = frozenset({"（生成失败，请重试）", "（修改失败，请重试）"})
_COUNCIL_FAILURE_PREFIXES = {
    "deep": "（深哲发言失败: ",
    "nietzsche": "（尼采发言失败: ",
    "synthesis": "（综合失败: ",
}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _rows(value):
    return value if isinstance(value, list) else []


def _has_row(value, *fields):
    return any(isinstance(row, dict) and all(_text(row.get(field)) for field in fields)
               for row in _rows(value))


def _speech(value):
    if not isinstance(value, str):
        return False
    # The actual debate tool prefixes every speech with a speaker and colon.
    # No minimum length: an actual one-word reply is still a delivered reply.
    parts = re.split(r"[:：]", value, maxsplit=1)
    return _text(parts[-1])


def validate_general_result(name, args, result):
    """Return the original artifact or an explicit failure with missing fields.

    Unknown tools (including all retrieval tools) and existing errors pass
    through. This function is installed only in the general tool registry.
    """
    if name not in CHECKED_TOOLS:
        return result
    if isinstance(result, dict) and (result.get("error") or result.get("accepted") is False):
        return result
    missing = []
    if not isinstance(result, dict):
        missing = ["result"]
    elif name == "compare_views":
        delivered = (
            _has_row(result.get("comparison_axes"), "axis", "side_a", "side_b")
            or (_has_row(result.get("side_a_claims"), "claim")
                and _has_row(result.get("side_b_claims"), "claim"))
            or _text(result.get("strongest_divergence"))
        )
        if not delivered:
            missing = ["comparison_axes / paired_claims / strongest_divergence"]
    elif name == "advisor_council":
        if not _has_row(_mapping(result.get("council")).get("perspectives"), "advisor", "advice"):
            missing = ["council.perspectives"]
    elif name == "agent_council":
        council = _mapping(result.get("council"))
        for member, prefix in _COUNCIL_FAILURE_PREFIXES.items():
            speech = council.get(member)
            if (not _text(speech)
                    or re.fullmatch(re.escape(prefix) + r".*）", speech.strip(), flags=re.S)):
                missing.append("council." + member)
    elif name == "dialectic":
        movement = _mapping(result.get("movement"))
        if not any(_text(movement.get(key)) and movement[key].strip() != _DIALECTIC_FAILURE
                   for key in _MOVEMENT_FIELDS):
            missing = ["movement"]
    elif name == "confrontation":
        missing = [f"{side}.text" for side in ("stance_a", "stance_b")
                   if not _text(_mapping(result.get(side)).get("text"))]
    elif name == "socratic_tutor":
        question = result.get("next_question")
        # Match the entire known fallback signature, not an ordinary short
        # question or any occurrence of failure-related vocabulary.
        fallback = (isinstance(question, str)
                    and question.strip() == "你说这话时, 心里把它当作什么?"
                    and not _text(result.get("diagnosed_assumption"))
                    and result.get("question_purpose") == "暴露隐含前提")
        if not _text(question) or fallback:
            missing = ["next_question"]
    elif name == "thought_experiment":
        if not _text(result.get("setting")):
            missing.append("setting")
        if not (_has_row(result.get("stance_projections"), "stance", "projection")
                or _text(result.get("revealed_problem"))):
            missing.append("stance_projections / revealed_problem")
    elif name == "philosopher_debate":
        if "debate_summary" in result:
            if not _text(result.get("debate_summary")):
                missing = ["debate_summary"]
        else:
            speeches = _rows(result.get("debate"))
            if not speeches:
                missing = ["debate"]
            else:
                missing = [f"debate[{index}]" for index, speech in enumerate(speeches) if not _speech(speech)]
    elif name == "write_essay":
        essay = result.get("essay")
        if not _text(essay) or essay.strip() in _ESSAY_FAILURES:
            missing = ["essay"]
    if missing:
        failure = {"error": "INCOMPLETE_TOOL_RESULT", "tool": name,
                   "message": "工具未返回可用的完整产物，不能记为已完成；请基于已有材料继续或重试。",
                   "missing_fields": missing}
        if name == "agent_council" and isinstance(result, dict):
            # Keep actual successful speeches and the shared tool's explicit
            # per-member failures; partial work must not masquerade as a complete council.
            return {**result, **failure, "partial": len(missing) < len(_COUNCIL_FAILURE_PREFIXES)}
        return failure
    return result
