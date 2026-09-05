# z-lib 批量补壳作战状态

## 已入库上线（8 本）
爱弥儿 / 英国工人阶级状况 / 狱中书简 / 神圣家族 / 疯癫与文明 / 小说理论 / 论法的精神 / 正义论
（全部 verify 全绿 + master 部署 + OSS 双轨 + 向量）

## 已下载待 OCR/处理（z-lib 扫描 PDF，位于 F:/philosophy/西方/{作者}/）
| 书 | 扫描页数 | OCR 产物 | 状态 |
|---|---|---|---|
| 正义论 | 624 | _tmp/mia_batch/zhengyi_ocr.txt | ✅ 已入库上线 |
| 逻辑研究（第二卷） | 435 | _tmp/mia_batch/luoji_ocr.txt | ⏳ OCR 队列跑中 |
| 人类理解论 | 750 | _tmp/mia_batch/renlei_ocr.txt | ⏳ OCR 队列排队 |
| 语词和对象 | ? | 未 OCR | 📋 待 OCR |
| 狱中札记 | ? | 未 OCR | 📋 待 OCR |
| 文集（拉康） | epub 文本 | 无需 OCR | 📋 待构建（EPUB 管线参照 law_build.py） |
| 科学革命的结构 | 267 | 未 OCR | 📋 待 OCR |
| 算术基础 | 138 | 未 OCR | 📋 待 OCR |

## 下载游标
- z-lib 搜索游标：localStorage `zq`（z-library.sk 域）当前 = 8
- 队列文件：backend/tools/_tmp/shell_batch/zlib_queue.json（76 项，每项 {id,title,author,dir}）
- 下载流程：/s/{query}?content_type=book → domSnapshot 解析 /book/ 条目（shadow DOM 普通选择器不可见）→ 书页快照提取 /dl/{key} → 导航触发下载 → Downloads/*.tmp 稳定后 rename 到 F:/philosophy
- ⚠️ 连续搜索会触发 DiamWall 墙（冷却 30 分钟自动过）；扫描件下载稳定检测要等 ≥2 次相同 size

## 注意
- 逻辑研究 z-lib 这份只有第二卷，第一卷需另搜
- OCR 命令：backend/tools/_tmp/ocr_runner.py <pdf> <out.txt>（复用 dp_pdf_import 的 PaddleOCR）
- 处理完成的书：删除对应 0 字节 txt 占位；file_type 改 epub/pdf；verify_book + OSS + 向量 + master 部署
