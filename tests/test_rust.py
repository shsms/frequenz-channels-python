# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Tests for the rust module."""

from _frequenz_channels_rust_impl import FastBroadcast


async def test_bcast_channel() -> None:
    """Test BcastChannel."""
    channel: FastBroadcast[int] = FastBroadcast("test")
    sender = channel.new_sender()
    receiver = channel.new_receiver()
    await sender.send(1)
    assert await receiver.receive() == 1

# def test_sum_as_string() -> None:
#     """Test sum_as_string."""
#     assert sum_as_string(1, 2) == "3"
