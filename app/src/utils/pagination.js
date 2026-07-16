/**
 * 番茄小说式分页引擎 —— 像素级测量 + 字符偏移分页
 * 不依赖 EPUB.js，自己控制页码
 */

// 隐形测量 DOM（单例，避免重复创建）
let measureEl = null;
function getMeasureEl() {
  if (!measureEl) {
    measureEl = document.createElement('div');
    measureEl.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:800px;visibility:hidden;white-space:pre-wrap;word-break:break-all;font-family:serif;font-size:18px;line-height:1.9;padding:0;overflow:hidden;pointer-events:none;';
    document.body.appendChild(measureEl);
  }
  return measureEl;
}

/**
 * 测量在当前视口下一次能显示多少字符
 * @param {number} width - 容器宽度
 * @param {number} height - 容器高度
 * @param {number} fontSize - 字体大小 (px)
 * @param {number} lineHeight - 行高倍率
 * @returns {number} 每页字符数
 */
export function measurePageCapacity(width, height, fontSize = 18, lineHeight = 1.9) {
  const el = getMeasureEl();
  el.style.width = width + 'px';
  el.style.height = height + 'px';
  el.style.fontSize = fontSize + 'px';
  el.style.lineHeight = String(lineHeight);

  // 填充足够多的文本
  const sample = '测' + '试字。'.repeat(2000);
  el.textContent = sample;

  // 检查实际渲染了多少字符的高度
  // 用 range 或 scrollHeight 判断溢出
  let lo = 0, hi = sample.length;
  while (lo < hi) {
    const mid = Math.ceil((lo + hi) / 2);
    el.textContent = sample.slice(0, mid);
    // 如果内容高度超过容器高度，说明太多了
    if (el.scrollHeight > height) {
      hi = mid - 1;
    } else {
      lo = mid;
    }
  }
  el.textContent = '';
  return Math.max(100, lo);
}

/**
 * 将文本按每页字符数分页
 * @param {string} text - 全书文本
 * @param {number} charsPerPage - 每页字符数
 * @returns {Array<{page: number, start: number, end: number, text: string}>}
 */
export function paginateText(text, charsPerPage) {
  const pages = [];
  let offset = 0;
  let pageNum = 1;

  while (offset < text.length) {
    // 在 charsPerPage 附近寻找自然断点（段落/句号）
    let end = Math.min(offset + charsPerPage, text.length);
    if (end < text.length) {
      // 往回找最近的段落分隔
      const searchStart = Math.max(offset + Math.floor(charsPerPage * 0.7), offset);
      const slice = text.slice(searchStart, end);
      const breakIdx = slice.search(/[\n]{2,}|[。！？.!?\n]/);
      if (breakIdx >= 0) {
        end = searchStart + breakIdx + 1;
      }
    }
    pages.push({
      page: pageNum,
      start: offset,
      end: end,
      text: text.slice(offset, end),
    });
    offset = end;
    pageNum++;
  }
  return pages;
}

/**
 * 从字符偏移计算页码
 */
export function getPageFromOffset(pageBreaks, charOffset) {
  for (let i = 0; i < pageBreaks.length; i++) {
    if (charOffset < pageBreaks[i].end) return i;
  }
  return pageBreaks.length - 1;
}
