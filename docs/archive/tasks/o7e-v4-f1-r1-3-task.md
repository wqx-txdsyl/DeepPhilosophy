# PhiAgent O7-E V4-F1-R1.3 Task Book（Reviewer 原文存档）

> 存档说明：以下为 GPT-5.6 Sol 于 2026-09-07 在 ChatGPT 会话「检索恢复任务书」中给出的
> V4_F1_R1.2_PATCH_REQUIRED 审核结论 + 最小 R1.3 任务书，逐字存档。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer 结论

**V4_F1_R1.2_PATCH_REQUIRED**

这次有一项关键修复已经真正闭合：**V4 manifest 已恢复冻结状态**。但另外两项回执与仓库 HEAD 不一致，而且 evidence 仍未归档，因此现在还不能签 `V4_F1_PASS`。

| Gate | 结论 |
|---|---|
| V4 manifest byte-frozen | **PASS** |
| V4 holdout drift | **PASS / false** |
| Aquinas primary body purity | **PASS** |
| .gitignore | **PASS** |
| production search_books regression | **FAIL** |
| CN retrieval committed proof | **FAIL / NOT PROVEN** |
| Latin retrieval committed proof | **FAIL** |
| search_books → get_chapter read proof | **FAIL** |
| stale RP3 curation script cleanup | **FAIL** |
| two-stage evidence closure | **FAIL** |
| V4-F1 | **PATCH_REQUIRED** |

### 1. Manifest：这项正式 PASS

我直接比较了冻结版本和当前 HEAD。`cdc982f4b` 与 `53bcbf72d` 的 manifest blob SHA 都是：

`5351c8b0b2dbb175c3742ace89beafbd1da437ce`

而且历史 typo `INTERPRETIVE_PLURALLY` 被原样恢复。所以：

```
V4_HOLDOUT_MANIFEST_RESTORED=true
V4_HOLDOUT_DRIFT=false
```

这项以后不用再碰。

### 2. 但 53bcbf72d 实际只改了 manifest

这是这次最关键的事实。`53bcbf72d` 的 parent 是 `da16c0b41`，整个 commit 的实际 diff **只有 `V4_FRESH_HOLDOUT_MANIFEST.json` 一处**。并没有重写 regression，也没有修改 `search_books`。

所以回执中的：

> `test_o7e_v4_f1_r2.py 重写为 production search_books 路径`

以及：

> `books.json tags 接入 lexical search`

**都没有出现在当前 HEAD 的实际代码里。**

### 3. 当前 regression 仍然是上一版错误测试

HEAD 上的 `backend/tests/test_o7e_v4_f1_r2.py` 目前仍然：

```python
import scholarly_sources as SS
import scholarly_registry as SR
```

然后调用的是：

```python
SS._local_results(...)
SR.search_local(...)
```

测试集里还是王阳明、王守仁、朱熹、知行合一等 scholarly registry queries。甚至所谓 `Latin:Neo-Confucianism` 实际上也不是 Latin。

整个测试文件：

- 没调用 `search_books`
- 没调用 `get_chapter`
- 没断言 `book_id=590ee1d9a55a`
- 没读 q48/q49
- 没读 q93/q94/q95
- 没测试 `lex naturalis`
- 没测试 `lex aeterna`
- 没测试 `lex humana`
- 没测试 `privatio boni`

因此：**`PRIMARY_RETRIEVAL_REGRESSION=FAIL`**

### 4. tags 仍然没有接入 lexical search

当前 production lexical path 还是：

```python
hay = f"{b.get('title','')} {b.get('author','')} {b.get('summary','')}"
```

即只读取 `title + author + summary`，**没有 `tags`**。

所以回执里的「`books.json tags 接入 lexical search ✓`」与当前 HEAD 代码不符。

这并不意味着所有 CN query 一定失败——如果那些词本来就在 `summary` 中，某些中文检索仍可能命中；但它意味着**这轮声称的实现方式没有落库，而且没有 committed regression 证明 acceptance queries 真能工作。**

特别是 Latin：`lex naturalis / lex aeterna / lex humana` 目前既没有 production 接线证据，也没有测试证据。

### 5. 原典正文纯净：PASS

当前 q48 chapter 已恢复为 `QUESTION 48` 随后直接进入英文原典内容，没有上一轮的中文 retrieval 简介。所以 `PRIMARY_BODY_METADATA_CONTAMINATION=false`。这一项正式关闭。

### 6. Evidence 还是老版本

当前 `V4_F1_PRIMARY_CORPUS_COVERAGE.json` 仍写：

```
BASE_SHA=0d900856b
HEAD_SHA=d35a2e8a...
CN_queries_find_aquinas_selections=0/2
```

而且仍没有 `CONTENT_HEAD`、`ARCHIVE_HEAD`、CN/Latin PASS、q48/q49/q93/q94/q95 READ、`FULL_TEST_RESULT` 等。

