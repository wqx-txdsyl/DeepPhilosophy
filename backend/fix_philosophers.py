"""修复哲学家地区分类 + AI 多维度评分排序"""
import json, os, sys, io, time

# UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(__file__)
PHILOSOPHERS_PATH = os.path.join(BASE, "..", "app", "public", "philosophers.json")

philosophers = json.load(open(PHILOSOPHERS_PATH, "r", encoding="utf-8"))

# ═══════════════════════════════════════════
# 地区分类规则 — 基于国家/地区的明确映射
# ═══════════════════════════════════════════

COUNTRY_REGION = {
    # ── 东方哲学：仅中国 ──
    "中国": "东方", "中国等": "东方",
    "西藏": "东方",
    "元朝": "东方",

    # ── 西方哲学：欧洲 + 美洲 + 大洋洲 + 俄罗斯 ──
    # 西欧
    "英国": "西方", "法国": "西方", "德国": "西方",
    "意大利": "西方", "古罗马": "西方", "罗马帝国": "西方", "罗马共和国": "西方",
    "希腊": "西方", "古希腊": "西方",
    "西班牙": "西方", "荷兰": "西方", "瑞士": "西方",
    "奥地利": "西方", "奥匈帝国": "西方",
    "爱尔兰": "西方", "比利时": "西方",
    # 北欧
    "丹麦": "西方", "挪威": "西方", "瑞典": "西方", "芬兰": "西方",
    # 东欧
    "波兰": "西方", "捷克": "西方", "匈牙利": "西方",
    "保加利亚": "西方", "克罗地亚": "西方", "立陶宛": "西方",
    # 俄罗斯/苏联
    "俄罗斯": "西方", "苏联": "西方", "俄国": "西方",
    "格鲁吉亚": "西方",
    # 东南欧/小亚细亚基督教传统
    "拜占庭帝国": "西方", "亚美尼亚": "西方",
    "卡帕多细亚": "西方",
    # 北美
    "美国": "西方", "加拿大": "西方",
    # 拉美（欧洲哲学传统）
    "墨西哥": "西方", "阿根廷": "西方", "巴西": "西方", "秘鲁": "西方",
    "古巴": "西方", "乌拉圭": "西方",
    # 大洋洲
    "澳大利亚": "西方", "新西兰": "西方",
    # 非洲（殖民时代后受欧洲传统影响的哲学家）
    "塞内加尔": "西方", "肯尼亚": "西方", "加纳": "西方",
    "南非": "西方", "尼日利亚": "西方", "喀麦隆": "西方",

    # ── 世界哲学：印度、中东、东亚（除中国外）、非洲、前哥伦布、大洋洲原住民 ──
    # 日本、朝鲜
    "日本": "世界", "朝鲜": "世界", "朝鲜王朝": "世界", "新罗": "世界", "韩国": "世界",
    # 印度、南亚
    "印度": "世界", "古印度": "世界",
    "不丹": "世界", "乌仗那": "世界",
    # 蒙古
    "蒙古": "世界", "蒙古帝国": "世界",
    # 东南亚
    "越南": "世界", "泰国": "世界", "印度尼西亚": "世界",
    # 波斯/伊斯兰哲学传统
    "波斯": "世界", "伊朗": "世界",
    "阿拉伯帝国": "世界", "安达卢斯": "世界",
    "土耳其": "世界", "奥斯曼": "世界", "后突厥汗国": "世界",
    "小亚细亚": "世界",
    # 古代美索不达米亚/中东
    "苏美尔": "世界", "美索不达米亚": "世界", "巴比伦": "世界",
    "巴比伦第一王朝": "世界",
    "叙利亚": "世界", "亚述": "世界",
    "巴勒斯坦": "世界", "加达拉": "世界",
    # 犹太传统
    "以色列": "世界", "以色列王国": "世界", "犹太": "世界", "犹大王国": "世界",
    "乌斯地": "世界",
    # 中亚
    "中亚": "世界", "哈萨克斯坦": "世界",
    # 北非
    "埃及": "世界", "突尼斯": "世界",
    # 古埃及
    "古埃及": "世界",
    # 前哥伦布文明
    "玛雅": "世界", "玛雅文明": "世界", "玛雅城邦帕伦克": "世界",
    "玛雅城邦科潘": "世界", "玛雅城邦": "世界",
    "阿兹特克": "世界", "阿兹特克帝国": "世界",
    "印加帝国": "世界",
    "托尔特克": "世界",
    "尤卡坦半岛": "世界",
    # 大洋洲
    "汤加": "世界",
}

