# 冻结开发评审记录 R2（zcode统一重评）

同一60道分析/研究题、每对象72回合全部由zcode按冻结v1.2统一重评（648/648）。控制样本T1-T6通过；错误指控经主体感知回执可得性规则裁定。R1保持冻结不动。

|对象|统一60题总分 /100|C维|R维|通过题数|裁定后严重错误|
|---|---:|---:|---:|---:|---:|
|PhiAgent v0.1.0|95.27|95.4*|96.2*|53/60|confirmed 0 / pending 0|
|PhiAgent v0.1.1|99.42|99.5*|97.3*|59/60|confirmed 0 / pending 0|
|PhiAgent v0.1.2|97.12|97.3*|98.8*|56/60|confirmed 1 / pending 1|
|PhiAgent v0.1.3|98.60|98.9*|98.0*|58/60|confirmed 0 / pending 0|
|PhiAgent v0.1.4|99.14|99.1*|99.4*|59/60|confirmed 0 / pending 0|
|PhiAgent v0.1.5|99.24|99.3*|98.5*|60/60|confirmed 0 / pending 0|
|DeepSeek 网页型号未记录 · 深度思考＋联网|77.83|79.9*|58.7*|30/60|confirmed 0 / pending 8|
|豆包 网页型号未记录 · 快速默认档|70.37|72.7*|51.3*|21/60|confirmed 0 / pending 23|
|ChatGPT Work · 6.1 Sol · high|80.36|83.7*|65.0*|34/60|confirmed 0 / pending 10|

*维度列为逐键百分制的简单平均，仅作速览；正式口径见aggregate.json（C/R按贡献公式合成）。

R1→R2主要差异：R1为混合方法抽样评审（每对象9-28轮直接复核+模型初评，ChatGPT为全文文档评审），R2为单一冻结协议全量重评。ChatGPT大幅下降主因是R1未做逐轮评审；PhiAgent上升部分反映全量引文核验下的真实完成度，但同项目评审从属关系与单一评审族限制已如实登记，不构成受控排行。

完整逐轮等级、裁定后错误记录与hash在[SCORES.json](SCORES.json)。冻结校验见[FREEZE_MANIFEST.json](FREEZE_MANIFEST.json)。
