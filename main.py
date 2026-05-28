from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import asyncio
import os
import sys
import atexit

# ========================
# 🔥 중복 실행 방지
# ========================
def prevent_multiple_instances():
    lock_file = "bot.lock"

    if os.path.exists(lock_file):
        print("이미 실행 중인 봇이 있음 → 종료")
        sys.exit(0)

    with open(lock_file, "w") as f:
        f.write("running")

    def remove_lock():
        if os.path.exists(lock_file):
            os.remove(lock_file)

    atexit.register(remove_lock)


# ========================
# TOKEN
# ========================
TOKEN = os.getenv("BOT_TOKEN") or "여기에_토큰입력"

if not TOKEN:
    raise ValueError("BOT_TOKEN 없음")

ADMINS = [1003909241114]
matches = {}


# ========================
# 키보드
# ========================
def build_keyboard(match_id, match):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🏠 홈승 ({match['votes']['home']})", callback_data=f"{match_id}|home"),
            InlineKeyboardButton(f"🟩 무승부 ({match['votes']['draw']})", callback_data=f"{match_id}|draw"),
            InlineKeyboardButton(f"✈️ 원정승 ({match['votes']['away']})", callback_data=f"{match_id}|away"),
        ]
    ])


# ========================
# 경기 생성
# ========================
async def create_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("관리자만 사용 가능합니다.")
        return

    try:
        text = update.message.text.replace("/create ", "")
        split_text = text.split("|")

        if len(split_text) != 3:
            await update.message.reply_text("사용법:\n/create 홈팀 | 원정팀 | 마감시간(분)")
            return

        home_team = split_text[0].strip()
        away_team = split_text[1].strip()
        close_minutes = int(split_text[2].strip())

        match_id = f"{home_team}_vs_{away_team}"

        if match_id in matches:
            await update.message.reply_text("이미 등록된 경기입니다.")
            return

        matches[match_id] = {
            "home_team": home_team,
            "away_team": away_team,
            "votes": {"home": 0, "draw": 0, "away": 0},
            "users": {},
            "closed": False
        }

        match = matches[match_id]

        message = await update.message.reply_text(
            f"⚽ {home_team} vs {away_team}\n\n"
            f"🏠 홈승 : 0\n"
            f"🟩 무승부 : 0\n"
            f"✈️ 원정승 : 0\n\n"
            f"⏰ 남은시간 : {close_minutes}분",
            reply_markup=build_keyboard(match_id, match)
        )

        match["chat_id"] = message.chat.id
        match["message_id"] = message.message_id

        context.application.create_task(
            auto_close_match(context, match_id, close_minutes)
        )

    except ValueError:
        await update.message.reply_text("마감시간은 숫자로 입력해주세요.")

    except Exception as e:
        await update.message.reply_text(f"오류 발생:\n{e}")


# ========================
# 버튼 처리
# ========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data.split("|")

    if len(data) != 2:
        return

    match_id, choice = data

    if match_id not in matches:
        await query.answer("경기를 찾을 수 없습니다.")
        return

    match = matches[match_id]

    if match["closed"]:
        await query.answer("이미 마감된 경기입니다.", show_alert=True)
        return

    old_choice = match["users"].get(user_id)

    if old_choice == choice:
        await query.answer("이미 선택한 항목입니다.")
        return

    if old_choice:
        match["votes"][old_choice] -= 1

    match["users"][user_id] = choice
    match["votes"][choice] += 1

    await query.edit_message_text(
        f"⚽ {match['home_team']} vs {match['away_team']}\n\n"
        f"🏠 홈승 : {match['votes']['home']}\n"
        f"🟩 무승부 : {match['votes']['draw']}\n"
        f"✈️ 원정승 : {match['votes']['away']}\n\n"
        f"👥 참여 인원 : {len(match['users'])}명",
        reply_markup=build_keyboard(match_id, match)
    )


# ========================
# 자동 마감
# ========================
async def auto_close_match(context, match_id, minutes):
    try:
        await asyncio.sleep(minutes * 60)

        if match_id not in matches:
            return

        match = matches[match_id]
        match["closed"] = True

        await context.bot.edit_message_text(
            chat_id=match["chat_id"],
            message_id=match["message_id"],
            text=(
                f"⛔ 투표 마감\n\n"
                f"⚽ {match['home_team']} vs {match['away_team']}\n\n"
                f"🏠 홈승 : {match['votes']['home']}\n"
                f"🟩 무승부 : {match['votes']['draw']}\n"
                f"✈️ 원정승 : {match['votes']['away']}\n\n"
                f"👥 총 참여 인원 : {len(match['users'])}명"
            )
        )

    except Exception as e:
        print(f"[auto_close 오류] {e}")


# ========================
# 경기 목록
# ========================
async def matches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not matches:
        await update.message.reply_text("현재 진행중인 경기가 없습니다.")
        return

    text = "📋 진행중 경기 목록\n\n"

    for match in matches.values():
        status = "⛔ 마감" if match["closed"] else "🟢 진행중"
        text += f"⚽ {match['home_team']} vs {match['away_team']} - {status}\n"

    await update.message.reply_text(text)


# ========================
# 🚀 실행 (🔥 핵심 수정됨)
# ========================
def main():
    prevent_multiple_instances()

    print("봇 실행중...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("create", create_match))
    app.add_handler(CommandHandler("matches", matches_command))
    app.add_handler(CallbackQueryHandler(button))

    # 🔥 Python 3.14 대응 핵심
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("봇 종료")
        sys.exit(0)


if __name__ == "__main__":
    main()
