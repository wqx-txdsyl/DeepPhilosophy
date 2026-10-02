# 流派详情页与内容维护

正式入口保持 `/school/:name`，现有组件名称、JSON 和图片路径不变。

## 页面

- 大幅原图 Hero、完整简介、独立子流派章节、人物星图、连续时间轴、词海、金句、典籍、结语和参考来源。
- 子流派默认在父页展开真实资料。已有独立数据的分支提供详情链接；旧子流派网址可回到所属父页并展开分支，避免无内容的“建设中”。
- 星图使用稳定布局，完整保留人物及关系中的相关节点；后者可能是学派、文本或概念，不能统称人物。主题比较不画成直接师承。
- 时间轴解析公元前、公元后和世纪，未知年代不伪造年份；点击事件就在原位展开。优先从事件标题识别人名，避免逝世者的说明提到另一人时展示错肖像。
- 词海与金句支持悬停、点击固定、键盘和触摸。相同词名的不同解释归到同一入口下，保留全部解释。
- 书目只用准确标题及作者匹配正式书库，不把释义、导读或研究著作链接成原典。未有可读章节的书标为“查看书目”。
- 头像与作者链接根据目录中的真实路径和姓名解析。遇到明显跨时代身份冲突时隐藏误导性入口。

## 数据与审校

`app/public/schools/data/` 仍是流派内容唯一正式源。新增 `schools/catalog.json` 是由现有数据生成的轻量导航索引，包含 111 个主流派、子流派所属关系、作者图片路径及书目，不取代原始详情。

本次修正包括七个空壳流派的完整重建，古希伯来、古埃及及非洲资料中的硬错，中文简介补充、人物身份与生卒年纠正、错误书名/出版时间，以及把整份流派书目错归第一位人物的问题。具体已核对来源保存在各页 `sources`；重点修订范围写入 `contentReview`。

旧金句缺乏可校对的版本、页码或逐字引文证据。保留有用的概述，使用 `kind: "paraphrase"`，界面不加引号、显示“思想概述”。新增直接引文须用 `kind: "quote"` 并附 `source` 或 `sourceUrl`。这项分类不意味着其中每一个历史或解释性断言都已得到独立学术审定。

`docs/school-content-audit.json` 记录全部流派的结构检验、重复概念、关系外部节点和需要进一步来源核查的事项。结构完整与逐条学术考证是不同检查：零结构错误不表示不存在解释争议。不要按统一数量虚构人物、作品、分支或历史事件。

## 更新流程

```sh
python3 scripts/audit_school_content.py --strict --output docs/school-content-audit.json
python3 scripts/sync_genealogy_catalog.py
python3 scripts/sync_school_catalog.py
node --test app/tests/genealogyAtlas.test.mjs app/tests/schoolContent.test.mjs app/tests/schoolConstellationLayout.test.mjs
cd app
npm run build
```

`--normalize-legacy` 仅用于转换早期 Python 列表字符串及嵌套数组，并为未标注的旧金句设置概述类型；不要使用它代替内容审校。

发布沿用 Cloudflare Pages + OSS 双轨：先验证分支预览并同步完整 JS/CSS/字体和更新的静态数据，再发布 master，确认生产提交、页面交互和 OSS 资源均可访问。
