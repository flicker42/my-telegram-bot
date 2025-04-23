import random
import os
import json
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils import executor
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Главное меню
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("📱 Мои соцсети"))
main_keyboard.add(KeyboardButton("🤣 Мем дня"))
main_keyboard.add(KeyboardButton("🎮 Крестики-нолики"))
main_keyboard.add(KeyboardButton("🏆 Лидеры"))

SOCIALS = """
🔥 Вот мои соцсети:
- Telegram: https://t.me/w52andhaunted
- DM - @flickerovich
"""

# Игры и счёт
user_games = {}
SCORE_FILE = "score.json"

# Загрузка счёта
if os.path.exists(SCORE_FILE):
    with open(SCORE_FILE, "r") as f:
        user_scores = json.load(f)
else:
    user_scores = {}

def save_scores():
    with open(SCORE_FILE, "w") as f:
        json.dump(user_scores, f)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Выбирай кнопку 👇", reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text == "📱 Мои соцсети")
async def socials(message: types.Message):
    await message.answer(SOCIALS)

@dp.message_handler(lambda message: message.text == "🤣 Мем дня")
async def meme(message: types.Message):
    now = datetime.datetime.now()
    folder = "memes_night" if 22 <= now.hour or now.hour < 6 else "memes"
    if not os.path.exists(folder):
        await message.answer("Мемов пока нет 😢")
        return
    memes = os.listdir(folder)
    if memes:
        file_name = random.choice(memes)
        with open(f"{folder}/{file_name}", "rb") as photo:
            await message.answer_photo(photo)
    else:
        await message.answer("Мемов пока нет 😢")

@dp.message_handler(lambda message: message.text == "🎮 Крестики-нолики")
async def start_game(message: types.Message):
    user_id = message.from_user.id
    user_games[user_id] = [" " for _ in range(9)]
    await message.answer("Ты играешь ❌. Удачи!", reply_markup=render_board(user_games[user_id]))

@dp.message_handler(lambda message: message.text == "🏆 Лидеры")
async def show_leaders(message: types.Message):
    if not user_scores:
        await message.answer("Пока что никто не выигрывал 🙃")
        return
    top = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    text = "🏆 Топ 5 игроков по победам:\n"
    for i, (user, score) in enumerate(top, 1):
        text += f"{i}. {user} — {score} побед\n"
    await message.answer(text)

def render_board(board, end_game=False):
    keyboard = InlineKeyboardMarkup(row_width=3)
    for i in range(9):
        text = board[i] if board[i] != " " else "⬜"
        keyboard.insert(InlineKeyboardButton(text=text, callback_data=f"move:{i}"))
    if end_game:
        keyboard.add(InlineKeyboardButton("🔁 Играть заново", callback_data="restart"))
    return keyboard

@dp.callback_query_handler(lambda call: call.data == "restart")
async def restart_game(call: CallbackQuery):
    user_id = call.from_user.id
    user_games[user_id] = [" " for _ in range(9)]
    await call.message.edit_text("Ты играешь ❌. Удачи!", reply_markup=render_board(user_games[user_id]))

@dp.callback_query_handler(lambda call: call.data.startswith("move:"))
async def handle_move(call: CallbackQuery):
    user_id = call.from_user.id
    index = int(call.data.split(":")[1])
    board = user_games.get(user_id, [" " for _ in range(9)])

    if board[index] != " ":
        await call.answer("Уже занято!", show_alert=True)
        return

    board[index] = "❌"
    if check_win(board, "❌"):
        user_scores[str(user_id)] = user_scores.get(str(user_id), 0) + 1
        save_scores()
        await call.message.edit_text("Ты победил! 🎉", reply_markup=render_board(board, end_game=True))
        try:
            with open("prize/win.jpg", "rb") as photo:
                await bot.send_photo(user_id, photo, caption=f"Счёт побед: {user_scores[str(user_id)]}")
        except:
            await bot.send_message(user_id, "Приз не найден :(")
        return

    if " " not in board:
        await call.message.edit_text("Ничья! Попробуй ещё раз.", reply_markup=render_board(board, end_game=True))
        return

    bot_index = get_minimax_move(board, "⭕")
    board[bot_index] = "⭕"
    if check_win(board, "⭕"):
        await call.message.edit_text("Бот победил! Попробуй снова.", reply_markup=render_board(board, end_game=True))
        return

    await call.message.edit_reply_markup(reply_markup=render_board(board))

def check_win(board, symbol):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    return any(all(board[i] == symbol for i in combo) for combo in wins)

def get_minimax_move(board, bot_symbol):
    human = "❌"
    bot = bot_symbol

    def minimax(board, depth, is_maximizing):
        if check_win(board, bot): return 1
        if check_win(board, human): return -1
        if " " not in board: return 0

        if is_maximizing:
            best_score = -float("inf")
            for i in range(9):
                if board[i] == " ":
                    board[i] = bot
                    score = minimax(board, depth + 1, False)
                    board[i] = " "
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float("inf")
            for i in range(9):
                if board[i] == " ":
                    board[i] = human
                    score = minimax(board, depth + 1, True)
                    board[i] = " "
                    best_score = min(score, best_score)
            return best_score

    best_move = None
    best_score = -float("inf")
    for i in range(9):
        if board[i] == " ":
            board[i] = bot
            score = minimax(board, 0, False)
            board[i] = " "
            if score > best_score:
                best_score = score
                best_move = i
    return best_move

if __name__ == "__main__":
    executor.start_polling(dp)
