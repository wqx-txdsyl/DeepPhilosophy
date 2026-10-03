import test from 'node:test';
import assert from 'node:assert/strict';
import { reduceEvent } from '../exercises/ownership.mjs';

const fresh = () => ({conversations: {a: {}, b: {}}, activeConversationId: 'b',
  runs: {a: {id: 'run-a', text: '', status: 'streaming'}}});
test('a late A event writes A while B is selected', () => {
  const state = fresh();
  const next = reduceEvent(state, {type:'token',conversationId:'a',invocationId:'run-a',text:'自由'});
  assert.equal(next.runs.a.text,'自由');
  assert.equal(state.runs.a.text,'');
  assert.equal(next.activeConversationId,'b');
});
test('deleted conversation ignores events', () => {
  const state = fresh();
  delete state.conversations.a;
  assert.equal(reduceEvent(state,{type:'token',conversationId:'a',invocationId:'run-a',text:'x'}),state);
});
test('old invocation cannot write a new run', () => {
  const state = fresh();
  assert.equal(reduceEvent(state,{type:'token',conversationId:'a',invocationId:'older-run',text:'x'}),state);
});
test('done seals output against late tokens', () => {
  const state = reduceEvent(fresh(),{type:'done',conversationId:'a',invocationId:'run-a',text:'最终答案'});
  assert.equal(state.runs.a.status,'completed');
  assert.equal(reduceEvent(state,{type:'token',conversationId:'a',invocationId:'run-a',text:'x'}),state);
});
