import { getApiBase } from '../utils/api';

export function projectApi(token) {
  return async (path = '', options = {}) => {
    const response = await fetch(`${getApiBase()}/api/projects${path}`, {
      ...options, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: options.body === undefined ? undefined : JSON.stringify(options.body), cache: 'no-store',
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(typeof data.detail === 'string' ? data.detail : response.status === 422 ? '内容格式不正确或超过长度限制。' : '项目请求失败，请重试。');
      error.status = response.status; throw error;
    }
    return data;
  };
}

export const objectId = () => crypto.randomUUID();
export function blankProject(title,question) {
  return { title: title.trim(), question: question.trim(), brief: '', sources: [], objects: [
    { id: objectId(), kind: 'document', title: '研究文稿', content: '', versions: [] },
    { id: objectId(), kind: 'debate', title: '争点与异议', content: '', versions: [] },
    { id: objectId(), kind: 'action', title: '行动与反馈', content: '', versions: [] },
  ] };
}

export function downloadProject(data, name, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([typeof data === 'string' ? data : JSON.stringify(data,null,2)],{type}));
  const a = document.createElement('a'); a.href=url; a.download=name.replace(/[\\/:*?"<>|]/g,'-'); a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
