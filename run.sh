#!/bin/bash
# Wrapper: sleeps a random 0–60 minutes, then runs the bot.
# A Chrome window will briefly appear and close.
#
# Crontab entry (runs at 8 PM, actual execution 8:00–9:00 PM):
#   0 20 * * * /Users/gkarabinos/Documents/fun/strava/run.sh

DELAY=$((RANDOM % 3600))
echo "$(date) — sleeping ${DELAY}s before running bot"
sleep $DELAY

cd "$(dirname "$0")"
/usr/bin/python3 bot.py
