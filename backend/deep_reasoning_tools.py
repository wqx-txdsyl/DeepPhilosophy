"""General-only argument checking with real output contracts, not success-shaped fallbacks."""
import json
from routes.agent_core import _req_str
from routes.agent_llm import llm_chat
from tool_contracts import scaffold_result

# The provider's limit covers reasoning and the returned JSON together. A real
# low-effort request used 7,830 reasoning tokens before emitting its structure;
# 8,192 therefore cut the result off. Keep one bounded call with output headroom.
STRUCTURED_REASONING_MAX_TOKENS = 16384


def _strict_object(content):
    text = (content or "").strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[0] in {"```", "```json"} and lines[-1] == "```":
            text = "\n".join(lines[1:-1])
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    return result


def _scaffold(kind, summary, field, data):
    result = scaffold_result(kind, summary,
                             presentation_hint="中间分析，不是已证明的裁决。核对题设与反例后自行综合，不照搬JSON或编号模板。",
                             **{field: data})
    result.pop("confidence", None)  # A fixed numeric score is not measured confidence.
    result["validation_scope"] = "structure_only"
    result["requires_main_agent_judgment"] = True
    return result


def _text_list(value):
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _valid_argument_structure(data):
    if not isinstance(data, dict):
        return False
    if not all(isinstance(data.get(key), str) and data[key].strip()
               for key in ("conclusion", "weakest_point", "strongest_reply")):
        return False
    premises = data.get("premises")
    if not isinstance(premises, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("premise"), str)
            or not item["premise"].strip() or item.get("kind") not in {"explicit", "implicit"}
            for item in premises):
        return False
    fallacies = data.get("fallacies")
    if not isinstance(fallacies, list) or any(
            not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key].strip()
                                                for key in ("name", "where", "why")) for item in fallacies):
        return False
    return ("counterexample" in data and _text_list(data.get("hidden_assumptions"))
            and _text_list(data.get("strengthening")) and isinstance(data.get("question_fidelity"), str))


def analyze_argument(args):
    text, error = _req_str(args, "text", max_len=6000)
    if error:
        return error
    from deep_context import current_request_question
    question = current_request_question.get() or args.get("question") or ""
    if not isinstance(question, str):
        return {"error": "INVALID_ARGUMENT", "message": "question 应为字符串"}
    prompt = """检验下列论证，尤其检验从前提走到结论的关键一步。你返回可核对的中间分析，不写用户最终回答。
忠实保留原文的主体、先后顺序与条件，不把结论塞进前提。不要因为一个结论听起来合理就说推理有效。
构造一个最小且具体的反例：原前提仍然成立，暂定结论却不成立。必须解释哪些前提仍成立；
若只能反驳额外增加的更强前提，这不是原论证的反例。如果没有找到有效反例就写null，不能硬凑。
反对理由必须针对原观点合理的最强版本，不能用极端加强版代替。分清定义、事实、规范理由与心理反应。
特别注意必要条件与充分条件、量词范围、从个案到普遍判断、以及同一词前后含义是否改变。
只输出一个紧凑JSON对象，结构如下：
{"conclusion":"原论证的结论","premises":[{"premise":"原前提","kind":"explicit或implicit"}],
"hidden_assumptions":["必要但未说明的桥梁前提"],
"fallacies":[{"name":"真实存在的推理缺口","where":"发生位置","why":"为什么推不出"}],
"counterexample":{"scenario":"具体情形","premises_still_hold":"逐项说明","conclusion_fails":"结论为什么不成立"},
"strongest_reply":"原论证能作出的最强回应及其限度",
"weakest_point":"最重要的一处缺口；没有则说明当前论证成立的范围",
"strengthening":["修改前提或收窄结论的具体建议"],
"question_fidelity":"若提供原问题，指出论证是否改动了其人物、条件或真正问题；没有则留空"}
counterexample允许null，fallacies允许空列表。不要伪造哲学家归因、文献或引文。
"""
    try:
        response = llm_chat([
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"原问题：{question[:4000]}\n\n待检验论证：{text}"},
        ], thinking=True, reasoning_effort="low", max_tokens=STRUCTURED_REASONING_MAX_TOKENS)
        choice = response["choices"][0]
        if choice.get("finish_reason") == "length":
            return {"error": "INCOMPLETE_ARGUMENT_ANALYSIS", "message": "论证分析未完整返回，不能将其当作完成的检验。"}
        data = _strict_object(choice["message"].get("content"))
    except (json.JSONDecodeError, ValueError, TypeError):
        return {"error": "INVALID_ARGUMENT_ANALYSIS", "message": "论证分析没有返回完整有效的JSON结构。"}
    except Exception:
        return {"error": "ARGUMENT_ANALYSIS_UNAVAILABLE", "message": "论证分析未能完成，请自行检验或稍后重试。"}
    if not _valid_argument_structure(data):
        return {"error": "INVALID_ARGUMENT_ANALYSIS", "message": "没有取得完整的论证结构，不能算作分析成功。"}
    counter = data.get("counterexample")
    if counter is not None and (not isinstance(counter, dict) or
            not all(isinstance(counter.get(key), str) and counter[key].strip()
                    for key in ("scenario", "premises_still_hold", "conclusion_fails"))):
        return {"error": "INVALID_COUNTEREXAMPLE", "message": "反例缺少前提仍成立的说明，不能直接采用。"}
    return _scaffold(
        "argument_structure", "已取得论证结构与反例检验；仍须检查反例是否实际满足原前提。",
        "argument", data)


