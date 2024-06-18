# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Tests for the Pipe class."""


import asyncio
import typing

from frequenz.channels import Broadcast, Receiver
from frequenz.channels.experimental import Pipe

T = typing.TypeVar("T")


class Timeout:
    """Sentinel for timeout."""


async def receive_timeout(recv: Receiver[T], timeout: float = 0.1) -> T | type[Timeout]:
    """Receive message from receiver with timeout."""
    try:
        return await asyncio.wait_for(recv.receive(), timeout=timeout)
    except asyncio.TimeoutError:
        return Timeout


async def test_pipe() -> None:
    """Test pipe."""
    channel1: Broadcast[int] = Broadcast(name="channel1")
    channel2: Broadcast[int] = Broadcast(name="channel2")

    sender_chan1 = channel1.new_sender()
    sender_chan2 = channel2.new_sender()
    receiver_chan1 = channel1.new_receiver()
    receiver_chan2 = channel2.new_receiver()

    async with Pipe(channel2.new_receiver(), channel1.new_sender()):
        await sender_chan2.send(42)
        assert await receive_timeout(receiver_chan1) == 42
        assert await receive_timeout(receiver_chan2) == 42

        await sender_chan2.send(-2)
        assert await receive_timeout(receiver_chan1) == -2
        assert await receive_timeout(receiver_chan2) == -2

        await sender_chan1.send(43)
        assert await receive_timeout(receiver_chan1) == 43
        assert await receive_timeout(receiver_chan2) is Timeout

        await sender_chan2.send(5)
        assert await receive_timeout(receiver_chan1) == 5
        assert await receive_timeout(receiver_chan2) == 5

    await sender_chan2.send(5)
    assert await receive_timeout(receiver_chan1) is Timeout
    assert await receive_timeout(receiver_chan2) == 5
