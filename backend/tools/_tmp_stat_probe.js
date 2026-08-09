// 直接 stat public 目录下的文件, 对照正常/异常两组
const fs = require('fs');
const path = 'F:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/c0e78ea6f80a/';
for (const i of ['0', '5', '17', '23', '28', '38', '39', '55', '82', '83', '84', '89', '90', '95', '97', '105', '111', '129']) {
  const p = path + i + '.json';
  try {
    const s = fs.statSync(p);
    console.log(i.padStart(3), 'OK', s.size + 'B', s.mtime.toISOString());
  } catch (e) {
    console.log(i.padStart(3), 'STAT-ERR', e.code, e.message.slice(0, 60));
  }
}
