// The user's task and quoted material have different meanings. Keep them
// separate, including when the user sends a file without any written request.
export const ATTACHMENT_INPUT_PREFIX = '【本轮用户要求与附件材料】\n';

export function attachmentMessage(request, files = []) {
  if (!files.length) return request;
  return ATTACHMENT_INPUT_PREFIX + JSON.stringify({
    schema: 'phiagent-input-v1',
    user_request: request,
    attachments: files.map(file => ({
      filename: file.filename,
      kind: file.kind,
      truncated: !!file.truncated,
      content: file.content || '',
    })),
  });
}
