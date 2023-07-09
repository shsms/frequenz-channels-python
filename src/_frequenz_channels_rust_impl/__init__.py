from typing import Generic, TypeVar

from frequenz.channels._base_classes import Receiver, Sender

from ._channels_impl import BcastChannel, BcastReceiver, BcastSender

T = TypeVar("T")


class FastBroadcast(Generic[T]):
    def __init__(self, name: str) -> None:
        self._channel: BcastChannel[T] = BcastChannel()
        self._name: str = name

    def new_receiver(self) -> Receiver[T]:
        return FastReceiver(self._channel.new_receiver())

    def new_sender(self) -> Sender[T]:
        return FastSender(self._channel.new_sender())

class FastSender(Sender[T]):
    def __init__(self, sender: "BcastSender[T]") -> None:
        self._sender: BcastSender[T] = sender

    async def send(self, message: T) -> None:
        self._sender.send(message)

class FastReceiver(Receiver[T]):
    def __init__(self, receiver: "BcastReceiver[T]") -> None:
        self._receiver: BcastReceiver[T] = receiver
        self._value = None

    async def ready(self) -> None:
        self._value = await self._receiver.receive()

    def consume(self) -> T:
        assert self._value is not None
        return self._value
