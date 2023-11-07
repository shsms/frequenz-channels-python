# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Base classes for Channel Sender and Receiver."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

from ._exceptions import ReceiverStoppedError

_T = TypeVar("_T")
_U = TypeVar("_U")


class Sender(ABC, Generic[_T]):
    """A channel Sender."""

    @abstractmethod
    async def send(self, msg: _T) -> None:
        """Send a message to the channel.

        Args:
            msg: The message to be sent.

        Raises:
            SenderError: if there was an error sending the message.
        """


class Receiver(ABC, Generic[_T]):
    """A channel Receiver."""

    async def __anext__(self) -> _T:
        """Await the next value in the async iteration over received values.

        Returns:
            The next value received.

        Raises:
            StopAsyncIteration: if the receiver stopped producing messages.
            ReceiverError: if there is some problem with the receiver.
        """
        try:
            await self.ready()
            return self.consume()
        except ReceiverStoppedError as exc:
            raise StopAsyncIteration() from exc

    @abstractmethod
    async def ready(self) -> bool:
        """Wait until the receiver is ready with a value or an error.

        Once a call to `ready()` has finished, the value should be read with
        a call to `consume()` (`receive()` or iterated over). The receiver will
        remain ready (this method will return immediately) until it is
        consumed.

        Returns:
            Whether the receiver is still active.
        """

    @abstractmethod
    def consume(self) -> _T:
        """Return the latest value once `ready()` is complete.

        `ready()` must be called before each call to `consume()`.

        Returns:
            The next value received.

        Raises:
            ReceiverStoppedError: if the receiver stopped producing messages.
            ReceiverError: if there is some problem with the receiver.
        """

    def __aiter__(self) -> Receiver[_T]:
        """Initialize the async iterator over received values.

        Returns:
            `self`, since no extra setup is needed for the iterator.
        """
        return self

    async def receive(self) -> _T:
        """Receive a message from the channel.

        Returns:
            The received message.

        Raises:
            ReceiverStoppedError: if there is some problem with the receiver.
            ReceiverError: if there is some problem with the receiver.
        """
        try:
            received = await self.__anext__()  # pylint: disable=unnecessary-dunder-call
        except StopAsyncIteration as exc:
            # If we already had a cause and it was the receiver was stopped,
            # then reuse that error, as StopAsyncIteration is just an artifact
            # introduced by __anext__.
            if (
                isinstance(exc.__cause__, ReceiverStoppedError)
                # pylint is not smart enough to figure out we checked above
                # this is a ReceiverStoppedError and thus it does have
                # a receiver member
                and exc.__cause__.receiver is self  # pylint: disable=no-member
            ):
                raise exc.__cause__
            raise ReceiverStoppedError(self) from exc
        return received

    def map(self, call: Callable[[_T], _U]) -> Receiver[_U]:
        """Return a receiver with `call` applied on incoming messages.

        Args:
            call: function to apply on incoming messages.

        Returns:
            A `Receiver` to read results of the given function from.
        """
        return _Map(self, call)


class _Map(Receiver[_U], Generic[_T, _U]):
    """Apply a transform function on a channel receiver.

    Has two generic types:

    - The input type: value type in the input receiver.
    - The output type: return type of the transform method.
    """

    def __init__(self, receiver: Receiver[_T], transform: Callable[[_T], _U]) -> None:
        """Create a `Transform` instance.

        Args:
            receiver: The input receiver.
            transform: The function to run on the input data.
        """
        self._receiver: Receiver[_T] = receiver
        """The input receiver."""

        self._transform: Callable[[_T], _U] = transform
        """The function to run on the input data."""

    async def ready(self) -> bool:
        """Wait until the receiver is ready with a value or an error.

        Once a call to `ready()` has finished, the value should be read with
        a call to `consume()` (`receive()` or iterated over). The receiver will
        remain ready (this method will return immediately) until it is
        consumed.

        Returns:
            Whether the receiver is still active.
        """
        return await self._receiver.ready()  # pylint: disable=protected-access

    # We need a noqa here because the docs have a Raises section but the code doesn't
    # explicitly raise anything.
    def consume(self) -> _U:  # noqa: DOC502
        """Return a transformed value once `ready()` is complete.

        Returns:
            The next value that was received.

        Raises:
            ChannelClosedError: if the underlying channel is closed.
        """
        return self._transform(
            self._receiver.consume()
        )  # pylint: disable=protected-access

    def __str__(self) -> str:
        """Return a string representation of the timer."""
        return f"{type(self).__name__}:{self._receiver}:{self._transform}"

    def __repr__(self) -> str:
        """Return a string representation of the timer."""
        return f"{type(self).__name__}({self._receiver!r}, {self._transform!r})"