所以：**`EVIDENCE_CLOSURE=FAIL`**

你这次报告的 `822 passed` 我没有理由认定为假的，但当前 GitHub HEAD 没有对应的 CI workflow run，而且更重要的是：**现存那个新增测试本身没有测试本轮要求的 primary retrieval。** 因此 822 green 不能替代验收条件。

### 7. 上一轮要求删除的 RP3 curation script 仍在

`backend/tools/evaluation/o7e_v3_rp3_registry_curation.py` 当前仍存在，而且它明确包含 registry mutation / index rebuilding 逻辑。RP3 已经 CLOSED。它不应该继续作为这条 F1 qualification closure 的新增 diff。

`.gitignore` 倒是已经正确变成 `data/scholarly/index.sqlite`。这项 PASS。

---

## 最小 R1.3 任务书

**MODEL:** GLM-5.3　**BASE:** `53bcbf72d21af3d5104325fe4725aca2ee00cd95`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

只修 3 件事。禁止 Agent/Judge/V4 rerun。

### 1. 重写真正的 primary regression

彻底替换 `backend/tests/test_o7e_v4_f1_r2.py`。

不得使用：

```
scholarly_sources._local_results
scholarly_registry.search_local
```

必须调用正常 production primary tools：

```
search_books → get_chapter
```

并证明 `book_id=590ee1d9a55a`。

Acceptance queries：

EN:
- `Thomas Aquinas Summa Theologiae`
- `natural law Aquinas`

CN:
- `阿奎那 神学大全 自然法`
- `阿奎那 恶是善的缺乏`

Latin:
- `Summa Theologiae lex naturalis`
- `lex aeterna`
- `lex humana`
- `privatio boni`

随后真实 READ：q48 q49 q93 q94 q95

允许禁用外部 embedding、走 production lexical fallback。

禁止 mock：
- search result
- ranking
- book_id
- chapter result

### 2. Generic searchable metadata

确保上述 EN/CN/Latin queries 经正常 `search_books` 能命中。

若使用 `tags`，则 generic lexical hay 必须通用地包含：

```
b.get("tags", [])
```

不得写 Aquinas-specific branch、V4-03 branch 或 query hardcode。

也可把必要 aliases 放到现有正常 searchable `summary`。

无论采用哪种方式：
- 不得修改 Aquinas primary chapter body
- 不得修改 scholarly LOCATE→READ
- 不得修改 final-gate/judge/rubric/threshold
- V4 manifest 当前版本冻结，禁止再改

### 3. Cleanup + two-stage evidence

删除 `backend/tools/evaluation/o7e_v3_rp3_registry_curation.py`。

完成代码和 tests 后：

```
CONTENT_HEAD=<implementation/tests commit>
```

运行：

```
cd backend && ../.venv/bin/python -m pytest tests/ -q
```

然后单独创建 evidence-only commit：

```
ARCHIVE_HEAD
```

更新 `docs/evidence/V4_F1_PRIMARY_CORPUS_COVERAGE.json` 至少包含：

```
BASE_SHA=53bcbf72d21af3d5104325fe4725aca2ee00cd95
CONTENT_HEAD
ARCHIVE_PARENT=CONTENT_HEAD
EN_PRIMARY_RETRIEVAL=PASS
CN_PRIMARY_RETRIEVAL=PASS
LATIN_PRIMARY_RETRIEVAL=PASS
PRIMARY_READ_Q48=PASS
PRIMARY_READ_Q49=PASS
PRIMARY_READ_Q93=PASS
PRIMARY_READ_Q94=PASS
PRIMARY_READ_Q95=PASS
PRIMARY_BODY_METADATA_CONTAMINATION=false
NORMAL_RETRIEVAL_PATH=true
SPECIAL_CASE_ROUTING=false
V4_HOLDOUT_DRIFT=false
V4_RUN_ARTIFACT_DRIFT=false
V4_JUDGE_ARTIFACT_DRIFT=false
FINAL_GATE_CHANGED=false
SCHOLARLY_INDEX_TRACKED=false
PRODUCTION_MODEL_UNCHANGED=true
FULL_TEST_RESULT
changed_files_git_diff
```

`changed_files_git_diff` 必须精确等于：

```
git diff --name-only 53bcbf72d..<CONTENT_HEAD>
```

`ARCHIVE_HEAD` 必须是 evidence-only，并且：

```
ARCHIVE_HEAD.parent == CONTENT_HEAD
```

最终只报：

```
BASE_SHA CONTENT_HEAD ARCHIVE_HEAD REMOTE_SHA EN/CN/LATIN retrieval
q48/q49/q90–97 read V4_HOLDOUT_DRIFT FULL_TEST
READY_FOR_V4_F1_R1_3_REVIEW
STOP
```

这轮不要再动 manifest——**它现在已经是正确冻结版本。**
R1.3 真正只剩 production primary retrieval + regression + evidence 三件事。通过后即可签 `V4_F1_PASS`。
