---
name: add-skill
description: Add Skill — 创建新 Skill 的 Skill（元 Skill）
---
# Add Skill — 创建新 Skill 的 Skill（元 Skill）

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_NAME` = 新 skill 名（kebab-case）；`ARG_SCRIPT` = 对应可执行脚本路径；`ARG_DEPS` = 前置依赖列表
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- 无外部依赖（仅需文件写入权限）

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：需求分析 — 确定 skill 类型和步骤
- [ ] 步骤 2：文件生成 — 按模板写入 `.claude/skills/ARG_NAME.md`
- [ ] 步骤 3：模板合规检查 — 验证所有必填章节
- [ ] 步骤 4：脚本关联 — 确认 ARG_SCRIPT 存在或标记待创建
- [ ] 步骤 5：交叉引用更新 — 更新相关 skill 的引用

## Skill 模板（必须包含的章节）

### 1. 标题
```markdown
# Skill Name
```

### 2. 核心执行协议
```markdown
## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败才报错并**回滚/标记**（而非直接退出）。
- **变量替换规则**：列出所有 ARG_xxx 变量及其含义
- **标记格式**：[SKIPPED:reason] / [WARN:reason]
```

### 3. 前置依赖
```markdown
## 前置依赖
- 列出所有必需的脚本、API Key、Python 包
```

### 4. 状态初始化（TodoWrite）
```markdown
## 状态初始化
> TodoWrite:
- [ ] 步骤 1：xxx
- [ ] 步骤 2：xxx
```

### 5. 原子步骤（每个步骤必须包含以下 4 段）
```markdown
### 步骤 X：[动作名]
- **动作**：可执行的 Shell/Python 命令
- **门禁验证（Check）**：检查产物是否存在/达标
- **补全分支（Remediate）**：若验证失败，执行具体补全命令（最多 2 次）
- **失败上限**：2 次后标记 [SKIPPED:reason] 或 [WARN:reason]，继续后续非依赖步骤
```

### 6. 执行报告
```markdown
## 执行报告（必须输出）
- 成功项：X 条
- 补全项：Y 条（列出：{项目名} -> 补全动作 -> 最终状态）
- 失败跳过项：Z 条（列出：{项目名} -> 失败原因，格式 [SKIPPED:reason]）
```

## 原子步骤

### 步骤 1：需求分析
- **动作**：向用户确认以下信息：
  1. Skill 名称（英文 kebab-case）
  2. 该 skill 完成什么任务
  3. 涉及哪些脚本/API
  4. 有几个步骤，每步验证什么
- **门禁验证（Check）**：所有问题已得到明确回答。
- **补全分支（Remediate）**：模糊处主动推断并标注 `[ASSUMED]`，请用户确认。

### 步骤 2：文件生成
- **动作**：按模板写入文件。
- **门禁验证（Check）**：
```bash
python -c "
import os; p='.claude/skills/ARG_NAME.md'
assert os.path.exists(p), '[SKIPPED:FILE_NOT_CREATED]'
with open(p,encoding='utf-8') as f: content=f.read()
# Check all required sections
required=['核心执行协议','前置依赖','状态初始化','原子步骤','执行报告']
missing=[s for s in required if s not in content]
assert not missing, f'MISSING SECTIONS: {missing}'
print(f'{p}: {len(content)} chars, all sections present')
"
```
- **补全分支（Remediate）**：缺失章节 -> 补充后重新验证。

### 步骤 3：模板合规检查
- **动作**：逐项核对：
  - [ ] 变量替换规则是否列出所有 `ARG_xxx`
  - [ ] 补全分支是否包含可执行命令（非描述性文字）
  - [ ] 门禁验证是否包含 `os.path.exists` 或 `assert`
  - [ ] 失败上限是否明确（2 次 + 标记格式）
  - [ ] 执行报告格式是否正确
  - [ ] 产物路径是否完整
- **门禁验证（Check）**：
```bash
python -c "
with open('.claude/skills/ARG_NAME.md',encoding='utf-8') as f: c=f.read()
checks=[]
checks.append(('变量替换', 'ARG_' in c))
checks.append(('可执行补全', '```bash' in c or '```python' in c))
checks.append(('门禁验证', 'os.path.exists' in c or 'assert' in c))
checks.append(('失败上限', '2 次' in c or '重试' in c))
checks.append(('执行报告', '成功项' in c or '补全项' in c))
for n,ok in checks: print(f'  [{\"PASS\" if ok else \"FAIL\"}] {n}')
if all(ok for _,ok in checks): print('TEMPLATE OK')
"
```
- **补全分支（Remediate）**：不合规项 -> 手动修正。

### 步骤 4：脚本关联
- **动作**：如果 skill 引用了脚本，确认脚本存在：
```bash
test -f "scripts/ARG_SCRIPT" && echo "SCRIPT EXISTS" || echo "[SKIPPED:SCRIPT_NOT_FOUND - will need creation]"
```
- **补全分支（Remediate）**：脚本不存在 -> 在 skill 的补全分支中使用内联 Python/Shell 代替，或标记 `[TODO:CREATE_SCRIPT]`。

### 步骤 5：交叉引用更新
- **动作**：如果新 skill 与现有 skill 功能重叠，更新相关 skill：
  - 在重叠 skill 的"前置依赖"或"补全分支"中添加交叉引用
  - 如果是合并关系，将被合并方改为瘦入口（参考 `school-bg-gen.md` -> `agnes-image.md`）
- **门禁验证（Check）**：`grep -r "ARG_NAME" .claude/skills/ | wc -l` 确认引用数 >= 1。

## 关键规则速查

| 规则 | 说明 |
|------|------|
| bio/摘要字数 | 循环生成直到 `len >= X`，最多 2 次，失败标记 `[WARN:SHORT_xxx]` |
| 文件校验 | 每次写入后立即 `os.path.exists` + `os.path.getsize` |
| 图片处理 | Wikipedia -> Commons -> AI 兜底，三级 fallback |
| 标签规范化 | 入库后立即调用 `_normalize_tags.py` |
| 构建验证 | 所有修改源码的 skill 最后一步必须是 `npm run build` |
| 跳过标记 | 非致命失败统一用 `[SKIPPED:reason]`，必须能被终局自检兼容 |
| 合并 skill | 共享逻辑提取为独立 skill，原 skill 改为瘦入口（变量覆盖 + 引用） |

## 执行报告（必须输出）
- 成功项：X 条
- 补全项：Y 条（列出：{项目名} -> 补全动作 -> 最终状态）
- 失败跳过项：Z 条（列出：{项目名} -> 失败原因）
- 产物：`.claude/skills/ARG_NAME.md`
