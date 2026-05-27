from telegram import (
InlineKeyboardButton,
InlineKeyboardMarkup,
Update
)

from telegram.ext import (
Application,
CommandHandler,
CallbackQueryHandler,
ContextTypes
)

import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

# 관리자 텔레그램 ID

ADMINS = [1003909241114]

# 경기 저장

matches = {}

# 버튼 생성

def build_keyboard(match_id, match):

keyboard = [
    [
        InlineKeyboardButton(
            f"🏠 홈승 ({match['votes']['home']})",
            callback_data=f"{match_id}|home"
        ),

        InlineKeyboardButton(
            f"🟩 무승부 ({match['votes']['draw']})",
            callback_data=f"{match_id}|draw"
        ),

        InlineKeyboardButton(
            f"✈️ 원정승 ({match['votes']['away']})",
            callback_data=f"{match_id}|away"
        ),
    ]
]

return InlineKeyboardMarkup(keyboard)

# 경기 생성

async def create_match(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):

user_id = update.effective_user.id

# 관리자 체크
if user_id not in ADMINS:

    await update.message.reply_text(
        "관리자만 사용 가능합니다."
    )

    return

try:

    text = update.message.text.replace(
        "/create ",
        ""
    )

    split_text = text.split("|")

    home_team = split_text[0].strip()
    away_team = split_text[1].strip()

    close_minutes = int(split_text[2])

    match_id = (
        f"{home_team}_vs_{away_team}"
    )

    matches[match_id] = {

        "home_team": home_team,
        "away_team": away_team,

        "votes": {
            "home": 0,
            "draw": 0,
            "away": 0
        },

        "users": {},

        "closed": False
    }

    match = matches[match_id]

    text_message = f"""

⚽ {home_team} vs {away_team}

🏠 홈승 : 0
🟩 무승부 : 0
✈️ 원정승 : 0

⏰ 남은시간 : {close_minutes}분
"""

    message = await update.message.reply_text(
        text_message,
        reply_markup=build_keyboard(
            match_id,
            match
        )
    )

    match["chat_id"] = message.chat_id
    match["message_id"] = message.message_id

    asyncio.create_task(

        auto_close_match(
            context,
            match_id,
            close_minutes
        )

    )

except Exception as e:

    await update.message.reply_text(
        f"오류 발생:\n{e}"
    )

# 투표 처리

async def button(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):

query = update.callback_query

await query.answer()

user_id = query.from_user.id

data = query.data.split("|")

match_id = data[0]
choice = data[1]

if match_id not in matches:

    await query.answer(
        "경기를 찾을 수 없습니다."
    )

    return

match = matches[match_id]

# 마감 체크
if match["closed"]:

    await query.answer(
        "이미 마감된 경기입니다.",
        show_alert=True
    )

    return

# 기존 투표
old_choice = match["users"].get(user_id)

# 기존 투표 제거
if old_choice:

    match["votes"][old_choice] -= 1

# 새 투표 저장
match["users"][user_id] = choice

match["votes"][choice] += 1

new_text = f"""

⚽ {match['home_team']} vs {match['away_team']}

🏠 홈승 : {match['votes']['home']}
🟩 무승부 : {match['votes']['draw']}
✈️ 원정승 : {match['votes']['away']}
"""

await query.edit_message_text(
    text=new_text,
    reply_markup=build_keyboard(
        match_id,
        match
    )
)

# 자동 마감

async def auto_close_match(
context,
match_id,
minutes
):

await asyncio.sleep(minutes * 60)

if match_id not in matches:
    return

match = matches[match_id]

match["closed"] = True

close_text = f"""

⛔ 투표 마감

⚽ {match['home_team']} vs {match['away_team']}

🏠 홈승 : {match['votes']['home']}
🟩 무승부 : {match['votes']['draw']}
✈️ 원정승 : {match['votes']['away']}
"""

await context.bot.edit_message_text(

    chat_id=match["chat_id"],
    message_id=match["message_id"],
    text=close_text

)

# 경기 목록

async def matches_command(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):

if not matches:

    await update.message.reply_text(
        "현재 진행중인 경기가 없습니다."
    )

    return

text = "📋 진행중 경기 목록\n\n"

for match_id, match in matches.items():

    status = (
        "⛔ 마감"
        if match["closed"]
        else "🟢 진행중"
    )

    text += (
        f"⚽ {match['home_team']} "
        f"vs "
        f"{match['away_team']} "
        f"- {status}\n"
    )

await update.message.reply_text(text)

# 앱 실행

app = (
Application
.builder()
.token(TOKEN)
.build()
)

app.add_handler(
CommandHandler(
"create",
create_match
)
)

app.add_handler(
CommandHandler(
"matches",
matches_command
)
)

app.add_handler(
CallbackQueryHandler(button)
)

print("봇 실행중...")

app.run_polling()
