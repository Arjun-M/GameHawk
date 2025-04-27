from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle
import random
import uuid

class XOGameManager:
    def __init__(self):
        self.games = {}

    def choose_mode(self, query):
        keyboard = [
            [InlineKeyboardButton("Play with Friend", switch_inline_query="xo")],
            [InlineKeyboardButton("Play with Computer", callback_data='xo_computer')]
        ]
        query.edit_message_text("Select your game mode:", reply_markup=InlineKeyboardMarkup(keyboard))

    def choose_symbol(self, query, context):
        keyboard = [
            [InlineKeyboardButton("❌️", callback_data='choose_X')],
            [InlineKeyboardButton("⭕️", callback_data='choose_O')]
        ]
        query.edit_message_text("Play X-O as ❌️ or ⭕️ :", reply_markup=InlineKeyboardMarkup(keyboard))

    def set_player_symbol(self, query, context, data):
        symbol = '❌️' if data == 'choose_X' else '⭕️'
        context.user_data['player_symbol'] = symbol
        context.user_data['computer_symbol'] = '⭕️' if symbol == '❌️' else '❌️'
        self.ask_difficulty(query)

    def ask_difficulty(self, query):
        keyboard = [
            [InlineKeyboardButton("Easy", callback_data='level_easy')],
            [InlineKeyboardButton("Medium", callback_data='level_medium')],
            [InlineKeyboardButton("Hard", callback_data='level_hard')]
        ]
        query.edit_message_text("Choose your difficulty level from Easy, Medium or Hard.", reply_markup=InlineKeyboardMarkup(keyboard))

    def set_difficulty(self, query, context, data):
        context.user_data['level'] = data.split('_')[1]
        self.ask_rounds(query)

    def ask_rounds(self, query):
        keyboard = [
            [InlineKeyboardButton("1 Round", callback_data='rounds_1')],
            [InlineKeyboardButton("3 Rounds", callback_data='rounds_3')],
            [InlineKeyboardButton("6 Rounds", callback_data='rounds_6')]
        ]
        query.edit_message_text("Choose number of rounds to play:", reply_markup=InlineKeyboardMarkup(keyboard))

    def start_game(self, query, context, data):
        user_id = query.from_user.id
        rounds = int(data.split('_')[1])
        context.user_data['rounds'] = rounds
        context.user_data['current_round'] = 1
        context.user_data['player_score'] = 0
        context.user_data['computer_score'] = 0
        self.games[user_id] = {
            'board': [' '] * 9,
            'mode': 'computer',
            'level': context.user_data['level']
        }
        self.send_board(query, context)

    def handle_inline_query(self, update, context):
        query = update.inline_query.query
        if query == "invite_xo":
            game_id = str(uuid.uuid4())
            self.games[game_id] = {
                'board': [' '] * 9,
                'players': {},
                'turn': None
            }
            results = [
                InlineQueryResultArticle(
                    id=game_id,
                    title="Invite to play XO",
                    input_message_content=InputTextMessageContent(
                        "New XO Game! Waiting for a friend to accept..."
                    ),
                    reply_markup=self.get_invite_markup(game_id)
                )
            ]
            update.inline_query.answer(results, cache_time=0)

    def get_invite_markup(self, game_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Join as ❌️", callback_data=f'invite_accept_{game_id}_❌️')],
            [InlineKeyboardButton("Join as ⭕️", callback_data=f'invite_accept_{game_id}_⭕️')]
        ])

    def accept_invite(self, query, context, data):
        parts = data.split('_')
        game_id = parts[2]
        symbol = parts[3]
        user = query.from_user

        game = self.games.get(game_id)
        if not game:
            query.edit_message_text("Invite expired or not found.")
            return

        if not game['players']:
            game['players'][user.id] = symbol
            game['turn'] = user.id
            query.edit_message_text(f"{user.first_name} joined as {symbol}\nWaiting for another player...", reply_markup=self.get_invite_markup(game_id))
        elif len(game['players']) == 1 and user.id not in game['players']:
            game['players'][user.id] = symbol
            query.edit_message_text(self.render_board(game_id), reply_markup=self.get_board_markup(game_id))
        else:
            query.answer("Game full!", show_alert=True)

    def render_board(self, game_id):
        game = self.games.get(game_id)
        if not game:
            return "Game not found."

        board = game['board']
        board_str = ''
        for i in range(0, 9, 3):
            board_str += ''.join(f"{cell if cell != ' ' else '⬜️'}" for cell in board[i:i+3]) + "\n"
        return board_str

    def get_board_markup(self, game_id):
        game = self.games.get(game_id)
        if not game:
            return InlineKeyboardMarkup([])

        buttons = []
        for i in range(0, 9, 3):
            row = []
            for j in range(3):
                idx = i + j
                cell = game['board'][idx]
                text = cell if cell != ' ' else '⬜️'
                row.append(InlineKeyboardButton(text, callback_data=f'friendmove_{game_id}_{idx}'))
            buttons.append(row)
        return InlineKeyboardMarkup(buttons)

    def friend_move(self, update, context):
        query = update.callback_query
        parts = query.data.split('_')
        game_id = parts[1]
        move_index = int(parts[2])
        user_id = query.from_user.id

        game = self.games.get(game_id)
        if not game:
            query.answer("Game not found!", show_alert=True)
            return

        if user_id not in game['players']:
            query.answer("You are not part of this game.", show_alert=True)
            return

        if game['turn'] != user_id:
            query.answer("Not your turn!", show_alert=True)
            return

        if game['board'][move_index] != ' ':
            query.answer("Cell already taken!", show_alert=True)
            return

        symbol = game['players'][user_id]
        game['board'][move_index] = symbol

        if self.check_winner(game['board'], symbol):
            query.edit_message_text(f"{query.from_user.first_name} ({symbol}) wins!\n\n" + self.render_board(game_id))
            self.games.pop(game_id, None)
            return

        if ' ' not in game['board']:
            query.edit_message_text("Draw!\n\n" + self.render_board(game_id))
            self.games.pop(game_id, None)
            return

        # Switch turn
        for pid in game['players']:
            if pid != user_id:
                game['turn'] = pid
                break

        query.edit_message_text(self.render_board(game_id), reply_markup=self.get_board_markup(game_id))

    def send_board(self, query, context):
        user_id = query.from_user.id
        board = self.games[user_id]['board']
        keyboard = []
        for i in range(0, 9, 3):
            row = []
            for j in range(3):
                idx = i + j
                text = board[idx] if board[idx] != ' ' else '⬜️'
                row.append(InlineKeyboardButton(text, callback_data=f'move_{idx}'))
            keyboard.append(row)
        query.edit_message_text("Your move:", reply_markup=InlineKeyboardMarkup(keyboard))

    def player_move(self, update, context):
        query = update.callback_query
        user_id = query.from_user.id
        move_index = int(query.data.split('_')[1])

        game = self.games.get(user_id)
        if not game:
            query.answer("Game not found!", show_alert=True)
            return

        board = game['board']
        if board[move_index] != ' ':
            query.answer("Cell already taken!", show_alert=True)
            return

        player_symbol = context.user_data['player_symbol']
        board[move_index] = player_symbol

        if self.check_winner(board, player_symbol):
            query.edit_message_text(f"You ({player_symbol}) win!\n\n" + self.render_board(user_id))
            self.games.pop(user_id, None)
            return

        if ' ' not in board:
            query.edit_message_text("Draw!\n\n" + self.render_board(user_id))
            self.games.pop(user_id, None)
            return

        self.computer_move(query, context)

    def computer_move(self, query, context):
        user_id = query.from_user.id
        game = self.games.get(user_id)
        board = game['board']
        computer_symbol = context.user_data['computer_symbol']
        player_symbol = context.user_data['player_symbol']
        level = game['level']

        if level == 'easy':
            available = [i for i, v in enumerate(board) if v == ' ']
            move = random.choice(available)
        elif level == 'medium':
            move = self.medium_move(board, player_symbol, computer_symbol)
        else:  # hard
            move = self.minimax(board, computer_symbol, computer_symbol, player_symbol)['index']

        board[move] = computer_symbol

        if self.check_winner(board, computer_symbol):
            query.edit_message_text(f"Computer ({computer_symbol}) wins!\n\n" + self.render_board(user_id))
            self.games.pop(user_id, None)
            return

        if ' ' not in board:
            query.edit_message_text("The Game was a Draw!\n\n" + self.render_board(user_id))
            self.games.pop(user_id, None)
            return

        self.send_board(query, context)

    def medium_move(self, board, player, computer):
        available = [i for i, v in enumerate(board) if v == ' ']
        for move in available:
            board_copy = board.copy()
            board_copy[move] = computer
            if self.check_winner(board_copy, computer):
                return move
        for move in available:
            board_copy = board.copy()
            board_copy[move] = player
            if self.check_winner(board_copy, player):
                return move
        return random.choice(available)

    def minimax(self, board, player, computer, opponent):
        available = [i for i, v in enumerate(board) if v == ' ']

        if self.check_winner(board, opponent):
            return {'score': -10}
        elif self.check_winner(board, computer):
            return {'score': 10}
        elif not available:
            return {'score': 0}

        moves = []
        for idx in available:
            board_copy = board.copy()
            board_copy[idx] = player
            result = self.minimax(board_copy, opponent if player == computer else computer, computer, opponent)
            moves.append({'index': idx, 'score': result['score']})

        if player == computer:
            best = max(moves, key=lambda x: x['score'])
        else:
            best = min(moves, key=lambda x: x['score'])
        return best

    def check_winner(self, board, symbol):
        win_patterns = [
            [0,1,2], [3,4,5], [6,7,8],
            [0,3,6], [1,4,7], [2,5,8],
            [0,4,8], [2,4,6]
        ]
        for pattern in win_patterns:
            if all(board[i] == symbol for i in pattern):
                return True
        return False
