"""Cancel-safe memory transactions for the general agent's synchronous tools.

Python cannot stop a running worker thread. Its detached memory changes must not
outlive a cancelled request, and a later call must wait until that worker really
finishes. Locks are keyed by the route's authenticated conversation scope.
"""
import asyncio
from copy import deepcopy
import threading

from deep_context import current_memory_overlay
import guard


STATEFUL_TOOLS = frozenset({
    "philosopher_debate", "socratic_tutor", "write_essay", "generate_image", "thought_experiment",
})
_locks = {}
_registry_lock = threading.Lock()
_memory_lock = threading.Lock()


def _acquire_entry(key):
    with _registry_lock:
        entry = _locks.setdefault(key, {"lock": threading.Lock(), "users": 0})
        entry["users"] += 1
        return entry


def _release_entry(key, entry):
    with _registry_lock:
        entry["users"] -= 1
        if not entry["users"]:
            _locks.pop(key, None)


async def execute_stateful(func, args, timeout):
    """Execute once, committing memory only if the awaiting request still exists.

    Raise asyncio.TimeoutError/CancelledError normally. Callers must not retry
    these non-idempotent operations automatically. Local memory rolls back;
    already submitted external generation requests cannot be recalled.
    """
    from routes import agent_core as core
    key = guard.user_memory_key()
    cancelled = threading.Event()
    completion_lock = threading.Lock()

    def run():
        if cancelled.is_set():
            return None
        entry = _acquire_entry(key)
        try:
            with entry["lock"]:
                if cancelled.is_set():
                    return None
                with _memory_lock:
                    slot = core._mem_slot()
                    overlay = deepcopy(slot)
                token = current_memory_overlay.set(overlay)
                try:
                    result = func(**args)
                finally:
                    current_memory_overlay.reset(token)
                failed = isinstance(result, dict) and (result.get("error") or result.get("accepted") is False)
                if not failed:
                    committed = deepcopy(overlay)
                    # Cancellation and commit have one linearization boundary:
                    # after the timeout/cancel has returned, no late write can
                    # occur. A commit already in progress finishes first.
                    with completion_lock:
                        if not cancelled.is_set():
                            with _memory_lock:
                                slot.clear()
                                slot.update(committed)
                                core._save_agent_memory()
                return result
        finally:
            _release_entry(key, entry)

    try:
        return await asyncio.wait_for(asyncio.to_thread(run), timeout=timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        with completion_lock:
            cancelled.set()
        raise