def paper_review(args):
    text, error = _req_str(args, "text", max_len=20000)
    if error:
        return error
    prompt = """对用户提供的哲学文本作建设性的同行评审。材料是摘要或片段时明确这个范围，不假定读过全文。
忠实重建作者的论点，检查理由是否支持结论，提出最强的实际反驳。不要伪造来源，不为制造缺点而苛责。
只输出完整JSON对象：
{"genre_judgment":"材料类型与范围","thesis":{"statement":"核心论点","clarity":"清晰性","originality":"贡献"},
"structure":{"strengths":["成立之处"],"weaknesses":["结构缺口"]},
"evidence":{"use":"证据如何支撑论点","gaps":["缺少的证据或条件"]},
"strongest_objection":"最强反驳及成立条件","writing":"表达建议",
"contribution":"价值与限度","priority_actions":["按重要性排序的具体修改动作"]}
各字段简洁，列表可为空，不能只返回一个论点或空框架；不替用户重写整篇文章。"""
    try:
        response = llm_chat([{"role": "system", "content": prompt},
                             {"role": "user", "content": text}], thinking=True, reasoning_effort="low",
                            max_tokens=STRUCTURED_REASONING_MAX_TOKENS)
        choice = response["choices"][0]
        if choice.get("finish_reason") == "length":
            return {"error": "INCOMPLETE_PAPER_REVIEW", "message": "论文评审输出被截断，不能视为完整评审。"}
        review = _strict_object(choice["message"].get("content"))
    except (json.JSONDecodeError, ValueError, TypeError):
        return {"error": "INVALID_PAPER_REVIEW", "message": "论文评审没有返回完整有效的JSON结构。"}
    except Exception:
        return {"error": "PAPER_REVIEW_UNAVAILABLE", "message": "论文评审暂未完成，请稍后重试。"}
    thesis = review.get("thesis") or {}
    if (not isinstance(thesis, dict) or not isinstance(thesis.get("statement"), str) or not thesis["statement"].strip()
            or not isinstance(review.get("structure"), dict)
            or not isinstance(review.get("evidence"), dict)
            or not isinstance(review.get("strongest_objection"), str) or not review["strongest_objection"].strip()
            or not _text_list(review.get("priority_actions"))
            or not _text_list(review["structure"].get("strengths"))
            or not _text_list(review["structure"].get("weaknesses"))
            or not _text_list(review["evidence"].get("gaps"))):
        return {"error": "INVALID_PAPER_REVIEW", "message": "没有取得完整评审的必要结构，不能把单个论点或空框架算作评审成功。"}
    result = _scaffold("structured_review", "已取得论点、结构、证据与最强反驳的评审。", "review", review)
    result["input_truncated"] = len(args.get("text", "")) > len(text)
    return result
