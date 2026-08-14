# -*- coding: utf-8 -*-
"""mermaid → draw.io XML 转换器
支持: mindmap（缩进树）/ flowchart TD-LR（节点+边）
确定性转换（不依赖 LLM 再生成）——conceptual_map/辩论演变图可在 draw.io 中继续编辑。
"""
import re, uuid, html

X = 0
Y = 0
NODE_W = 140
NODE_H = 44
LEVEL_W = 190   # 横向层间距
LEVEL_H = 60    # 纵向间距


def _esc(t):
    return html.escape(t or "", quote=True)


def _parse_flowchart(code):
    """解析 flowchart: A[文本] -->|label| B{文本} / A --- B 等"""
    nodes, edges = {}, []
    nid = {}
    def _node_id(key):
        if key not in nid:
            nid[key] = f"n{len(nid) + 1}"
        return nid[key]
    # 节点定义: word[文本] 或 word((文本)) 或 word{文本}
    node_pat = re.compile(r'([A-Za-z0-9_]+)\s*(\[\(?|\{\{?|\[\[|\{\{)\s*"?([^"\]\}]+)"?\s*[\]\}]{1,2}')
    for m in node_pat.finditer(code):
        key, text = m.group(1), m.group(3)
        nodes[key] = {"text": text.strip(), "id": _node_id(key)}
    # 边: A -->|label| B  /  A --> B  /  A --- B（先剥离节点定义文本, 使 A[文本] 变成 A）
    stripped = re.sub(r'\[[^\]]*\]|\{\{[^}]*\}\}|\{[^}]*\}|\(\([^)]*\)\)', '', code)
    edge_pat = re.compile(r'([A-Za-z0-9_]+)\s*--[->]+\s*(?:\|([^|]*)\|)?\s*([A-Za-z0-9_]+)')
    for m in edge_pat.finditer(stripped):
        a, label, b = m.group(1), (m.group(2) or ""), m.group(3)
        if a in nodes and b in nodes:
            edges.append({"from": nodes[a]["id"], "to": nodes[b]["id"], "label": label.strip()})
    return list(nodes.values()), edges


def _parse_mindmap(code):
    """解析 mindmap（缩进层级树）"""
    nodes, edges = [], []
    stack = []   # (depth, node_id)
    for line in code.split("\n"):
        s = line.rstrip()
        if not s.strip():
            continue
        if s.strip().startswith("mindmap"):
            continue
        indent = len(s) - len(s.lstrip())
        depth = indent // 2
        text = s.strip()
        text = re.sub(r"^[-\s]*", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        # 根节点 root((文本))
        m = re.search(r"root\(\((.*)\)\)", text)
        if m:
            text = m.group(1)
        node = {"text": text, "id": f"n{len(nodes) + 1}"}
        nodes.append(node)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if stack:
            edges.append({"from": stack[-1][1], "to": node["id"], "label": ""})
        stack.append((depth, node["id"]))
    return nodes, edges


def _layout(nodes, edges):
    """简单网格布局: 横向分层（BFS 层级）"""
    children = {}
    for e in edges:
        children.setdefault(e["from"], []).append(e["to"])
    roots = [n["id"] for n in nodes if not any(e["to"] == n["id"] for e in edges)] or ([nodes[0]["id"]] if nodes else [])
    level = {}
    for r in roots:
        level[r] = 0
    # BFS
    from collections import deque
    q = deque(roots)
    order = []
    while q:
        cur = q.popleft()
        order.append(cur)
        for c in children.get(cur, []):
            if c not in level:
                level[c] = level[cur] + 1
                q.append(c)
    col_pos = {}
    for nid in order:
        col_pos.setdefault(level[nid], []).append(nid)
    pos = {}
    for lv, ids in col_pos.items():
        for i, nid in enumerate(ids):
            pos[nid] = (20 + lv * LEVEL_W, 20 + i * LEVEL_H)
    return pos


def mermaid_to_drawio(code):
    """mermaid 代码 → draw.io XML"""
    code = code or ""
    if re.search(r"^\s*mindmap\b", code, re.M):
        nodes, edges = _parse_mindmap(code)
    else:
        nodes, edges = _parse_flowchart(code)
    if not nodes:
        return None
    pos = _layout(nodes, edges)
    did = f"d{uuid.uuid4().hex[:8]}"
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for n in nodes:
        x, y = pos.get(n["id"], (20, 20))
        cells.append(
            f'<mxCell id="{n["id"]}" value="{_esc(n["text"])}" style="rounded=1;whiteSpace=wrap;html=1;'
            f'fillColor=#ffffff;strokeColor=#d0d0d5;fontSize=13;arcSize=8;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" as="geometry"/></mxCell>')
    for i, e in enumerate(edges):
        lab = f' value="{_esc(e["label"])}"' if e.get("label") else ""
        cells.append(
            f'<mxCell id="e{i}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;strokeColor=#b0b0b8;'
            f'fontSize=11;html=1;"{lab} edge="1" parent="1" source="{e["from"]}" target="{e["to"]}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>')
    return (
        f'<mxfile><diagram name="page-1" id="{did}">'
        f'<mxGraphModel dx="900" dy="650" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
        f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">'
        f'<root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>')
