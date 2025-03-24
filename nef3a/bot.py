from phonetic_utils import arabic_to_phonetic, english_to_phonetic

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import RetryAfter
import sqlite3
from datetime import datetime
import asyncio
import re
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ACCESS_CODE = os.getenv("ACCESS_CODE")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# --- DB Path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, '..', 'data', 'converted.sqlite')
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
TABLE = "CARMDI"

authorized_users = set()

# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("🔐 Please enter the access code to use the bot.")
        return
    await update.message.reply_text("👋 Welcome! Send a plate (with or without letter), phone, name, or DOB to search.")

# --- Authorization ---
async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id in authorized_users:
        await handle_search(update, context)
        return

    if text == ACCESS_CODE:
        authorized_users.add(user_id)
        await update.message.reply_text("✅ Access granted! Now send a plate, name, phone, or DOB.")
    else:
        await update.message.reply_text("❌ Invalid passcode.")

# --- Core Search Logic ---
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("🔐 Please enter the access code first.")
        return

    text = update.message.text.strip()
    parts = text.split()
    filtered_rows = []

    try:
        query = None
        params = None

        if len(parts) == 2 and (parts[0].isdigit() or parts[1].isdigit()):
            number = parts[0] if parts[0].isdigit() else parts[1]
            letter = parts[1] if parts[0].isdigit() else parts[0]
            query = f"SELECT * FROM {TABLE} WHERE ActualNB = ? AND CodeDesc = ?"
            params = (number, letter.upper())

        elif len(parts) == 1:
            keyword = parts[0]
            cleaned = ''.join(filter(str.isdigit, keyword))

            if len(cleaned) >= 7:
                query = f"SELECT * FROM {TABLE} WHERE REPLACE(REPLACE(REPLACE(TelProp, '/', ''), '-', ''), ' ', '') LIKE ?"
                params = (f"%{cleaned}%",)

            elif "/" in keyword:
                query = f"SELECT * FROM {TABLE} WHERE AgeProp = ?"
                params = (keyword,)

            elif keyword.isdigit():
                query = f"SELECT * FROM {TABLE} WHERE ActualNB = ?"
                params = (keyword,)

            else:
                query = f"SELECT * FROM {TABLE} WHERE MarqueDesc LIKE ? OR TypeDesc LIKE ?"
                params = (f"%{keyword}%", f"%{keyword}%")

                input_phonetic = arabic_to_phonetic(keyword)
                cursor.execute(f"SELECT * FROM {TABLE} WHERE Prenom IS NOT NULL OR Nom IS NOT NULL")
                for row in cursor.fetchmany(100):
                    data = dict(zip([col[0] for col in cursor.description], row))
                    if input_phonetic in arabic_to_phonetic(data.get("Prenom") or "") or input_phonetic in arabic_to_phonetic(data.get("Nom") or ""):
                        filtered_rows.append(data)

        elif len(parts) >= 2:
            first, last = parts[0], parts[1]
            input_soundex = arabic_to_phonetic(first) + arabic_to_phonetic(last)
            cursor.execute(f"SELECT * FROM {TABLE} WHERE Prenom IS NOT NULL AND Nom IS NOT NULL")
            for row in cursor.fetchmany(100):
                data = dict(zip([col[0] for col in cursor.description], row))
                soundex = arabic_to_phonetic(data.get("Prenom") or "") + arabic_to_phonetic(data.get("Nom") or "")
                if soundex == input_soundex:
                    filtered_rows.append(data)

        if query and params is not None:
            cursor.execute(query, params)
            col_names = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            filtered_rows.extend([dict(zip(col_names, row)) for row in rows])

        if not filtered_rows:
            await update.message.reply_text("❌ No results found.")
            return

        context.user_data['results'] = filtered_rows
        context.user_data['start'] = 0
        await send_limited_results(update, context, 0)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# --- Send Paginated Results ---
async def send_limited_results(update: Update, context: ContextTypes.DEFAULT_TYPE, start=0):
    results = context.user_data.get('results', [])
    count = 3
    next_chunk = results[start:start+count]

    for data in next_chunk:
        msg_lines = [
            f"🚘 Plate: {data.get('ActualNB', '')} {data.get('CodeDesc', '')}",
            f"📅 Year: {data.get('PRODDATE', '')}",
            f"🧑‍💼 Name: {data.get('Prenom', '')} {data.get('Nom', '')}",
            f"📞 Phone: {data.get('TelProp', '')}",
            f"🚗 Car: {data.get('MarqueDesc', '')} {data.get('TypeDesc', '')}",
            f"🎨 Color: {data.get('CouleurDesc', '')}",
            f"📍 Address: {data.get('Addresse', '')}"
        ]
        if data.get('AgeProp'): msg_lines.append(f"🎂 DOB: {data.get('AgeProp')}")
        if data.get('BirthPlace'): msg_lines.append(f"🌍 Birthplace: {data.get('BirthPlace')}")
        await update.message.reply_text("\n".join(msg_lines))

    if len(results) > start + count:
        context.user_data['start'] = start + count
        await update.message.reply_text("🔄 Send 'more' to load more results.")
    else:
        context.user_data.pop('results', None)
        context.user_data.pop('start', None)

# --- "More" Pagination ---
async def handle_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'results' in context.user_data:
        start = context.user_data.get('start', 0)
        await send_limited_results(update, context, start)
    else:
        await update.message.reply_text("❗ No more results to show.")

# --- Admin Panel ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not authorized.")
        return

    try:
        with open("search_log.txt", "r", encoding="utf-8") as f:
            logs = f.readlines()[-10:]
    except FileNotFoundError:
        logs = ["(No logs yet)"]

    log_text = "🧾 Last 10 Searches:\n" + "".join(logs)
    users_text = "\n".join([f"• {uid}" for uid in authorized_users]) or "(None)"
    await update.message.reply_text(log_text + "\n\n👥 Users:\n" + users_text)

# --- Run Bot ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^more$"), handle_more))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, authorize))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
app.run_polling()
