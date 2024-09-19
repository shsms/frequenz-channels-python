# Frequenz channels Release Notes

## New Features

- `Timer.reset()` now supports setting the interval and will restart the timer with the new interval.

## Bug Fixes

- `FileWatcher`: Fixed `ready()` method to return False when an error occurs. Before this fix, `select()` (and other code using `ready()`) never detected the `FileWatcher` was stopped and the `select()` loop was continuously waking up to inform the receiver was ready.

- `Timer.stop()` and `Timer.reset()` now immediately stop the timer if it is running. Before this fix, the timer would continue to run until the next interval.
