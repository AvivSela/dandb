#!/bin/sh
# Repair /data ownership when a host volume is mounted over it (arrives as root-owned).
# Runs as root, then drops to appuser for the actual process.
chown -R appuser:appgroup /data
exec gosu appuser "$@"
