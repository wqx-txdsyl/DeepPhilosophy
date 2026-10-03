我审完 a398b55f3 → 2f85229da。这轮 metric closure 我接受，SCHOL_CAL2 parity 归档也已经闭合，但 PF-RP4B 还不能 PASS。原因非常具体：S9 那个唯一 unresolved legacy key 其实在同一次 run 的 retrieved_evidence 里就存在精确 (book, chapter_idx) → book_id 映射，只是当前 resolver 只查了 citations，所以把本来可机械解析的 key 判成了 unresolved。

【注：本文件前半为 PF-RP4B 审查存档副本误挂；V4 Fresh Scholarly Qualification 任务书正文见下方分隔线之后的原文。】

=== 以下为 Reviewer 最新裁决原文（V3_RP3 = PASS → V4 FRESH QUALIFICATION AUTHORIZED）===

我审完 a398b55f3 → 2f85229da（V3-RP3-R1 receipt）。Reviewer Verdict — V3_RP3_PASS

我确认 R1.1 两个剩余 blocker 已关闭。V3-RP3 Scholarly Retrieval Recovery 至此正式通过 Reviewer Gate。

关键核验结果：

010bf438e 的真实工具链测试已经把同一 SID 串起来：search_scholarship("Wang Yangming") → sid ∈ results → search 不暴露正文 → get_scholarly_source(sid) → ABSTRACT_AVAILABLE → abstract 非空。上一轮"A 搜到、B 被读"的假连接已经不存在。

METADATA_ONLY candidate 现在确实进入 get_scholarly_source，并机械断言无 abstract、无 passages，没有伪造内容。

400de963c → 010bf438e 只有 regression test 文件发生变化，因此 evidence 中的 changed_files_git_diff=["backend/tests/test_o7e_v3_rp3_registry_recovery.py"] 与内容冻结 commit 对得上。

010bf438e → d8ae6b809 又确实只有 V3_RP3_RETRIEVAL_RECOVERY.json 一个 docs artifact 变化。

关于 SHA 自指

我接受现在的两阶段方案：

CONTENT_HEAD = 010bf438e
ARCHIVE_HEAD = d8ae6b809

artifact 内记录 HEAD_SHA=010bf438e，而包含 artifact 自身的 d8ae6b809 是纯归档 commit。

这是有效的无循环证据模型，不需要为了让文件记录自己的 commit SHA 再制造无限 docs commit。

因此最终 gate：

QUERY_FORMULATION_GUIDANCE          PASS
MULTILINGUAL_ALIAS_COVERAGE        PASS
RELEVANT_SEARCH_RESULT_AVAILABLE   PASS
SEARCH_TO_READ_PATH                PASS
CONTENT_EVIDENCE_PATH              PASS
METADATA_ONLY_SAFE_READ            PASS
SAFE_FALLBACK_REGRESSION           PASS
CANONICAL_SOURCE_CHAIN             PASS
CLEAN_REBUILD_DIFF                 0
CURATION_PROVENANCE                PASS
RP3_EVIDENCE_CONSISTENCY           PASS
V3_EVIDENCE_DRIFT                  false
PRODUCTION_MODEL_UNCHANGED         true
FROZEN_COMPONENT_DIFF              0

V3_RP3 = PASS

你报告的全量结果为 822/822/0/0；我这边不能远程重新执行你的本地 pytest，但已经独立核验对应测试代码和提交链，没有发现与回执冲突。

同时再次锁死：

V3_SCHOLARLY_GATE_NOT_MET

仍然是历史有效事实。RP3 PASS 不会、也不得把 V3 改成 PASS。下一次资格判断必须使用全新的 V4 holdout。

下一阶段直接授权。

PhiAgent O7-E — V4 Fresh Scholarly Qualification

MODEL: GLM-5.3
PRODUCTION_MODEL: deepseek-v4-flash
QUALIFICATION_BASE: d8ae6b809
Reviewer: GPT-5.6 Sol

Objective

使用全新、未消费、未调参的 V4 scholarly holdout，重新判断修复后的 PhiAgent 是否满足 O7-E scholarly qualification。

这是新测量，不是 V3 重判。

0. Freeze

从 d8ae6b809 开始冻结生产系统。

禁止：

修改 retrieval / registry / aliases / query formulation

修改 Local Patch / validator / quote_bound / replay

修改 evaluator/judge rubric 以适配结果

使用 V3 28 cases 作为 V4

使用 R25 或 RP3 王阳明 development probes 作为正式 holdout

看到 V4 answer/judge 后再 tuning

允许的仅是 qualification harness / fresh case manifest / evidence 输出。

1. Fresh Holdout

建立新的 V4 case set。

要求：

NO_V3_CASE_REUSE=true
NO_R25_REUSE=true
NO_RP3_DEV_PROBE_REUSE=true
CASE_CONTENT_UNSEEN_BEFORE_FREEZE=true

覆盖：

西方古典 / 中世纪 / 近现代 / 当代

中国哲学

至少一个其他非西方传统

原典解释

概念辨析

哲学家比较

scholarly controversy / secondary scholarship

需要 secondary-source content evidence 的题目

不得专门围绕 registry 已知强项出题。

2. Run

正式 run 使用：

PRODUCTION_MODEL=deepseek-v4-flash
BASE=d8ae6b809

保存完整：

prompts

final answers

tool trace

scholarly search calls

selected records

get_scholarly_source READ calls

evidence levels

repair trace

validator result

不得丢弃能够支持 RCA 的 query / tool args。

3. Mechanical Gate

先运行现有 delivery/mechanical gates。

必须独立报告：

PUBLISHED_COUNT
REPAIR_CONVERGENCE
REPAIR_CREATES_NEW_FATAL_ERROR
VALIDATOR_FATAL_COUNTS
SCHOLARLY_SEARCH_CALLS
SCHOLARLY_READ_CALLS
CONTENT_EVIDENCE_CASE_COUNT
SAFE_FALLBACK_CASE_COUNT

不得因为 scholarly judge 结果反向修改 mechanical evidence。

4. Scholarly Judge

沿用冻结后的 canonical scholarly rubric。

至少输出此前相同核心指标：

applicable_mean
textual
argument
interpretive
HD
LO
MEDIAN_LT_2
REQUIRED_DIMENSION_MEDIAN_LT_2
fatal categories

Judge 必须基于 V4 answer + V4 evidence。

不得参考 V3 分数决定 V4 分数。

5. Final Evidence

生成：

docs/evidence/V4_FINAL_HOLDOUT_*

以及机械 summary。

最终 Reviewer 输入必须能回答：

DELIVERY_GATE
SCHOLARLY_GATE
FAILED_GATES
FATAL_COUNTS
FINAL_V4_VERDICT

6. Stop condition

Builder 不得自行宣布：

O7-E_PASS
FINAL_PASS

完成后只返回：

READY_FOR_V4_SCHOLARLY_REVIEW

并附：

qualification BASE/HEAD

fresh holdout manifest

case count

run summary

judge summary

final-gate checker output

artifact paths

STOP

当前阶段转换正式记录为：

V3 FAIL → RCA → RP3 → R1 → R1.1 → RP3 PASS → V4 FRESH QUALIFICATION AUTHORIZED

这条 repair 线到这里收口，不再继续打 RP3 patch。
