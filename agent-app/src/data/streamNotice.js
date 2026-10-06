/** Display-only error classification. Keep the original message error for diagnostics. */
export function streamNotice({ state, error, hasContent = false, hasQuestion = false, zh = true }) {
  const raw = typeof error === 'string' ? error : error ? JSON.stringify(error) : '';
  const code = raw.match(/(?:error\s*code|http|status(?:_code)?)\s*[:=(]?\s*(\d{3})\b/i)?.[1] || '';
  const requestId = raw.match(/request[_ -]?id[\s'":=]+([a-z0-9][a-z0-9_-]{5,127})/i)?.[1] || '';
  let kind = 'unknown';
  if (state === 'stopped') kind = 'stopped';
  else if (code === '402' || /insufficient[_\s-]*(?:balance|quota)|余额不足|额度不足/i.test(raw)) kind = 'quota';
  else if (/invalid[_\s-]*api[_\s-]*key|incorrect api key|authenticationerror|api.?key.*(?:invalid|missing)/i.test(raw)) kind = 'configuration';
  else if (code === '401' || /登录.*(?:过期|失效)|未登录/i.test(raw)) kind = 'auth';
  else if (code === '403') kind = 'access';
  else if (code === '429' || /rate.?limit|too many requests|quota[_\s-]*exceeded/i.test(raw)) kind = 'rate';
  else if (['500', '502', '503', '504', '524'].includes(code)) kind = 'service';
  else if (state === 'interrupted' || /network|failed to fetch|load failed|timeout|timed out|连接|网络|超时|中断/i.test(raw)) kind = 'network';
  const messages = {
    quota: ['暂时无法生成回答', '模型服务额度不足，需管理员补充额度后恢复。', 'Unable to generate an answer', 'The model service is out of credits. An administrator needs to replenish them.'],
    configuration: ['模型服务暂不可用', '模型服务的认证配置异常，需要管理员处理。', 'Model service unavailable', 'The model service authentication needs attention from an administrator.'],
    auth: ['登录状态需要更新', '请重新登录后再试。', 'Please sign in again', 'Your sign-in needs to be renewed before you retry.'],
    access: ['暂时无法访问服务', '当前请求未获授权，请联系管理员确认。', 'Service access unavailable', 'This request was not authorized. Please contact an administrator.'],
    rate: ['请求有点拥挤', '请稍等片刻再试。', 'Too many requests', 'Please wait a moment before trying again.'],
    service: ['服务暂时没有响应', '请稍后重试。', 'Service temporarily unavailable', 'Please try again shortly.'],
    network: ['连接中断了', '请检查网络后重试。', 'Connection interrupted', 'Check your connection and try again.'],
    stopped: ['已停止生成', hasContent ? '你可以从这里继续。' : '准备好后，可以重新生成。', 'Generation stopped', hasContent ? 'You can continue from here.' : 'You can try again when you are ready.'],
    unknown: ['这次回答未能完成', '请稍后重试；若持续出现，可将错误信息反馈给管理员。', 'This answer could not be completed', 'Try again shortly. If the issue persists, share the error information with an administrator.'],
  };
  const text = messages[kind];
  const canRetry = !['quota', 'configuration', 'auth', 'access'].includes(kind) && (hasContent || hasQuestion);
  const action = canRetry ? (hasContent ? 'continue' : 'retry') : null;
  const diagnostics = [zh ? `问题类型：${kind}` : `Issue: ${kind}`, ...(code ? [`HTTP ${code}`] : []), ...(requestId ? [`Request ID: ${requestId}`] : [])].join('\n');
  return { kind, code, requestId, title: text[zh ? 0 : 2], description: text[zh ? 1 : 3], action,
    actionLabel: action === 'continue' ? (zh ? '继续回答' : 'Continue answer') : (zh ? '重新生成' : 'Try again'),
    retained: hasContent ? (zh ? '已生成的内容保留在上方。' : 'The answer so far is kept above.') : '', diagnostics };
}
