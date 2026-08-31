import { useState } from 'react';
import { DP_READER, resolveCite } from '../../utils/api';
import { useLang } from '../../utils/i18n';
import DrawioInline from '../DrawioInline';

/**
 * markdown 简易渲染（从 AgentPage 抽出）
 *
 * 2026-08-29 Conversation Workspace 重构（§10）: 修复历史 citation 门控 bug——
 * 旧实现 `agent !== 'general' ? null : <CiteLink/>` 导致非 General 回答的
 * 【出处】链接整体不可见。Citation 现在只属于 assistant message, 与当前/历史
 * Agent 身份无关, General 与 Nietzsche 的引用均可见、可点击（UAT-06）。
 * 2026-08-30 Phase 3: 引用解析复用 utils/api.resolveCite（与引用面板同一实现）。
 */

/* ── 出处跳转链接（【《书名》·章节】→ 定位后跳 DeepPhilosophy 阅读器） ── */
export function CiteLink({ book, chapter }) {
  const { t } = useLang();
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const openCite = () => {
    if (loading) return;
    setLoading(true);
    setFailed(false);
    resolveCite(book, chapter || '')
      .then(d => {
        setLoading(false);
        if (d.error || d.matched === false) { setFailed(true); return; }   // 2026-08-14: 未匹配章节不再静默跳第 0 章
        window.open(`${DP_READER}/${d.book_id}?ch=${d.chapter_idx || 0}`, '_blank');
      })
      .catch(() => { setLoading(false); setFailed(true); });
  };
  return (
    <span onClick={openCite} title={failed ? t('citeFail') : t('citeOpen')}
      className={`cw-cite-inline${failed ? ' cw-cite-inline-fail' : ''}${loading ? ' cw-cite-inline-loading' : ''}`}
      style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
      【《{book}》{chapter ? `·${chapter}` : ''}】{loading ? '…' : ''}
    </span>
  );
}

/* ── 行内元素: **粗体** *斜体* `代码` [链接](url) ~~删除线~~ 【出处】 ── */
export function renderInline(text) {
  const parts = (text || '').split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]*\]\([^)]*\)|~~[^~]+~~|【[^】]+】)/g);
  return parts.map((p, i) => {
    if (p.startsWith('**') && p.endsWith('**')) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith('*') && p.endsWith('*') && p.length > 2) return <em key={i}>{p.slice(1, -1)}</em>;
    if (p.startsWith('`') && p.endsWith('`')) return <code key={i} style={{ background: 'var(--soft)', padding: '1px 5px', borderRadius: 4, fontSize: '0.92em' }}>{p.slice(1, -1)}</code>;
    const lm = p.match(/^\[([^\]]*)\]\(([^)]*)\)$/);
    if (lm) {
      const href = lm[2];
      if (/^(https?:|#|\/)/.test(href)) {
        return <a key={i} href={href} target="_blank" rel="noreferrer"
          style={{ color: 'var(--accent)', textDecoration: 'underline' }}>{lm[1]}</a>;
      }
      return lm[0];
    }
    if (p.startsWith('~~') && p.endsWith('~~')) return <del key={i} style={{ color: 'var(--text-dim)' }}>{p.slice(2, -2)}</del>;
    const cm = p.match(/^【《([^》]+)》·?([^】]*)】$/);
    if (cm) return <CiteLink key={i} book={cm[1]} chapter={cm[2]} />;
    const cm2 = p.match(/^【([^】]+)】$/);
    if (cm2) return <CiteLink key={i} book={cm2[1]} chapter="" />;
    return p;
  });
}

