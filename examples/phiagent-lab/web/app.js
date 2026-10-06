import { readEvents } from './sse.mjs';
const $ = selector => document.querySelector(selector);
let cid = localStorage.getItem('phi-course-conversation') || crypto.randomUUID();
localStorage.setItem('phi-course-conversation', cid);
let controller = null;

function addMessage(role, content) {
  const node = document.createElement('article');
  node.dataset.role = role;
  node.textContent = content;
  $('#messages').append(node);
  return node;
}
function busy(value) {
  $('#send').disabled = value;
  $('#new').disabled = value;
  $('#stop').disabled = !value;
}
function showSource(source) {
  const details = document.createElement('details');
  const title = document.createElement('summary');
  title.textContent = `${source.title} [${source.id}]`;
  const text = document.createElement('p');
  text.textContent = `${source.source}：${source.text}`;
  details.append(title, text);
  $('#sources').append(details);
}
$('#stop').onclick = () => controller?.abort();
$('#new').onclick = () => {
  cid = crypto.randomUUID();
  localStorage.setItem('phi-course-conversation', cid);
  $('#messages').replaceChildren();
  $('#sources').replaceChildren();
  $('#status').textContent = '新会话';
};
$('#form').onsubmit = async event => {
  event.preventDefault();
  if (controller) return;
  const question = $('#question').value.trim();
  if (!question) return;
  controller = new AbortController();
  busy(true);
  addMessage('user', question);
  const answer = addMessage('assistant', '');
  $('#sources').replaceChildren();
  let completed = false;
  try {
    const response = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: cid, message: question }), signal: controller.signal,
    });
    await readEvents(response, data => {
      if (data.type === 'status') $('#status').textContent = data.text;
      if (data.type === 'tool') $('#status').textContent = `调用工具：${data.name}`;
      if (data.type === 'source') showSource(data.source);
      if (data.type === 'token') answer.textContent += data.text;
      if (data.type === 'error') throw new Error(`${data.message} 请求编号：${data.request_id}`);
      if (data.type === 'done') {
        completed = true;
        answer.textContent = data.text;
        $('#status').textContent = '已完成并保存';
      }
    });
    if (!completed) throw new Error('连接结束，但没有完成事件');
  } catch (error) {
    answer.textContent = '[本轮未确认完成；已清除未通过最终验收的文字]';
    $('#status').textContent = error.name === 'AbortError' ? '已停止；刷新可核对服务端保存状态' : error.message;
  } finally {
    controller = null;
    busy(false);
  }
};

async function boot() {
  busy(true);
  try {
    const healthResponse = await fetch('/api/health');
    if (!healthResponse.ok) throw new Error('健康检查失败');
    const health = await healthResponse.json();
    $('#mode').textContent = health.mode === 'mock' ? '离线脚本演示' : '真实模型';
    const response = await fetch(`/api/conversations/${cid}`);
    if (!response.ok) throw new Error('历史读取失败；点击新会话可重新开始');
    const history = await response.json();
    for (const item of history) addMessage(item.role, item.content);
  } catch (error) { $('#status').textContent = error.message; }
  finally { busy(false); }
}
boot();
