# 文档命名与生命周期

当前说明按主题放入agent、operations、library、ui、evaluation、course、reference。目录入口统一为README.md；其他人工维护文件采用小写英文短词与连字符，如account-memory.md、benchmark-ledger.md。日期使用YYYY-MM-DD，确需版本的设计稿使用v0.1.5等明确编号。

历史报告与旧任务放archive/<主题>/，保留阶段编号并规范文件名。归档不代表任务已完成，也不代表历史判断仍适用；原始报告正文保持原样。需要当前决策时，应在当前主题目录写说明并引用历史证据。

原始证据放evidence，沿用已有批次、题号与机器标识。冻结文件、source hash和注册表不可为统一大小写而重命名或改写。新实验使用新批次目录，不把每轮轨迹、JSON返回和临时日志散放docs根目录。

以下是稳定接口例外：分章标准规范.md保留AGENTS约定路径；evidence内原始标识与冻结文件不改名；agent/AUTONOMOUS_HANDOFF_CONTRACT.json保留机器契约名称。

可运行教学源码放examples，不混在docs里。node_modules、.venv、dist、__pycache__、.pytest_cache、运行数据库和密钥都不属于文档或提交内容。临时脚本继续放backend/tools/_tmp，不入库。

清理规则：生成物可删除重建；唯一的设计、原始答卷、任务状态、审计证据不能因日期早就删除。确认无引用、无独有内容且已被替代的稿件才删除，并在迁移记录说明。冻结评分R1不覆盖；更正另建明确修订。