/* ── mermaid 代码清洗（LLM 常产出非法语法, 尽量救回来） ── */
export function sanitizeMermaid(code) {
  let c = (code || '').replace(/\r/g, '');
  // 1) 引号内的裸换行 → <br/>（mermaid 节点文本不允许换行）
  c = c.replace(/"([^"]*)"/g, (m, inner) =>
    inner.includes('\n') ? '"' + inner.replace(/\n+/g, '<br/>') + '"' : m);
  // 2) 一行式 mindmap → 拆成多行（保护括号/引号内容不被空格拆碎; mindmap/root 关键字不缩进, 其余缩进为一级）
  const t = c.trim();
  if (/^mindmap\b/.test(t) && !t.includes('\n')) {
    const protectedParts = [];
    const masked = t.replace(/\(\([^)]*\)\)|"[^"]*"/g, m => {
      protectedParts.push(m);
      return `\x00${protectedParts.length - 1}\x00`;
    });
    const tokens = masked.split(/\s+/).map(tok =>
      tok.replace(/\x00(\d+)\x00/g, (_, idx) => protectedParts[+idx]));
    if (tokens.length > 1) {
      c = tokens.map((tok, idx) =>
        idx === 0 || tok.startsWith('root') ? tok : '  ' + tok).join('\n');
    }
  }
  return c;
}

const renderMermaid = (code, onEdit, drawioXml, t) => {
  if (drawioXml) {
    return <DrawioInline xml={drawioXml} onEdit={() => onEdit && onEdit(code)} />;
  }
  return (
  <div style={{ position: 'relative', margin: '10px 0' }}>
    <div className="mermaid"
      style={{ display: 'flex', justifyContent: 'center', overflowX: 'auto' }}>
      {sanitizeMermaid(code)}
    </div>
    {onEdit && (
      <button onClick={() => onEdit(code)} title={t ? t('drawioEdit') : 'draw.io edit'}
        style={{ position: 'absolute', top: 0, right: 0, fontSize: 11, cursor: 'pointer',
                 padding: '3px 8px', borderRadius: 6, border: '1px solid var(--border)',
                 background: 'var(--card-bg)', color: 'var(--text-dim)' }}>
        {t ? t('drawioEdit') : '✏️ draw.io'}
      </button>
    )}
  </div>
  );
};

