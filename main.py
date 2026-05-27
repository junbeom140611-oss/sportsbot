from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

import os

TOKEN = os.getenv("BOT_TOKEN")

votes = {
    "home": 0,
    "draw": 0,
    "away": 0
}

users = {}

async def startvote(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                f"🏠 홈승 ({votes['home']})",
                callback_data='home'
            ),
            InlineKeyboardButton(
                f"🟩 무승부 ({votes['draw']})",
                callback_data='draw'
            ),
            InlineKeyboardButton(
                f"✈️ 원정승 ({votes['away']})",
                callback_data='away'
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚽ 경기 투표\n\n👇 아래 버튼으로 참여하세요.",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    choice = query.data

    if user_id in users:
        await query.answer("이미 참여하셨습니다.", show_alert=True)
        return

    users[user_id] = choice

    votes[choice] += 1

    keyboard = [
        [
            InlineKeyboardButton(
                f"🏠 홈승 ({votes['home']})",
                callback_data='home'
            ),
            InlineKeyboardButton(
                f"🟩 무승부 ({votes['draw']})",
                callback_data='draw'
            ),
            InlineKeyboardButton(
                f"✈️ 원정승 ({votes['away']})",
                callback_data='away'
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_reply_markup(
        reply_markup=reply_markup
    )

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("startvote", startvote))
app.add_handler(CallbackQueryHandler(button))

print("봇 실행중...")

app.run_polling()
