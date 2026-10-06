const PROFILE_FIELDS = ['nickname', 'occupation', 'about', 'custom_instructions', 'language'];

export function accountProfile(data) {
  const fields = data?.profile && typeof data.profile === 'object' ? data.profile : {};
  return { id: data?.id, username: data?.username,
    ...Object.fromEntries(PROFILE_FIELDS.filter(k => typeof fields[k] === 'string').map(k => [k, fields[k]])) };
}

export function profilePatch(data) {
  return Object.fromEntries(PROFILE_FIELDS.filter(k => typeof data?.[k] === 'string').map(k => [k, data[k]]));
}

/** Never clear unsaved account history, or another account's device cache. */
export function clearDeviceCache(store, sync, storage) {
  if (sync && (!sync.active() || !sync.hydrated || sync.queue.size || sync.busy.size)) throw new Error('SYNC_PENDING');
  storage.removeItem(store.key);
  if (sync) storage.removeItem(sync.metaKey);
}

export async function deleteConversationHistory(store, sync) {
  const owner = store.owner;
  if (sync) {
    if (!sync.active() || sync.busy.size) throw new Error('HISTORY_BUSY');
    await sync.hydrate();
    if (!sync.active() || store.owner !== owner) throw new Error('ACCOUNT_CHANGED');
  }
  store.deleteAllConversations();
  if (!sync) return;
  try {
    while (sync.queue.size) {
      if (!sync.active() || store.owner !== owner) throw new Error('ACCOUNT_CHANGED');
      await sync.flush();
    }
  } catch { throw new Error('HISTORY_DELETE_PENDING'); }
}
