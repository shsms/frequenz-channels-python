# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Tests for the rust module."""

from _frequenz_channels_rust_impl._channels_impl import BcastChannel


async def test_bcast_channel() -> None:
    """Test BcastChannel."""
    channel: BcastChannel[int] = BcastChannel()
    sender = channel.new_sender()
    receiver = channel.new_receiver()
    sender.send(1)
    receiver.ready()
    assert await receiver.consume() == 1

# def test_sum_as_string() -> None:
#     """Test sum_as_string."""
#     assert sum_as_string(1, 2) == "3"
