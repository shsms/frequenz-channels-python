# Frequenz channels Release Notes

## Summary

In addition to the new `LatestValueCache` and the ability to `filter` messages on `Receiver`s, this release introduces two "Experimental" features for providing interconnections between channels.

## New Features

- The `LatestValueCache` class, which used to be internal to the Frequenz SDK, is now available through the channels package.

- **Experimental**: `RelaySender`, which is a `Sender` that forwards the messages sent to it, to multiple senders.

- **Experimental**: `Pipe`, which provides a pipe between two channels, by connecting a `Receiver` to a `Sender`.

- `Receiver`s now have a `filter` method that applies a filter function on the messages on a receiver.