def classify_region(name, country_str, school_str):
    """根据国家、流派、姓名综合判断地区"""
    if not country_str:
        return None

    countries = [c.strip() for c in country_str.split('/')]
    regions = set()
    for c in countries:
        r = COUNTRY_REGION.get(c)
        if r:
            regions.add(r)

    if len(regions) == 1:
        return regions.pop()
    if len(regions) > 1:
        # 中国 + 其他 → 东方优先；西方 + 世界 → 西方优先
        if "东方" in regions:
            return "东方"
        if "西方" in regions:
            return "西方"
        return "世界"

    # 未能根据国家判断 → 基于流派推断
    chinese_schools = ["儒家", "道家", "宋明理学", "法家", "墨家", "兵家",
                        "朱子学", "阳明学", "玄学", "黄老", "名家",
                        "纵横家", "农家", "小说家", "杂家"]
    western_schools = ["古希腊哲学", "经院哲学", "德国古典哲学", "现象学",
                       "分析哲学", "存在主义", "实用主义", "结构主义",
                       "后结构主义", "解构主义", "法兰克福学派", "批判理论",
                       "马克思主义", "自由主义", "功利主义", "经验主义",
                       "理性主义", "唯心主义", "唯物主义", "实证主义",
                       "逻辑哲学", "语言哲学", "科学哲学", "心灵哲学",
                       "启蒙运动", "启蒙", "文艺复兴", "教父哲学", "经院"]

    for cs in chinese_schools:
        if cs in school_str:
            return "东方"
    for ws in western_schools:
        if ws in school_str:
            return "西方"

    # 非中国的东方流派 → 世界
    world_schools = ["佛学", "佛教", "禅宗", "华严宗", "唯识", "中观", "密宗",
                      "伊斯兰", "苏菲", "琐罗亚斯德", "印度教", "吠檀多",
                      "耆那教", "锡克教", "神道教", "萨满", "犹太",
                      "儒教", "东亚", "东亚哲学"]
    for ws in world_schools:
        if ws in school_str:
            return "世界"

    return None


# ═══════════════════════════════════════════
# 执行分类
# ═══════════════════════════════════════════
stats = {"东方": 0, "西方": 0, "世界": 0, "未分类": 0}
changes = []

for name, p in philosophers.items():
    old_region = p.get("region", "")
    # 规范化旧值
    if old_region in ("?", "", None):
        old_region = "未分类"
    elif old_region not in ("东方", "西方", "世界"):
        # 尝试从旧值中提取主要分类
        if "东方" in old_region:
            old_region = "东方"
        elif "西方" in old_region:
            old_region = "西方"
        elif "世界" in old_region:
            old_region = "世界"
        elif "中国" in old_region or "Africa" in old_region or "Latin" in old_region:
            old_region = "未分类"
        else:
            old_region = "未分类"

    country = p.get("country", "")
    school = p.get("school", "")

    new_region = classify_region(name, country, school)
    if new_region is None:
        new_region = "未分类"

    if old_region != new_region:
        changes.append((name, old_region, new_region, country, school))

    p["region"] = new_region
    stats[new_region] = stats.get(new_region, 0) + 1

# 按 rank 降序排序后保存
items = sorted(philosophers.items(), key=lambda x: x[1].get('rank', 0), reverse=True)
philosophers = dict(items)
json.dump(philosophers, open(PHILOSOPHERS_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"哲学家总数: {len(philosophers)}")
print(f"\n地区分布:")
for r, c in stats.items():
    print(f"  {r}: {c}")

print(f"\n分类变更: {len(changes)} 条")
print("\n变更详情 (前30条):")
for name, old, new, country, school in changes[:30]:
    print(f"  [{old}→{new}] {name}  country={country}  school={school}")

if len(changes) > 30:
    print(f"  ... 还有 {len(changes)-30} 条")

# 打印仍未分类的
unclassified = [(k, v.get("country",""), v.get("school",""))
                for k, v in philosophers.items() if v.get("region") == "未分类"]
if unclassified:
    print(f"\n⚠ 仍未分类: {len(unclassified)} 位")
    for name, country, school in unclassified[:20]:
        print(f"  {name} | country={country} | school={school}")
else:
    print("\n✓ 全部哲学家已分类完成")
