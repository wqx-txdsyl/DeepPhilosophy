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
 * 估算每页字符数（公式计算，无需 DOM 测量，瞬间完成）
 * 标准中文字符约 = 容器宽×高 / (字号×行高) × 填充率
 */
export function measurePageCapacity(width, height, fontSize = 18, lineHeight = 1.9) {
  const charWidth = fontSize;            // 中文等宽约等于字号
  const lineH = fontSize * lineHeight;   // 实际行高
  const cols = Math.floor(width / charWidth);
  const rows = Math.floor(height / lineH);
  // 0.75 填充率（标点、段落间距）
  return Math.max(200, Math.floor(cols * rows * 0.75));
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
