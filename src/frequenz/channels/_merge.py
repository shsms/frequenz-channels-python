# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Merge messages coming from multiple receivers into a single receiver.

# Usage

If you just need to receive the same type of messages but from multiple sources in one
stream, you can use [`merge()`][frequenz.channels.merge] to create a new receiver that
will receive messages from all the given receivers:

```python
from frequenz.channels import Anycast, Receiver, merge

channel1: Anycast[int] = Anycast(name="channel1")
channel2: Anycast[int] = Anycast(name="channel2")
receiver1 = channel1.new_receiver()
receiver2 = channel2.new_receiver()

async for value in merge(receiver1, receiver2):
    print(value)
```

If the first message comes from `channel2` and the second message from `channel1`, the
first message will be received immediately, and the second message will be received as
soon as it is available.

This can be helpful when you just need to receive messages and don't care about
where are they coming from specifically. If you need to know where the message came
from, you can use [`select()`][frequenz.channels.select] instead.

# Stopping

A merge receiver will be stopped automatically when all the receivers that it merges are
stopped. When using the async iterator interface, this means that the iterator will stop
as soon as all the receivers are stopped. When using
[`receive()`][frequenz.channels.Receiver.receive], this means that the method will raise
a [`ReceiverStoppedError`][frequenz.channels.ReceiverStoppedError] exception as soon as
all the receivers are stopped.

If you want to stop a merge receiver manually, you can use the
[`stop()`][frequenz.channels.Merger.stop] method.

When using [`receive()`][frequenz.channels.Receiver.receive], you should make sure to
either stop all the receivers that you are merging, or to stop the merge receiver
manually. This is to make sure that all the tasks created by the merge receiver are
cleaned up properly.
"""

from __future__ import annotations

import asyncio
import itertools
from collections import deque
from typing import Any, TypeVar

from ._receiver import Receiver, ReceiverStoppedError

_T = TypeVar("_T")


def merge(*receivers: Receiver[_T]) -> Merger[_T]:
    """Merge messages coming from multiple receivers into a single stream.

    Example:
        For example, if there are two channel receivers with the same type,
        they can be awaited together, and their results merged into a single
        stream like this:

        ```python
        from frequenz.channels import Broadcast

        channel1 = Broadcast[int](name="input-chan-1")
        channel2 = Broadcast[int](name="input-chan-2")
        receiver1 = channel1.new_receiver()
        receiver2 = channel2.new_receiver()

        async for msg in merge(receiver1, receiver2):
            print(f"received {msg}")
        ```

    Args:
        *receivers: The receivers to merge.

    Returns:
        A receiver that merges the messages coming from multiple receivers into a
            single stream.

    Raises:
        ValueError: if no receivers are provided.
    """
    if not receivers:
        raise ValueError("At least one receiver must be provided")

    return Merger(*receivers, name="merge")


class Merger(Receiver[_T]):
    """A receiver that merges messages coming from multiple receivers into a single stream.

    Tip:
        Please consider using the more idiomatic [`merge()`][frequenz.channels.merge]
        function instead of creating a `Merger` instance directly.
    """

    def __init__(self, *receivers: Receiver[_T], name: str | None) -> None:
        """Create a `Merger` instance.

        Args:
            *receivers: The receivers to merge.
            name: The name of the receiver. Used to create the string representation
                of the receiver.
        """
        self._receivers: dict[str, Receiver[_T]] = {
            str(id): recv for id, recv in enumerate(receivers)
        }
        self._name: str = name if name is not None else type(self).__name__
        self._pending: set[asyncio.Task[Any]] = {
            asyncio.create_task(anext(recv), name=name)
            for name, recv in self._receivers.items()
        }
        self._results: deque[_T] = deque(maxlen=len(self._receivers))

    def __del__(self) -> None:
        """Cleanup any pending tasks."""
        for task in self._pending:
            if not task.done() and task.get_loop().is_running():
                task.cancel()

    async def stop(self) -> None:
        """Stop the `Merger` instance and cleanup any pending tasks."""
        for task in self._pending:
            task.cancel()
        await asyncio.gather(*self._pending, return_exceptions=True)
        self._pending = set()

    async def ready(self) -> bool:
        """Wait until the receiver is ready with a value or an error.

        Once a call to `ready()` has finished, the value should be read with
        a call to `consume()` (`receive()` or iterated over). The receiver will
        remain ready (this method will return immediately) until it is
        consumed.

        Returns:
            Whether the receiver is still active.
        """
        # we use a while loop to continue to wait for new data, in case the
        # previous `wait` completed because a channel was closed.
        while True:
            # if there are messages waiting to be consumed, return immediately.
            if len(self._results) > 0:
                return True

            # if there are no more pending receivers, we return immediately.
            if len(self._pending) == 0:
                return False

            done, self._pending = await asyncio.wait(
                self._pending, return_when=asyncio.FIRST_COMPLETED
            )
            for item in done:
                name = item.get_name()
                # if channel is closed, don't add a task for it again.
                if isinstance(item.exception(), StopAsyncIteration):
                    continue
                result = item.result()
                self._results.append(result)
                self._pending.add(
                    asyncio.create_task(anext(self._receivers[name]), name=name)
                )

    def consume(self) -> _T:
        """Return the latest value once `ready` is complete.

        Returns:
            The next value that was received.

        Raises:
            ReceiverStoppedError: if the receiver stopped producing messages.
            ReceiverError: if there is some problem with the receiver.
        """
        if not self._results and not self._pending:
            raise ReceiverStoppedError(self)

        assert self._results, "`consume()` must be preceded by a call to `ready()`"

        return self._results.popleft()

    def __str__(self) -> str:
        """Return a string representation of this receiver."""
        if len(self._receivers) > 3:
            receivers = [str(p) for p in itertools.islice(self._receivers.values(), 3)]
            receivers.append("…")
        else:
            receivers = [str(p) for p in self._receivers.values()]
        return f"{self._name}:{','.join(receivers)}"

    def __repr__(self) -> str:
        """Return a string representation of this receiver."""
        return (
            f"{self._name}("
            f"{', '.join(f'{k}={v!r}' for k, v in self._receivers.items())})"
        )
