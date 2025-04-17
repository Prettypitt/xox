#!/usr/bin/env python3
import sys
import os
import logging
import random

# ---- Attempt to import PTB v20+; tests will still load if missing ----
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        CallbackQueryHandler,
        ContextTypes,
    )
    TELEGRAM_AVAILABLE = True
except ModuleNotFoundError:
    TELEGRAM_AVAILABLE = False

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory games store: user_id -> game state
# game state stores board, user_mark, bot_mark, next_turn
GAMES = {}

WIN_COMBINATIONS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]

def check_win(board, mark) -> bool:
    """Return True if `mark` has a winning line on `board`."""
    return any(all(board[i] == mark for i in combo) for combo in WIN_COMBINATIONS)

if TELEGRAM_AVAILABLE:
    # ---- Bot command handlers (async for PTB v20+) ----

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Merhaba! Bir XoX oyunu oynamak için /play komutunu kullanın."
        )

    async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        board = [" "] * 9
        # Rastgele X veya O
        user_mark, bot_mark = random.choice([('X', 'O'), ('O', 'X')])
        # X her zaman ilk hamleyi yapar
        next_turn = 'user' if user_mark == 'X' else 'bot'
        GAMES[user_id] = {
            'board': board,
            'user_mark': user_mark,
            'bot_mark': bot_mark,
            'next_turn': next_turn
        }

        if next_turn == 'bot':
            avail = [i for i, v in enumerate(board) if v == " "]
            bot_idx = random.choice(avail)
            board[bot_idx] = bot_mark
            GAMES[user_id]['next_turn'] = 'user'
            text = f"Sen {user_mark}'sın! Bot başladı ve hamlesini yaptı. Sıra sende."
        else:
            text = f"Sen {user_mark}'sın! İlk hamleni yap."
        await _send_board(update, context, board, text)

    async def _send_board(update, context, board, text: str) -> None:
        keyboard = []
        for i in range(0, 9, 3):
            row = [
                InlineKeyboardButton(
                    board[j] if board[j] != " " else str(j + 1),
                    callback_data=str(j),
                )
                for j in range(i, i + 3)
            ]
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        game = GAMES.get(user_id)
        if not game:
            return await query.edit_message_text("Önce /play ile oyunu başlatın.")

        board = game['board']
        user_mark = game['user_mark']
        bot_mark = game['bot_mark']
        if game['next_turn'] != 'user':
            return

        idx = int(query.data)
        if board[idx] != " ":
            return

        board[idx] = user_mark
        if check_win(board, user_mark):
            del GAMES[user_id]
            return await query.edit_message_text("HELAL LAN SANA GİT SEVİNÇTEN 31 ÇEK")
        if " " not in board:
            del GAMES[user_id]
            return await query.edit_message_text("🤝 Berabere! 🤝")

        avail = [i for i, v in enumerate(board) if v == " "]
        bot_idx = random.choice(avail)
        board[bot_idx] = bot_mark

        if check_win(board, bot_mark):
            del GAMES[user_id]
            return await _send_board(update, context, board, "AĞLA KÖYLÜ")
        if " " not in board:
            del GAMES[user_id]
            return await _send_board(update, context, board, "🤝 Berabere! 🤝")

        game['next_turn'] = 'user'
        await _send_board(update, context, board, "🔄 Sıra sende.")

    def run_bot():
        # Önce ortam değişkenine bak
        token = os.getenv("7767671637:AAGaQ8Zph3rfkbVD1pn3zwgzv4tZzrTsfI0")
        if not token:
            # Kullanıcıdan prompt ile token al
            token = input("7767671637:AAGaQ8Zph3rfkbVD1pn3zwgzv4tZzrTsfI0: ").strip()
            if not token:
                logger.error("Bot token’ı girilmedi. Çıkılıyor.")
                sys.exit(1)
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("play", play))
        app.add_handler(CallbackQueryHandler(button))
        logger.info("Bot başladı...")
        app.run_polling()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import unittest

        class TestWinLogic(unittest.TestCase):
            def test_empty(self):
                self.assertFalse(check_win([" "] * 9, "X"))
                self.assertFalse(check_win([" "] * 9, "O"))

            def test_top_row(self):
                self.assertTrue(check_win(["X", "X", "X"] + [" "] * 6, "X"))

            def test_middle_row(self):
                self.assertTrue(check_win([" "] * 3 + ["O", "O", "O"] + [" "] * 3, "O"))

            def test_bottom_row(self):
                self.assertTrue(check_win([" "] * 6 + ["X", "X", "X"], "X"))

            def test_col_win(self):
                self.assertTrue(check_win(["O", " ", " "] * 3, "O"))

            def test_diag_win(self):
                self.assertTrue(check_win(["X", " ", " "] + [" ", "X", " "] + [" ", " ", "X"], "X"))
                self.assertTrue(check_win([" ", " ", "O", " ", "O", " ", "O", " ", " "], "O"))

            def test_multiple_wins(self):
                board = [
                    "X", "X", "X",
                    "X", "O", " ",
                    "X", " ", "O",
                ]
                self.assertTrue(check_win(board, "X"))

            def test_invalid_mark(self):
                board = ["Z"] * 9
                self.assertFalse(check_win(board, "Z"))

            def test_no_false_positive(self):
                board = ["X", "O", "X", "O", "X", "O", "O", "X", "O"]
                self.assertFalse(check_win(board, "X"))
                self.assertFalse(check_win(board, "O"))

        unittest.main(argv=[sys.argv[0]])
    else:
        if not TELEGRAM_AVAILABLE:
            print(
                "Error: `python-telegram-bot` not installed.\n"
                "Install with: pip install python-telegram-bot"
            )
            return
        run_bot()

if __name__ == "__main__":
    main()
