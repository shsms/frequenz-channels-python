# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Pipe between a receiver and a sender.

The `Pipe` class takes a receiver and a sender and creates a pipe between them by
forwarding all the messages received by the receiver to the sender.
"""

from __future__ import annotations

import asyncio
import typing

from .._generic import ChannelMessageT
from .._receiver import Receiver
from .._sender import Sender


class Pipe(typing.Generic[ChannelMessageT]):
    """A pipe between two channels.

    The `Pipe` class takes a receiver and a sender and creates a pipe between them
    by forwarding all the messages received by the receiver to the sender.

    Example:
        ```python
        from frequenz.channels import Broadcast, Pipe

        channel1: Broadcast[int] = Broadcast(name="channel1")
        channel2: Broadcast[int] = Broadcast(name="channel2")

        receiver_chan1 = channel1.new_receiver()
        sender_chan2 = channel2.new_sender()

        async with Pipe(channel2.new_receiver(), channel1.new_sender()):
            await sender_chan2.send(10)
            assert await receiver_chan1.receive() == 10
        ```
    """

    def __init__(
        self, receiver: Receiver[ChannelMessageT], sender: Sender[ChannelMessageT]
    ) -> None:
        """Create a new pipe between two channels.

        Args:
            receiver: The receiver channel.
            sender: The sender channel.
        """
        self._sender = sender
        self._receiver = receiver
        self._task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> Pipe[ChannelMessageT]:
        """Enter the runtime context."""
        await self.start()
        return self

    async def __aexit__(
        self,
        _exc_type: typing.Type[BaseException],
        _exc: BaseException,
        _tb: typing.Any,
    ) -> None:
        """Exit the runtime context."""
        await self.stop()

    async def start(self) -> None:
        """Start this pipe if it is not already running."""
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop this pipe."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        async for value in self._receiver:
            await self._sender.send(value)
