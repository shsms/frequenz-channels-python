# Frequenz channels Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

## Bug Fixes

- `FileWatcher`: Fixed `ready()` method to return False when an error occurs. Before this fix, `select()` (and other code using `ready()`) never detected the `FileWatcher` was stopped and the `select()` loop was continuously waking up to inform the receiver was ready.
