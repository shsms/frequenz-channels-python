# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Baseclasses for Channel Sender and Receiver."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Error(RuntimeError):
    """Base error.

    All exceptions generated by this library inherit from this exception.
    """

    def __init__(self, message: Any):
        """Create a ChannelError instance.

        Args:
            message: An error message.
        """
        super().__init__(message)


class ChannelError(Error):
    """An error produced in a channel.

    All exceptions generated by channels inherit from this exception.
    """

    def __init__(self, message: Any, channel: Any = None):
        """Create a ChannelError instance.

        Args:
            message: An error message.
            channel: A reference to the channel that encountered the error.
        """
        super().__init__(message)
        self.channel: Any = channel


class ChannelClosedError(ChannelError):
    """Error raised when trying to operate on a closed channel."""

    def __init__(self, channel: Any = None):
        """Create a `ChannelClosedError` instance.

        Args:
            channel: A reference to the channel that was closed.
        """
        super().__init__(f"Channel {channel} was closed", channel)


class SenderError(Error, Generic[T]):
    """An error produced in a [Sender][frequenz.channels.Sender].

    All exceptions generated by senders inherit from this exception.
    """

    def __init__(self, message: Any, sender: Sender[T]):
        """Create an instance.

        Args:
            message: An error message.
            sender: The [Sender][frequenz.channels.Sender] where the error
                happened.
        """
        super().__init__(message)
        self.sender: Sender[T] = sender


class Sender(ABC, Generic[T]):
    """A channel Sender."""

    @abstractmethod
    async def send(self, msg: T) -> None:
        """Send a message to the channel.

        Args:
            msg: The message to be sent.

        Raises:
            SenderError: if there was an error sending the message.
        """


class Receiver(ABC, Generic[T]):
    """A channel Receiver."""

    async def __anext__(self) -> T:
        """Await the next value in the async iteration over received values.

        Returns:
            The next value received.

        Raises:
            StopAsyncIteration: if the underlying channel is closed.
        """
        try:
            await self.ready()
            return self.consume()
        except ChannelClosedError as exc:
            raise StopAsyncIteration() from exc

    @abstractmethod
    async def ready(self) -> None:
        """Wait until the receiver is ready with a value.

        Once a call to `ready()` has finished, the value should be read with a call to
        `consume()`.

        Raises:
            ChannelClosedError: if the underlying channel is closed.
        """

    @abstractmethod
    def consume(self) -> T:
        """Return the latest value once `ready()` is complete.

        `ready()` must be called before each call to `consume()`.

        Returns:
            The next value received.

        Raises:
            ChannelClosedError: if the underlying channel is closed.
        """

    def __aiter__(self) -> Receiver[T]:
        """Initialize the async iterator over received values.

        Returns:
            `self`, since no extra setup is needed for the iterator.
        """
        return self

    async def receive(self) -> T:
        """Receive a message from the channel.

        Raises:
            ChannelClosedError: if the underlying channel is closed.

        Returns:
            The received message.
        """
        try:
            received = await self.__anext__()  # pylint: disable=unnecessary-dunder-call
        except StopAsyncIteration as exc:
            raise ChannelClosedError() from exc
        return received

    def map(self, call: Callable[[T], U]) -> Receiver[U]:
        """Return a receiver with `call` applied on incoming messages.

        Args:
            call: function to apply on incoming messages.

        Returns:
            A `Receiver` to read results of the given function from.
        """
        return _Map(self, call)

    def into_peekable(self) -> Peekable[T]:
        """Convert the `Receiver` implementation into a `Peekable`.

        Once this function has been called, the receiver will no longer be
        usable, and calling `receive` on the receiver will raise an exception.

        Raises:
            NotImplementedError: when a `Receiver` implementation doesn't have
                a custom `into_peekable` implementation.
        """
        raise NotImplementedError("This receiver does not implement `into_peekable`")


class Peekable(ABC, Generic[T]):
    """A channel peekable.

    A Peekable provides a [peek()][frequenz.channels.Peekable] method that
    allows the user to get a peek at the latest value in the channel, without
    consuming anything.
    """

    @abstractmethod
    def peek(self) -> Optional[T]:
        """Return the latest value that was sent to the channel.

        Returns:
            The latest value received by the channel, and `None`, if nothing
                has been sent to the channel yet.
        """


class _Map(Receiver[U], Generic[T, U]):
    """Apply a transform function on a channel receiver.

    Has two generic types:

    - The input type: value type in the input receiver.
    - The output type: return type of the transform method.
    """

    def __init__(self, recv: Receiver[T], transform: Callable[[T], U]) -> None:
        """Create a `Transform` instance.

        Args:
            recv: The input receiver.
            transform: The function to run on the input
                data.
        """
        self._recv = recv
        self._transform = transform

    async def ready(self) -> None:
        """Wait until the receiver is ready with a value."""
        await self._recv.ready()  # pylint: disable=protected-access

    def consume(self) -> U:
        """Return a transformed value once `ready()` is complete.

        Returns:
            The next value that was received.
        """
        return self._transform(self._recv.consume())  # pylint: disable=protected-access
