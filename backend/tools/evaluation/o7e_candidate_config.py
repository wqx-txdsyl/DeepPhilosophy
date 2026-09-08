# -*- coding: utf-8 -*-
"""O7-E Bakeoff V2.1 §1: 候选配置单一真源（Stage A/B 共用 build_candidate_client）。"""
import json
import os

ROOT = ospath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_MANIFEST = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7E_BAKEOFF_V2_CANDIDATES.json")


class BakeoffCandidateConfig:
    def __init__(self, candidate_id, provider, base_url, requested_model,
                 normal_temperature, normal_max_tokens, normal_thinking,
                 normal_reasoning_effort, repair_temperature, repair_max_tokens,
                 repair_thinking, repair_reasoning_effort, envkey,
                 production_deployable=True, general_api=True):
        self.candidate_id = candidate_id
        self.provider = provider
        self.base_url = base_url
        self.requested_model = requested_model
        self.normal = {"temperature": normal_temperature,
                       "max_tokens": normal_max_tokens,
                       "thinking": normal_thinking,
                       "reasoning_effort": normal_reasoning_effort}
        self.repair = {"temperature": repair_temperature,
                       "max_tokens": repair_max_tokens,
                       "thinking": repair_thinking,
                       "reasoning_effort": repair_reasoning_effort}
        self.envkey = envkey
        self.production_deployable = production_deployable
        self.general_api = general_api

    def api_key(self):
        for l in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
            if l.startswith(self.envkey + "="):
                return l.split("=", 1)[1].strip().strip('"').strip("'")
        return None


# V2.1 §3: v4-pro 冻结 normal + 两个 repair 配置（RP-A thinking on / RP-B off）
V4PRO_NORMAL = dict(temperature=0.7, max_tokens=8000, thinking="enabled",
                    reasoning_effort="low")
RP_A = dict(temperature=0, max_tokens=8000, thinking="enabled", reasoning_effort="low")
RP_B = dict(temperature=0, max_tokens=8000, thinking="disabled", reasoning_effort=None)


def v4pro_config(repair_cfg):
    c = BakeoffCandidateConfig(
        candidate_id=f"deepseek-v4-pro@{repair_cfg['id']}",
        provider="deepseek", base_url="https://api.deepseek.com",
        requested_model="deepseek-v4-pro",
        normal_temperature=V4PRO_NORMAL["temperature"],
        normal_max_tokens=V4PRO_NORMAL["max_tokens"],
        normal_thinking=V4PRO_NORMAL["thinking"],
        normal_reasoning_effort=V4PRO_NORMAL["reasoning_effort"],
        repair_temperature=repair_cfg["temperature"],
        repair_max_tokens=repair_cfg["max_tokens"],
        repair_thinking=repair_cfg["thinking"],
        repair_reasoning_effort=repair_cfg["reasoning_effort"],
        envkey="DEEPSEEK_API_KEY")
    return c


def build_candidate_client(cfg, mode):
    """按候选配置构建 raw-HTTP 调用器（mode: normal|repair）。

    返回 fn(messages) -> dict{content, response_model, finish_reason,
    content_chars, reasoning_chars, config_echo}。零 reasoning 内容存储。"""
    import urllib.request
    m = cfg.normal if mode == "normal" else cfg.repair

    def call(messages):
        payload = {"model": cfg.requested_model, "temperature": m["temperature"],
                   "max_tokens": m["max_tokens"], "messages": messages}
        if cfg.provider == "deepseek":
            body = {}
            if m.get("thinking"):
                body["thinking"] = {"type": m["thinking"]}
                if m.get("reasoning_effort"):
                    body["reasoning_effort"] = m["reasoning_effort"]
            elif m.get("thinking") == "disabled":
                body["thinking"] = {"type": "disabled"}
            if body:
                payload["extra_body"] = None
                del payload["extra_body"]
                payload.update(body)
        req = urllib.request.Request(
            cfg.base_url + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + (cfg.api_key() or "")})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read())
        msg = d["choices"][0]["message"]
        return {"content": msg.get("content") or "",
                "response_model": d.get("model"),
                "finish_reason": d["choices"][0].get("finish_reason"),
                "content_chars": len(msg.get("content") or ""),
                "reasoning_chars": len(msg.get("reasoning_content") or ""),
                "config_echo": {"requested_model": cfg.requested_model,
                                "temperature": m["temperature"],
                                "max_tokens": m["max_tokens"],
                                "thinking": m.get("thinking"),
                                "reasoning_effort": m.get("reasoning_effort")}}
    return call
