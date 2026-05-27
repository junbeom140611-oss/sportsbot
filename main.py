```python id="tcz1zn"
async def create_match(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.replace("/create ", "")

    if "|" not in text:
        await update.message.reply_text(
            "사용법:\n/create 팀1|팀2"
        )
        return

    split_text = text.split("|")

    home_team = split_text[0]
    away_team = split_text[1]

    match_id = f"{home_team}_vs_{away_team}"

    matches[match_id] = {
        "home_team": home_team,
        "away_team": away_team,
        "votes": {
            "home": 0,
            "draw": 0,
            "away": 0
        },
        "users": {}
    }

    match = matches[match_id]

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

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚽ {home_team} vs {away_team}\n\n👇 아래 버튼으로 참여하세요.",
        reply_markup=reply_markup
    )
```
