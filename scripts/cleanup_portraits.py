"""清理肖像 V2：仅处理确认的 MD5 相同对"""
import os, sys, json, io, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

def safe_fn(name):
    return name.replace('/', '-').replace('\\', '-').replace(':', '-')

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# ===== 确认的 MD5 相同对 =====
confirmed_dupes = [
    # --- 同一人不同名（合并条目）---
    ('索伦·克尔凯郭尔', '基尔克果'),
    ('阿维森纳', '伊本·西那'),
    ('卡尔·波普尔', '波普'),
    ('保罗·弗莱雷', 'Paulo Freire'),
    ('阿威罗伊', '伊本·鲁世德（阿威罗伊）'),
    ('塞涅卡', '塞内卡'),
    ('希帕提娅', '希帕基娅'),

    # --- 不同人共用一图（删错的那个，保留名字更像哲学家的）---
    ('乔尔丹诺·布鲁诺', '布鲁诺·德·菲内蒂'),   # 保留乔尔丹诺·布鲁诺 (the philosopher)
    ('义湘', '元晓 (Wonhyo)'),                 # 保留义湘 (删韩国僧人名)
    ('道宣', '元晓 (Wonhyo)'),                 # 保留道宣
    ('杰弗里·哈特曼', '杰弗里·辛顿'),           # 保留杰弗里·辛顿
    ('阿维塔尔·罗奈尔', '阿尔贝·加缪'),          # 保留加缪
    ('大卫·乌纳庞', '西塞罗'),                  # 保留西塞罗
    ('亚历克西斯·赖特', '托克维尔'),             # 保留托克维尔
    ('马纳里基·米哈卡-杜兰特', '费奥多尔·陀思妥耶夫斯基'), # 保留陀思妥耶夫斯基
    ('素拉·西瓦拉克', '拉纳吉特·古哈'),          # 保留拉纳吉特·古哈
    ('穆索尼乌斯·鲁弗斯', '盖尤斯'),            # 保留盖尤斯
    ('普莱斯纳', '莱昂纳多·博夫'),              # 保留莱昂纳多·博夫
    ('凯撒·尤利乌斯', '盖尤斯'),               # 保留盖尤斯
    ('比尔·尼格尔', '比尔·麦吉本'),             # 保留比尔·麦吉本
    ('詹姆斯·莫菲特', '詹姆斯·科恩'),           # 保留詹姆斯·科恩
    ('阿勒西奥·库马拉', '马可·奥勒留'),         # 保留马可·奥勒留
    ('马库伊尔肖奇特尔', '帕特丽夏·科林斯'),     # 保留帕特丽夏·科林斯
    ('特蕾西亚·特埃瓦', '玛丽亚·罗斯特沃罗夫斯基'), # 保留后者
    ('阿希卡尔', '卡尔·马克思'),               # 保留马克思
    ('托尔·尼尔森', '梅拉布·马马尔达什维利'),    # 保留后者
    ('卡罗琳·汉弗莱', '琳达·谢勒'),            # 保留琳达·谢勒
    ('史蒂文·温多努', '伯纳德·斯蒂格勒'),        # 保留斯蒂格勒
    ('玛拉基', '传道者'),                      # 保留传道者
    ('迈克·哈纳', '迈克尔·多德森'),            # 保留迈克尔·多德森
    ('彼得·欧文', '彼得·厄巴哈'),              # 保留彼得·厄巴哈
    ('梅特罗多罗斯', '伯纳德·纳罗科比'),         # 保留伯纳德·纳罗科比
    ('赫尔马库斯', '马可·奥勒留'),             # 保留马可·奥勒留
    ('德谟那克斯', '德谟克利特'),               # 保留德谟克利特
    ('禽滑厘', '墨子'),                        # 保留墨子
    ('卢伽尔班达', '提亚马特'),                 # 保留提亚马特
    ('尼努尔塔', '提亚马特'),                   # 保留提亚马特
    ('恩美尔卡尔', '提亚马特'),                 # 保留提亚马特
]

# ===== 1. 合并同人条目 =====
same_person_merge = confirmed_dupes[:7]  # 前7对是同人
merge_pairs_to_apply = [
    ('索伦·克尔凯郭尔', '基尔克果'),  # 保留全名
    ('阿维森纳', '伊本·西那'),         # 两者都是别名，保留阿维森纳
    ('卡尔·波普尔', '波普'),           # 保留全名
    ('保罗·弗莱雷', 'Paulo Freire'),    # 保留中文名
    ('阿威罗伊', '伊本·鲁世德（阿威罗伊）'),  # 保留有括号的
    ('塞涅卡', '塞内卡'),              # 保留塞涅卡
    ('希帕提娅', '希帕基娅'),           # 保留希帕提娅
]

for keeper, dropper in merge_pairs_to_apply:
    if keeper in philosophers and dropper in philosophers:
        kd = philosophers[keeper]
        dd = philosophers[dropper]
        if isinstance(kd, dict) and isinstance(dd, dict):
            if dd.get('rank', 0) > kd.get('rank', 0):
                kd['rank'] = dd['rank']
            if dd.get('book_count', 0) > kd.get('book_count', 0):
                kd['book_count'] = dd['book_count']
            if len(dd.get('bio', '')) > len(kd.get('bio', '')):
                kd['bio'] = dd['bio']
        del philosophers[dropper]
        print(f'[合并] {dropper} -> {keeper}')

# ===== 2. 删错误共用图 =====
wrong_image_pairs = confirmed_dupes[7:]  # 后面的都是错图
for to_delete, keeper in wrong_image_pairs:
    for ext in ['.jpg', '.png', '.webp']:
        fp = os.path.join(IMG_DIR, safe_fn(to_delete) + ext)
        if os.path.exists(fp):
            os.remove(fp)
            print(f'[错图] {safe_fn(to_delete)+ext} (与 {keeper} 同图)')
            break

# ===== 3. 删孤图 =====
phil_fnames = set()
for name in philosophers:
    for ext in ['.jpg', '.png', '.webp']:
        phil_fnames.add(safe_fn(name) + ext)

for f in os.listdir(IMG_DIR):
    if f.endswith(('.jpg', '.png', '.webp', '.jpeg')) and f not in phil_fnames:
        os.remove(os.path.join(IMG_DIR, f))
        print(f'[孤图] {f}')

# ===== 保存 =====
with open(PHIL_FILE, 'w', encoding='utf-8') as f:
    json.dump(philosophers, f, ensure_ascii=False, indent=2)

remaining = len([f for f in os.listdir(IMG_DIR) if f.endswith(('.jpg','.png','.webp'))])
print(f'\n=== 完成 ===')
print(f'合并条目: {len(merge_pairs_to_apply)}')
print(f'删除错图: {len(wrong_image_pairs)}')
print(f'哲学家: {len(philosophers)}')
print(f'剩余图片: {remaining}')
