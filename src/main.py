import random
import tkinter as tk

from GameBoard import GameBoard
from Structures import Player, Move
from StatusDisplay import StatusDisplay
from MenuBar import MenuBar

# Constants
BOARD_SIZE = (3, 3)
DEFAULT_PLAYERS = [
    Player(symbol="X", name="Red", color="#d31626"),
    Player(symbol="O", name="Blue", color="#0079c8"),
]

# ============================
# ===== Game Controller ======
# ============================

class GameController:
    """Handles the game logic and state"""
    def __init__(self, board_size=BOARD_SIZE, players=None):
        self.board_size = board_size
        self.players = players or DEFAULT_PLAYERS
        self.current_player_index = 0
        self.current_player = self.players[self.current_player_index]
        self.game_won = False
        self.winner_combination = []
        self.ai_types = ["minimax", "random", "greedy"]
        self.player_ai_type = {player.symbol: "minimax" for player in self.players}
        self._initialize_board()

    def set_ai_type(self, player_index, ai_type):
        self.player_ai_type[self.players[player_index].symbol] = ai_type

    def _initialize_board(self):
        self.board_state = [[Move(row, col) for col in range(self.board_size[1])] for row in range(self.board_size[0])]
        self.winning_combinations = self._calculate_winning_combinations()

    def _calculate_winning_combinations(self):
        rows = [[(move.row, move.col) for move in row] for row in self.board_state]
        cols = [list(col) for col in zip(*rows)]
        diag1 = [rows[i][i] for i in range(self.board_size[0])]
        diag2 = [rows[i][self.board_size[0] - i - 1] for i in range(self.board_size[0])]
        return rows + cols + [diag1, diag2]

    def is_valid_move(self, move: Move) -> bool:
        return not self.game_won and self.board_state[move.row][move.col].symbol == ""

    def apply_move(self, move: Move):
        row, col = move.row, move.col
        self.board_state[row][col] = move

        # Check if the move resulted in a win
        for combination in self.winning_combinations:
            symbols = {self.board_state[r][c].symbol for r, c in combination}
            if len(symbols) == 1 and "" not in symbols:
                self.game_won = True
                self.winner_combination = combination
                break

    def switch_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_player = self.players[self.current_player_index]

    def has_winner(self) -> str or bool:
        # Check all winning combinations to see if there is a winner
        for combination in self.winning_combinations:
            symbols = {self.board_state[r][c].symbol for r, c in combination}
            if len(symbols) == 1 and "" not in symbols:
                # Return the winning player's symbol
                return symbols.pop()

        return False

    def is_tie(self) -> bool:
        # Check if the game is a tie
        return not self.game_won and all(move.symbol for row in self.board_state for move in row)

    def reset_game(self):
        self._initialize_board()
        self.game_won = False
        self.winner_combination = []
        self.current_player_index = 0
        self.current_player = self.players[self.current_player_index]

    def toggle_ai(self, player_index):
        self.players[player_index] = self.players[player_index]._replace(is_ai=not self.players[player_index].is_ai)
        if self.current_player_index == player_index:  # Update current player if it's the one being toggled
            self.current_player = self.players[player_index]

    def minimax(self, depth, is_maximizing_player, alpha, beta):
        # If the game is won or finished, return a score
        if self.has_winner() == self.current_player.symbol:
            return 1  # AI wins
        elif self.has_winner() == self.get_opponent(self.current_player).symbol:
            return -1  # Opponent wins

        if self.is_tie():
            return 0  # Tie game

        if is_maximizing_player:
            max_eval = float('-inf')
            for r in range(self.board_size[0]):
                for c in range(self.board_size[1]):
                    if self.board_state[r][c].symbol == "":
                        self.board_state[r][c] = Move(r, c, self.current_player.symbol)
                        eval = self.minimax(depth + 1, False, alpha, beta)
                        self.board_state[r][c] = Move(r, c, "")
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)  # Update alpha
                        if beta <= alpha:  # Pruning
                            break  # Prune the branch
            return max_eval
        else:
            min_eval = float('inf')
            opponent = self.get_opponent(self.current_player)
            for r in range(self.board_size[0]):
                for c in range(self.board_size[1]):
                    if self.board_state[r][c].symbol == "":
                        self.board_state[r][c] = Move(r, c, opponent.symbol)
                        eval = self.minimax(depth + 1, True, alpha, beta)
                        self.board_state[r][c] = Move(r, c, "")
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)  # Update beta
                        if beta <= alpha:  # Pruning
                            break  # Prune the branch
            return min_eval

    def best_move(self):
        ai_type = self.player_ai_type[self.current_player.symbol]
        if ai_type == "random":
            return self.random_move()
        elif ai_type == "minimax":
            return self._minimax_best_move()
        elif ai_type == "greedy":
            return self.greedy_move()

    def greedy_move(self):
        # Check for a winning move for the AI
        for r in range(self.board_size[0]):
            for c in range(self.board_size[1]):
                if self.board_state[r][c].symbol == "":  # Check if the cell is empty
                    move = Move(r, c, self.current_player.symbol)
                    self.board_state[r][c] = move
                    if self.has_winner() == self.current_player.symbol:  # AI can win
                        self.board_state[r][c] = Move(r, c, "")  # Reset move
                        return r, c  # Return the winning move
                    self.board_state[r][c] = Move(r, c, "")  # Reset move

        # Check for a blocking move (if the opponent can win)
        opponent = self.get_opponent(self.current_player)
        for r in range(self.board_size[0]):
            for c in range(self.board_size[1]):
                if self.board_state[r][c].symbol == "":  # Check if the cell is empty
                    move = Move(r, c, opponent.symbol)
                    self.board_state[r][c] = move
                    if self.has_winner() == opponent.symbol:  # Opponent can win
                        self.board_state[r][c] = Move(r, c, "")  # Reset move
                        return r, c  # Block the opponent's winning move
                    self.board_state[r][c] = Move(r, c, "")  # Reset move

        # If no winning or blocking move, pick the first available move
        available_moves = [(r, c) for r in range(self.board_size[0]) for c in range(self.board_size[1])
                           if self.board_state[r][c].symbol == ""]
        return available_moves[0] if available_moves else None  # Return the first available move

    def random_move(self):
        available_moves = [(r, c) for r in range(self.board_size[0]) for c in range(self.board_size[1])
                           if self.board_state[r][c].symbol == ""]
        return random.choice(available_moves) if available_moves else None

    def _minimax_best_move(self):
        best_value = float('-inf')
        best_move = None
        # Initialize alpha and beta for the search of the best move
        alpha = float('-inf')
        beta = float('inf')

        # Evaluate all possible moves and choose the one with the best evaluation
        for r in range(self.board_size[0]):
            for c in range(self.board_size[1]):
                if self.board_state[r][c].symbol == "":
                    self.board_state[r][c] = Move(r, c, self.current_player.symbol)
                    move_value = self.minimax(0, False, alpha, beta)
                    self.board_state[r][c] = Move(r, c, "")
                    if move_value > best_value:
                        best_value = move_value
                        best_move = (r, c)

        return best_move

    def get_opponent(self, current_player):
        return self.players[1] if current_player == self.players[0] else self.players[0]


# ============================
# ====== Main Application =====
# ============================

class TicTacToeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tic-Tac-Toe")

        self.controller = GameController()
        self.status_display = StatusDisplay(self)
        self.game_board = GameBoard(self, self.controller)
        self.menu = MenuBar(self, self.controller)

    def update_status(self, message, color="black"):
        self.status_display.update_status(message, color)

def main():
    # Print rules
    print("Welcome to Tic-Tac-Toe!")
    print("The game is played on a "+str(BOARD_SIZE[0])+"x"+str(BOARD_SIZE[1])+" board.")
    print("Turns alternate between Red (X) and Blue (O). Red goes first.")
    print("To enable AI for a player, use the Game menu.")
    print("To change the AI type, use the AI menu. (Minimax, Greedy, Random)")

    app = TicTacToeApp()
    app.mainloop()

if __name__ == "__main__":
    main()