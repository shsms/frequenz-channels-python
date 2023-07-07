from typing import Generic, TypeVar

from frequenz.channels import Receiver, Sender


T = TypeVar("T")


class BcastChannel(Generic[T]):
    def __init__(self) -> None:
        ...

    def new_receiver(self) -> Receiver[T]:
        ...

    def new_sender(self) -> Sender[T]:
        ...
