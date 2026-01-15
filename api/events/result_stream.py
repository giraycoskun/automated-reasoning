import asyncio
from collections import defaultdict
from typing import AsyncIterator, Dict, Set


class ResultStreamer:
    def __init__(self) -> None:
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)

    async def publish(self, puzzle_id: str, message: dict) -> None:
        queues = list(self._subscribers.get(puzzle_id, set()))
        for queue in queues:
            queue.put_nowait(message)

    async def stream(self, puzzle_id: str) -> AsyncIterator[dict]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[puzzle_id].add(queue)
        try:
            while True:
                data = await queue.get()
                yield data
        finally:
            self._subscribers[puzzle_id].discard(queue)
            if not self._subscribers[puzzle_id]:
                self._subscribers.pop(puzzle_id, None)
