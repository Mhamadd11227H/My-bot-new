#!/data/data/com.termux/files/usr/bin/bash
cd ~/My-bot-new
set -a
source .env
set +a
termux-wake-lock

# ئەگەر بوت بۆ هەر هۆیەک وەستا (هەڵە، ئینتەرنێت...)، دوای ٥ چرکە خۆکار دەستپێ دەکاتەوە
while true; do
    python bot.py
    echo "⚠️ بوت وەستا. دوای ٥ چرکە دووبارە دەستپێ دەکات..."
    sleep 5
done
