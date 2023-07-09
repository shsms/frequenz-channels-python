from typing import Generic, TypeVar


T = TypeVar("T")


class BcastChannel(Generic[T]):
    def __init__(self) -> None:
        ...

    def new_receiver(self) -> BcastReceiver[T]:
        ...

    def new_sender(self) -> BcastSender[T]:
        ...


class BcastSender(Generic[T]):
    def send(self, message: T) -> None:
        ...


class BcastReceiver(Generic[T]):
    async def receive(self) -> T:
        ...
