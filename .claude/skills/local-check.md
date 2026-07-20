---
name: local-check
description: Local Check
---
# Local Check

## 核心执行协议
- **模式**：顺序执行，每步带检查-补全-验证闭环。
- **检查模式**：READ_ONLY — 仅诊断，不修改源文件。问题汇总到执行报告。
- **变量替换规则**：无（不接受参数）
- **标记格式**：[ISSUE:description]

## 前置依赖
- Node.js, Python 3, curl, 项目已构建过

## 状态初始化
> TodoWrite: 构建 哲人图片 流派背景 死代码 API响应 文件大小

## 原子步骤

### 步骤 1：构建
- **动作**：cd app && npm run build && rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist
- **门禁**：test -f app/dist/index.html || echo [ISSUE:BUILD_FAILED]

### 步骤 2：哲人图片（599张）
- **动作**：python -c "import os,json; p=json.load(open("backend/data/philosophers.json",encoding="utf-8")); imgs=set(os.path.splitext(f)[0] for f in os.listdir("app/public/philosopher") if f.endswith(".jpg")); m=[n for n in p if n.replace("/","-").replace(":","：") not in imgs]; print(f"[ISSUE:{len(m)}_MISSING_IMAGES]" if m else "ALL OK")"

### 步骤 3：流派背景图
- **动作**：python -c "import os,re; c=open("app/src/pages/SchoolDetailPage.jsx",encoding="utf-8").read(); refs=set(re.findall(r"bg:'url\(/schools/([^)]+)\)",c)); imgs=set(f for f in os.listdir("app/public/schools") if f.endswith(".jpg")); m=refs-imgs; print(f"[ISSUE:{len(m)}_MISSING_BG]" if m else "ALL OK")"

### 步骤 4：死代码
- **动作**：test -f app/src/pages/_new_schools_data.jsx && echo [ISSUE:DEAD_FILE]; ls app/public/schools/school_*.json 2>/dev/null && echo [ISSUE:STALE_JSONS]

### 步骤 5：API 响应
- **动作**：cd backend && python main.py & sleep 4; curl -s http://localhost:8000/api/health | grep -q ok && echo API_OK || echo [ISSUE:API_DOWN]; kill %1 2>/dev/null

### 步骤 6：文件大小
- **动作**：sz=2600546; [  -ge 2000000 ] && echo SIZE_OK || echo [ISSUE:SDP_TOO_SMALL]

## 执行报告
- ISSUES 总数：N（0 = CLEAN）