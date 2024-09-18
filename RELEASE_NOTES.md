# Frequenz channels Release Notes

## Upgrading

- `FileWatcher`: The file polling mechanism is now forced by default. This provides reliable and consistent file monitoring on network file systems (e.g., CIFS). However, it may have a performance impact on local file systems or when monitoring a large number of files.
  - To disable file polling, set the `force_polling` parameter to `False`.
  - The `polling_interval` parameter defines the interval for polling changes. This is relevant only when polling is enabled and defaults to 1 second.

## New Features

- `Timer.reset()` now supports setting the interval and will restart the timer with the new interval.

## Bug Fixes

- `FileWatcher`:
  - Fixed `ready()` method to return False when an error occurs. Before this fix, `select()` (and other code using `ready()`) never detected the `FileWatcher` was stopped and the `select()` loop was continuously waking up to inform the receiver was ready.
  - Reports file events correctly on network file systems like CIFS.

- `Timer.stop()` and `Timer.reset()` now immediately stop the timer if it is running. Before this fix, the timer would continue to run until the next interval.
