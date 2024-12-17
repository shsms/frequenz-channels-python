# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Tests for the merge implementation."""

import pytest

from frequenz.channels import merge, ReceiverStoppedError, Anycast


async def test_empty() -> None:
    """Ensure merge() raises an exception when no receivers are provided."""
    with pytest.raises(ValueError, match="At least one receiver must be provided"):
        merge()


async def test_merge_close_behavior() -> None:
    """Ensure that all underlying receivers are closed and ReceiverStoppedError is raised for merge."""
    chan1 = Anycast[int](name="chan1")
    chan2 = Anycast[int](name="chan2")

    receiver1 = chan1.new_receiver()
    receiver2 = chan2.new_receiver()

    merger = merge(receiver1, receiver2)

    merger.close()

    with pytest.raises(ReceiverStoppedError):
        await merger.receive()
