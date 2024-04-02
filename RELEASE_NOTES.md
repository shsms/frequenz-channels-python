# Frequenz channels Release Notes

## Summary

This is the first stable release of the Frequenz channels library.

If you are **upgrading from the previous 1.0.0 pre-releases**, please look into the release notes for those versions to see the changes and upgrade instructions:

* [1.0.0-rc.1](https://github.com/frequenz-floss/frequenz-channels-python/releases/tag/v1.0.0-rc.1)
* [1.0.0-beta.2](https://github.com/frequenz-floss/frequenz-channels-python/releases/tag/v1.0.0-beta.2)
* [1.0.0-beta.1](https://github.com/frequenz-floss/frequenz-channels-python/releases/tag/v1.0.0-beta.1)

There were no changes between 1.0.0-rc.1 and this 1.0.0 final release.

If you are **upgrading from v0.16.x**, please keep reading these release notes.

## Upgrading

* The following symbols were moved to the top-level `frequenz.channels` package:

  - `Selected`
  - `SelectError`
  - `UnhandledSelectedError`
  - `select`
  - `selected_from`

* `util`

  The entire `util` package was removed and its symbols were either moved to the top-level package or to their own public modules (as noted above).

* All exceptions that took `Any` as the `message` argument now take `str` instead.

  If you were passing a non-`str` value to an exception, you should convert it using `str(value)` before passing it to the exception.

* `Anycast`

  - `__init__`: The `maxsize` argument was renamed to `limit` and made keyword-only and a new keyword-only `name` (required) argument was added.

    You should instantiate using `Anycast(name=..., limit=...)` (or `Anycast(name=...)` if the default `limit` is enough) instead of `Anycast(...)` or `Anycast(maxsize=...)`.

  - The following properties were changed:

    - `limit`: is now read-only.
    - `closed`: is now named `is_closed` and read-only.

  - `new_sender` and `new_receiver`: They now return a base `Sender` and `Receiver` class (respectively) instead of a channel-specific `Sender` or `Receiver` subclass.

    This means users now don't have access to the internals to the channel-specific `Sender` and `Receiver` subclasses.

* `Broadcast`

  - `__init__`: The `name` and `resend_latest` arguments were made keyword-only.

    You should instantiate using `Broadcast(name=name, resend_latest=resend_latest)` (or `Broadcast()` if the defaults are enough) instead of `Broadcast(name)` or `Broadcast(name, resend_latest)`.

  - The following properties were changed:

    - `limit`: is now read-only.
    - `closed`: is now named `is_closed` and read-only.

  - `new_receiver`: The `maxsize` argument was renamed to `limit` and made keyword-only; the `name` argument was also made keyword-only. If a `name` is not specified, it will be generated from the `id()` of the instance instead of a random UUID.

    You should use `.new_receiver(name=name, limit=limit)` (or `.new_receiver()` if the defaults are enough) instead of `.new_receiver(name)` or `.new_receiver(name, maxsize)`.

  - `new_sender` and `new_receiver` now return a base `Sender` and `Receiver` class (respectively) instead of a channel-specific `Sender` or `Receiver` subclass.

    This means users now don't have access to the internals to the channel-specific `Sender` and `Receiver` subclasses.

* `Event`

  - Moved from `frequenz.channels.util` to `frequenz.channels.event`.

  - `__init__`: The `name` argument was made keyword-only. The default was changed to a more readable version of `id(self)`.

    You should instantiate using `Event(name=...)` instead of `Event(...)`.

* `FileWatcher`

  - Moved from `frequenz.channels.util` to `frequenz.channels.file_watcher`.

  - Support classes are no longer nested inside `FileWatcher`. They are now top-level classes within the new `frequenz.channels.file_watcher` module (e.g., `frequenz.channels.util.FileWatcher.EventType` -> `frequenz.channels.file_watcher.EventType`, `frequenz.channels.util.FileWatcher.Event` -> `frequenz.channels.file_watcher.Event`).

* `Receiver`

  - The `map()` function now takes a positional-only argument, if you were using `receiver.map(call=fun)` you should replace it with `receiver.map(func)`.

* `SelectError` now inherits from `channels.Error` instead of `BaseException`, so you should be able to catch it with `except Exception:` or `except channels.Error:`.

* `Selected`

  - The `value` property was renamed to `message`.
  - `was_stopped` is now a property, you need to replace `selected.was_stopped()` with `selected.was_stopped`.

* `Sender`

  - The `send` method now takes a positional-only argument, if you were using `sender.send(msg=message)` you should replace it with `sender.send(message)`.

* `Timer` and support classes

  - Moved from `frequenz.channels.util` to `frequenz.channels.timer`.

### Removals

* `Anycast`

  - The following public properties were removed (made private): `deque`, `send_cv`, `recv_cv`.

* `Bidirectional`

  This channel was removed as it is not recommended practice and was a niche use case. If you need to use it, you can set up two channels or copy the `Bidirectional` class from the previous version to your project.

* `Broadcast`

  - The following public properties were removed (made private): `recv_cv`, `receivers`.
  - `new_peekable()` was removed because `Peekable` was removed.

* `Merge`

  Replaced by the new `merge()` function. When replacing `Merge` with `merge()` please keep in mind that this new function will raise a `ValueError` if no receivers are passed to it.

  Please note that the old `Merge` class is still also available but it was renamed to `Merger` to avoid confusion with the new `merge()` function, but it is only present for typing reasons and should not be used directly.

* `MergeNamed`

  This class was redundant, use either the new `merge()` function or `select()` instead.

* `Peekable`

  This class was removed because it was merely a shortcut to a receiver that caches the last message received. It did not fit the channel abstraction well and was infrequently used.

  You can replace it with a task that receives and retains the last message.

* `Receiver.into_peekable()` was removed because `Peekable` was removed.

* `ReceiverInvalidatedError` was removed because it was only used when converting to a `Peekable` and `Peekable` was removed.

* `SelectErrorGroup` was removed, a Python built-in `BaseExceptionGroup` is raised instead in case of unexpected errors while finalizing a `select()` loop, which will be automatically converted to a simple `ExceptionGroup` when no exception in the groups is a `BaseException`.

- `Timer`:

  - `periodic()` and `timeout()`: The names proved to be too confusing, please use `Timer()` and pass a missing ticks policy explicitly instead. In general you can update your code by doing:

    * `Timer.periodic(interval)` / `Timer.periodic(interval, skip_missed_ticks=True)` -> `Timer(interval, TriggerAllMissed())`
    * `Timer.periodic(interval, skip_missed_ticks=False)` -> `Timer(interval, SkipMissedAndResync())`
    * `Timer.timeout(interval)` -> `Timer(interval, SkipMissedAndDrift())`

## New Features

* A new `Broadcast.resend_latest` read-write property was added to get/set whether the latest message should be resent to new receivers.

* `Timer()` and `Timer.reset()` now take an optional `start_delay` option to make the timer start after some delay.

  This can be useful, for example, if the timer needs to be *aligned* to a particular time. The alternative to this would be to `sleep()` for the time needed to align the timer, but if the `sleep()` call gets delayed because the event loop is busy, then a re-alignment is needed and this could go on for a while. The only way to guarantee a certain alignment (with a reasonable precision) is to delay the timer start.

## Improvements

* The arm64 architecture is now officially supported.

* A new User's Guide was added to the documentation and the documentation was greately improved in general.

* A new `merge()` function was added to replace `Merge`.

* A warning will be logged by `Anycast` channels if senders are blocked because the channel buffer is full.

* `Receiver`, `merge`/`Merger`, `Error` and its derived classes now use a covariant generic type, which allows the generic type to be broader than the actual type.

* `Sender` now uses a contravariant generic type, which allows the generic type to be narrower than the required type.

* `ChannelError` is now generic, so when accessing the `channel` attribute, the type of the channel is preserved.

* Most classes have now a better implementation of `__str__` and `__repr__`.

## Bug Fixes

* `Timer`: Fix bug that was causing calls to `reset()` to not reset the timer, if the timer was already being awaited.
