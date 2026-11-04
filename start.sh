#!/data/data/com.termux/files/usr/bin/bash
cd ~/My-bot-new
set -a
source .env
set +a
termux-wake-lock
python bot.py
