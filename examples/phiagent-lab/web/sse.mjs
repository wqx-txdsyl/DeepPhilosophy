// Incremental framing: network chunks are not SSE events or complete UTF-8 text.
export function createSSEParser(onEvent) {
  let buffer = '';
  function consume() {
    let match;
    while ((match = /\r?\n\r?\n/.exec(buffer))) {
      const frame = buffer.slice(0, match.index);
      buffer = buffer.slice(match.index + match[0].length);
      const data = frame.split(/\r?\n/).filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).replace(/^ /, '')).join('\n');
      if (data) onEvent(JSON.parse(data));
    }
  }
  return {
    feed(text) { buffer += text; consume(); },
    finish() { consume(); if (buffer.trim()) throw new Error('不完整的 SSE 事件'); },
  };
}

export async function readEvents(response, onEvent) {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  if (!response.body) throw new Error('浏览器未提供响应流');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const parser = createSSEParser(onEvent);
  let done = false;
  try {
    while (true) {
      const result = await reader.read();
      if (result.done) { done = true; break; }
      parser.feed(decoder.decode(result.value, { stream: true }));
    }
    parser.feed(decoder.decode());
    parser.finish();
  } finally {
    if (!done) await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