/* ── markdown 表格渲染 ── */
let outSeq = 0;
function renderTable(headers, rows) {
  return (
    <div key={`tbl${outSeq++}`} style={{ overflowX: 'auto', margin: '10px 0' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13, lineHeight: 1.6 }}>
        <thead>
          <tr>{headers.map((h, i) => (
            <th key={i} style={{ border: '1px solid var(--border)', padding: '6px 10px',
                                background: 'var(--soft)', fontWeight: 600, textAlign: 'left' }}>
              {renderInline(h)}
            </th>
          ))}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{r.map((c, j) => (
              <td key={j} style={{ border: '1px solid var(--border)', padding: '6px 10px' }}>{renderInline(c)}</td>
            ))}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function renderMarkdown(text, onEdit, drawioXml, t) {
  const lines = (text || '').split('\n');
  const out = [];
  let fence = null;         // 围栏语言（''=普通代码块, 'mermaid'=脑图）
  let fenceLines = [];
  const flushFence = () => {
    if (fence !== null) {
      const code = fenceLines.join('\n');
      if (fence === 'mermaid') {
        // mermaid 脑图: 由 useEffect 里 mermaid.run() 渲染成图形
        out.push(renderMermaid(code, onEdit, drawioXml, t));
      } else {
        out.push(<pre key={`p${out.length}`} style={{ background: 'var(--soft)', padding: '10px 12px', borderRadius: 8, overflowX: 'auto', fontSize: 12.5, lineHeight: 1.6 }}>{code}</pre>);
      }
      fenceLines = [];
    }
    fence = null;
  };
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (fence !== null) {
      if (trimmed.startsWith('```')) flushFence();
      else fenceLines.push(line);
      i++; continue;
    }
    const fm = trimmed.match(/^```(\w*)\s*$/);
    if (fm) { fence = fm[1] || ''; i++; continue; }
    // 裸 mermaid 块兜底: flowchart/graph/mindmap 开头 → 收集到空行为止, 按 mermaid 渲染（无围栏时）
    if (/^(flowchart|graph)\s+(TD|LR|TB|RL|BT)\b/.test(trimmed) || /^mindmap\b/.test(trimmed)) {
      const block = [trimmed];
      let j = i + 1;
      while (j < lines.length && lines[j].trim() !== '') { block.push(lines[j]); j++; }
      out.push(renderMermaid(block.join('\n'), null, null, t));
      i = j; continue;
    }
    // 表格: | 开头 + 下一行为分隔行（|---|---|）→ 收集整块渲染为 <table>
    if (trimmed.startsWith('|') && i + 1 < lines.length &&
        /^\|[\s\-:|]+\|?$/.test(lines[i + 1].trim()) && lines[i + 1].includes('-')) {
      const headers = trimmed.split('|').slice(1, -1).map(c => c.trim());
      const rows = [];
      let j = i + 2;
      while (j < lines.length && lines[j].trim().startsWith('|')) {
        rows.push(lines[j].trim().split('|').slice(1, -1).map(c => c.trim()));
        j++;
      }
      out.push(renderTable(headers, rows));
      i = j; continue;
    }
    const imgMatch = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imgMatch) {
      out.push(
        <div key={i} style={{ margin: '8px 0' }}>
          <img src={imgMatch[2]} alt={imgMatch[1]}
            style={{ maxWidth: '100%', maxHeight: 480, borderRadius: 8, border: '1px solid var(--border)' }} />
        </div>
      );
      i++; continue;
    }
    if (trimmed.startsWith('> ')) {
      out.push(<blockquote key={i} style={{ margin: '8px 0', padding: '6px 12px', borderLeft: '3px solid var(--border)', color: 'var(--text-dim)', background: 'var(--soft)', borderRadius: 4 }}>{renderInline(trimmed.slice(2))}</blockquote>);
    } else if (/^[-*] \[[ xX]\] /.test(trimmed)) {
      // 任务列表 - [x] / - [ ]
      const checked = /^[-*] \[[xX]\] /.test(trimmed);
      out.push(<div key={i} style={{ paddingLeft: '1.2em', margin: '2px 0', display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span style={{ color: checked ? '#6fae6f' : 'var(--text-dim)', fontSize: 12 }}>{checked ? '☑' : '☐'}</span>
        <span style={{ textDecoration: checked ? 'line-through' : 'none', color: checked ? 'var(--text-dim)' : 'inherit' }}>
          {renderInline(trimmed.replace(/^[-*] \[[ xX]\] /, ''))}
        </span>
      </div>);
    } else if (/^\s{2,}[-*] /.test(line)) {
      // 嵌套列表（缩进子项）
      const depth = Math.min(Math.floor((line.length - line.trimStart().length) / 2), 4);
      out.push(<div key={i} style={{ paddingLeft: `${1.2 + depth * 1.2}em`, margin: '1px 0' }}>· {renderInline(trimmed.replace(/^[-*] /, ''))}</div>);
    } else if (/^[-*] |^\d+\. /.test(trimmed)) {
      out.push(<div key={i} style={{ paddingLeft: '1.2em', margin: '2px 0' }}>· {renderInline(trimmed.replace(/^[-*] |^\d+\. /, ''))}</div>);
    } else if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      // 水平分割线 --- *** ___
      out.push(<hr key={i} style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '12px 0' }} />);
    } else if (trimmed.startsWith('#### ')) {
      out.push(<div key={i} style={{ fontWeight: 600, fontSize: 12.5, margin: '8px 0 3px', color: 'var(--text-dim)' }}>{renderInline(trimmed.slice(5))}</div>);
    } else if (trimmed.startsWith('### ')) {
      out.push(<div key={i} style={{ fontWeight: 600, fontSize: 13.5, margin: '10px 0 4px', color: 'var(--text-dim)' }}>{renderInline(trimmed.slice(4))}</div>);
    } else if (trimmed.startsWith('## ')) {
      out.push(<div key={i} style={{ fontWeight: 600, fontSize: 14.5, margin: '12px 0 4px' }}>{renderInline(trimmed.slice(3))}</div>);
    } else if (trimmed.startsWith('# ')) {
      out.push(<div key={i} style={{ fontWeight: 600, fontSize: 16, margin: '14px 0 6px' }}>{renderInline(trimmed.slice(2))}</div>);
    } else if (!trimmed) {
      out.push(<div key={i} style={{ height: '6px' }} />);
    } else {
      out.push(<div key={i} style={{ margin: '2px 0' }}>{renderInline(trimmed)}</div>);
    }
    i++;
  }
  flushFence();
  return out;
}
