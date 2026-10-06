"""Offline rubric arithmetic, protocol validation and preregistered checks.

No provider calls. Never converts invalid grades to valid ones or alters raw records.
Run: python3 docs/evidence/rubric_v1_2/validate.py
"""
import hashlib
import json
import unittest
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = Path(__file__).resolve().parent
RULES = json.loads((BASE / "RULES_FROZEN.json").read_text())


def score(family, ratings, errors=None):
    if family not in {"C", "R", "K"}:
        raise ValueError("unknown task family")
    layers = ["K"] if family == "K" else ["C", "R"] if family == "R" else ["C"]
    expected = {k for layer in layers for k in RULES[layer]}
    if set(ratings) != expected:
        raise ValueError("missing or extra rating keys")
    maximum = 1 if family == "K" else 4
    if any(v != "U" and (type(v) is not int or not 0 <= v <= maximum) for v in ratings.values()):
        raise ValueError("invalid ordinal rating; never rescale provider output")
    totals = {}
    for layer in layers:
        values = {k: ratings[k] for k in RULES[layer]}
        totals[layer] = None if "U" in values.values() else (
            sum(values.values()) if layer == "K" else
            sum(Decimal(RULES[layer][k]["weight"]) * v / 4 for k, v in values.items()))
    numeric = all(v is not None for v in totals.values())
    errors = errors or []
    for error in errors:
        if error.get("code") not in RULES["errors"] or error.get("status") not in {"pending", "confirmed"}:
            raise ValueError("invalid serious error")
        if not error.get("answer_span") or not error.get("reference_or_condition"):
            raise ValueError("serious errors need evidence")
    passed = numeric and not errors
    if passed:
        if family == "K":
            passed = totals["K"] == 4
        else:
            passed = totals["C"] >= 45 and all(ratings[k] >= 3 for k in ["C1", "C2", "C3"])
            if family == "R":
                passed = passed and totals["R"] >= 30 and all(ratings[k] >= 3 for k in RULES["R"])
    return {
        "exact": {k: None if v is None else float(v) for k, v in totals.items()},
        "display": {k: None if v is None else int(Decimal(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) for k, v in totals.items()},
        "verdict": "unresolved" if not numeric or any(e["status"] == "pending" for e in errors) else "pass" if passed else "fail",
    }


class ArithmeticTests(unittest.TestCase):
    def test_general_is_sixty_not_hundred(self):
        self.assertEqual(score("C", dict.fromkeys(RULES["C"], 4))["exact"], {"C": 60})

    def test_research_layers_separate(self):
        self.assertEqual(score("R", dict.fromkeys([*RULES["C"], *RULES["R"]], 4))["exact"], {"C": 60, "R": 40})

    def test_unknown_withholds_layer(self):
        grades = dict.fromkeys([*RULES["C"], *RULES["R"]], 4)
        grades["R2"] = "U"
        result = score("R", grades)
        self.assertEqual(result["exact"], {"C": 60, "R": None})
        self.assertEqual(result["verdict"], "unresolved")

    def test_zero_is_not_unknown(self):
        result = score("C", dict.fromkeys(RULES["C"], 0))
        self.assertEqual(result["exact"], {"C": 0})
        self.assertEqual(result["verdict"], "fail")

    def test_missing_or_extra_fields_rejected(self):
        for grades in [{}, {**dict.fromkeys(RULES["C"], 4), "R1": 4}]:
            with self.assertRaises(ValueError):
                score("C", grades)

    def test_invalid_values_rejected(self):
        for value in [True, 2.5, "3", -1, 5, None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                score("C", {**dict.fromkeys(RULES["C"], 4), "C1": value})

    def test_core_cannot_be_compensated(self):
        self.assertEqual(score("C", {**dict.fromkeys(RULES["C"], 4), "C2": 2})["verdict"], "fail")

    def test_research_cannot_be_compensated(self):
        grades = dict.fromkeys([*RULES["C"], *RULES["R"]], 4)
        self.assertEqual(score("R", {**grades, "R3": 2})["verdict"], "fail")

    def test_k_binary_only(self):
        self.assertEqual(score("K", dict.fromkeys(RULES["K"], 1))["exact"], {"K": 4})
        with self.assertRaises(ValueError):
            score("K", dict.fromkeys(RULES["K"], 4))

    def test_serious_errors_override_scores(self):
        error = {"code": "E2", "status": "confirmed", "answer_span": "x", "reference_or_condition": "y"}
        self.assertEqual(score("C", dict.fromkeys(RULES["C"], 4), [error])["verdict"], "fail")
        self.assertEqual(score("C", dict.fromkeys(RULES["C"], 4), [{**error, "status": "pending"}])["verdict"], "unresolved")

    def test_no_evidence_error_rejected(self):
        with self.assertRaises(ValueError):
            score("C", dict.fromkeys(RULES["C"], 4), [{"code": "E1", "status": "confirmed"}])

    def test_display_rounding_not_used_for_pass(self):
        self.assertEqual(score("C", {"C1": 3, "C2": 3, "C3": 3, "C4": 2, "C5": 3})["display"]["C"], 43)


def validate_records():
    key = json.loads((BASE / "BLIND_KEY.json").read_text())
    packets = json.loads((BASE / "BLIND_PACKETS.json").read_text())
    answers = {a["id"]: (p, a) for p in packets for a in p["answers"]}
    records, invalid = {}, {}
    for path in sorted((BASE / "review_round2").glob("*.provider.json")):
        name = path.name.removesuffix(".provider.json")
        request = json.loads(path.with_name(name + ".request.json").read_text())
        payload = json.loads(request["messages"][1]["content"])
        family = payload["task"]["family"]
        try:
            response = json.loads(path.read_text())
            if response["choices"][0].get("finish_reason") == "length":
                raise ValueError("truncated")
            row = json.loads(response["choices"][0]["message"]["content"])
            if row["answer_id"] != payload["answer"]["id"]:
                raise ValueError("wrong answer id")
            result = score(family, row["ratings"], row["errors"])
            if set(row["reasons"]) != set(row["ratings"]):
                raise ValueError("reason keys differ from rating keys")
            compact = lambda s: "".join(s.split())
            if any(compact(e["answer_span"]) not in compact(payload["answer"]["answer"]) for e in row["errors"]):
                raise ValueError("error anchor not literal")
            records[name] = {"task": payload["task"]["id"], "family": family, "ratings": row["ratings"], **result}
        except (ValueError, KeyError, TypeError) as exc:
            invalid[name] = str(exc)

    def by_role(task, role):
        return next((records.get(k) for k, v in key[task].items() if v == role), None)

    def check(items):
        return {"status": "fail" if any(x is False for x in items.values()) else "blocked" if any(x is None for x in items.values()) else "pass", "cases": items}

    critical, positive, brevity, position = {}, {}, {}, {}
    for task in key:
        fault = by_role(task, "fault")
        critical[task] = None if fault is None else fault["verdict"] == "fail" and any(
            v <= (0 if fault["family"] == "K" else 2) for k, v in fault["ratings"].items()
            if k in {"C1", "C2", "C3", "R1", "R2", "K1", "K2", "K3", "K4"} and v != "U")
        for role in ["reference", "concise"]:
            row = by_role(task, role)
            positive[task + ":" + role] = None if row is None else row["verdict"] == "pass"
        ref, short = by_role(task, "reference"), by_role(task, "concise")
        brevity[task] = None if ref is None or short is None else all(abs(ref["exact"][layer] - short["exact"][layer]) <= limit for layer, limit in ({"K": 0} if ref["family"] == "K" else {"C": 6, **({"R": 4} if ref["family"] == "R" else {})}).items())
    ref, repeat = by_role("T2", "reference"), by_role("T2", "repetitive")
    verbosity = None if ref is None or repeat is None else all(repeat["exact"][layer] - ref["exact"][layer] <= 3 for layer in ["C", "R"])
    ref, other = by_role("T5", "reference"), by_role("T5", "other_position")
    position["T5"] = None if ref is None or other is None else other["verdict"] == "pass" and abs(ref["exact"]["C"] - other["exact"]["C"]) <= 6
    retests = {}
    for aid in key["T3"]:
        a, b = records.get(aid), records.get("retest-" + aid)
        retests[aid] = None if a is None or b is None else a["verdict"] == b["verdict"] and all(abs(a["exact"][layer] - b["exact"][layer]) <= 6 for layer in ["C", "R"])
    human, ai = records.get("author-human"), records.get("author-ai")
    author = None if human is None or ai is None else human["verdict"] == ai["verdict"] and abs(human["exact"]["C"] - ai["exact"]["C"]) <= 3
    checks = {"critical_sensitivity": check(critical), "good_and_concise": check(positive), "brevity_gap": check(brevity), "verbosity_gain": check({"T2": verbosity}), "position_fairness": check(position), "order_probe": check(retests), "author_label_probe": check({"same_answer": author})}
    prereg = json.loads((BASE / "PREREGISTRATION.json").read_text())
    hashes = {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest() == digest for name, digest in prereg["files"].items()}
    candidate = json.loads((BASE / "RULES_CANDIDATE.json").read_text())
    frozen_matches_candidate = all(RULES[k] == v for k, v in candidate.items() if k != "status")
    if not frozen_matches_candidate:
        raise ValueError("frozen numerical rules or criteria changed after calibration")
    providers = list((BASE / "review_round1").glob("*.provider.json")) + list((BASE / "review_round2").glob("*.provider.json"))
    usage = {"requests_with_response": len(providers), "total_tokens": sum(json.loads(p.read_text()).get("usage", {}).get("total_tokens", 0) for p in providers)}
    result = {"interpretation": "Synthetic control calibration only; invalid results are not repaired, rescaled or silently counted as passing.", "preregistration_hashes": hashes, "frozen_rules_match_candidate": frozen_matches_candidate, "checks": checks, "accepted_round2": len(records), "invalid_round2": invalid, "records": records, "usage": usage, "automated_evaluator_accepted": all(c["status"] == "pass" for c in checks.values()) and all(hashes.values())}
    (BASE / "VALIDATION_RESULTS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    tests = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ArithmeticTests))
    if not tests.wasSuccessful():
        raise SystemExit(1)
    result = validate_records()
    print(json.dumps({"unit_tests": tests.testsRun, "checks": {k: v["status"] for k, v in result["checks"].items()}, "accepted_round2": result["accepted_round2"], "invalid_round2": result["invalid_round2"], "automated_evaluator_accepted": result["automated_evaluator_accepted"]}, ensure_ascii=False, indent=2))
