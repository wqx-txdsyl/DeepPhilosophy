export function reduceEvent(state, event) {
  const run = state.runs[event.conversationId];
  if (!state.conversations[event.conversationId]) return state;
  if (!run || run.id !== event.invocationId) return state;
  if (run.status !== 'streaming') return state;
  if (event.type === 'token') {
    return {...state, runs: {...state.runs,
      [event.conversationId]: {...run, text: run.text + event.text}}};
  }
  if (event.type === 'done') {
    return {...state, runs: {...state.runs,
      [event.conversationId]: {...run, text: event.text, status: 'completed'}}};
  }
  return state;
}
