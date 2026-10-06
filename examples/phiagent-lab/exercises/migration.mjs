import assert from 'node:assert/strict';

export function appendToken(messages, id, text) {
  return messages.map(message => message.id === id
    ? {...message, content: message.content + text} : message);
}
const original = [{id: 'a', content: ''}, {id: 'b', content: '保留'}];
const next = appendToken(original, 'a', '自由');
assert.equal(original[0].content, '');
assert.equal(next[0].content, '自由');
assert.equal(next[1], original[1]);
console.log('不可变更新练习通过');
console.log('A');
Promise.resolve().then(() => console.log('B'));
console.log('C');
