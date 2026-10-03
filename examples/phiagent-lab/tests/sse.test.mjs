import test from 'node:test';
import assert from 'node:assert/strict';
import { createSSEParser, readEvents } from '../web/sse.mjs';

test('SSE handles every byte boundary, Chinese UTF-8, CRLF and adjacent frames', async () => {
  const raw = ': heartbeat\r\n\r\ndata: {"type":"token","text":"自由"}\r\n\r\ndata: {"type":"done"}\n\n';
  const bytes = new TextEncoder().encode(raw);
  const body = new ReadableStream({ start(controller) {
    for (let i = 0; i < bytes.length; i++) controller.enqueue(bytes.slice(i, i + 1));
    controller.close();
  } });
  const events = [];
  await readEvents(new Response(body), event => events.push(event));
  assert.deepEqual(events, [{ type: 'token', text: '自由' }, { type: 'done' }]);
});
test('partial frame is an error', () => {
  const parser = createSSEParser(() => {});
  parser.feed('data: {"x":1}');
  assert.throws(() => parser.finish(), /不完整/);
});
test('HTTP errors are not interpreted as event streams', async () => {
  await assert.rejects(readEvents(new Response('', { status: 422 }), () => {}), /422/);
});
