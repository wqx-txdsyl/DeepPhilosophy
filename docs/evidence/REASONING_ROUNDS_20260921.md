# 按轮次折叠思考：纠正上一版总面板

参考已实际读取的[DSH ReasoningRow.tsx](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/client/ui-chat/src/client/chat/ReasoningRow.tsx)。该组件对单段思考提供独立DisclosureRow；当前master默认折叠。按用户要求，本项目将正在生成的段落默认展开，工具开始后折叠上一段，再展开下一段；保留用户手动展开已完成段落的能力。不是声称完全复制DSH的默认行为。

前版错误：把所有思考与工具塞入一个总滚动面板；已移除。大号探索卡片也已撤掉，改为紧凑的单列问题列表。

英文思考原因：通用智能体初始中文提示只包含公开说明和回答，而且reinforce分支明确排除了general。两处均已修复，现在初始请求及每轮模型调用都要求中文reasoning。继续原样展示提供方reasoning_content，不把翻译伪装为原始输出。提示约束不能保证供应商模型始终遵守；本轮未进行长模型生成验收。

验收：前端四组测试、构建通过；中文general初始与reinforce系统消息均检查通过。浏览器在明确的交互测试场景中依次确认：第一段展开→点击工具阶段后第一段折叠→下一段展开且第一段保持折叠。旧段保留独立展开按钮。

已更新backend/static并重启后端。备份目录：backend/tools/_tmp/reasoning-rounds-release-20260921/previous。
