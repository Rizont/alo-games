import asyncio
import random

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def other(mark: str) -> str:
    return "O" if mark == "X" else "X"


def check(board: list[str]) -> tuple[str | None, list[int]]:
    """Возвращает ('X'|'O', выигрышная линия), ('draw', []) или (None, [])."""
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], [a, b, c]
    if all(board):
        return "draw", []
    return None, []


def bot_move(board: list[str], me: str) -> int:
    """Бот: выигрывает, если может; иначе блокирует; иначе центр; иначе случайно.
    Такого бота можно обыграть «вилкой», так что победа над ним возможна."""
    free = [i for i, v in enumerate(board) if not v]
    for mark in (me, other(me)):
        for i in free:
            trial = board.copy()
            trial[i] = mark
            if check(trial)[0] == mark:
                return i
    if 4 in free:
        return 4
    return random.choice(free)


# ---------- комната (сетевая часть) ----------
from ..room import Room, as_int  # noqa: E402


class TicTacToeRoom(Room):
    MARKS = "XO"  # место 0 — X (ходит первым), место 1 — O

    def __init__(self, mode, players):
        super().__init__(mode, players)
        self.board = [""] * 9
        self.line: list[int] = []

    def state(self, seat):
        s = self.base_state(seat)
        s.update(board=self.board, line=self.line)
        return s

    async def after_start(self):
        await self._bot_turn()

    async def on_message(self, seat, data):
        cell = as_int(data.get("cell"))
        if data.get("type") != "move" or cell is None:
            return
        if self.result or seat != self.turn or not 0 <= cell < 9 or self.board[cell]:
            return
        await self._place(seat, cell)
        await self._bot_turn()

    async def _bot_turn(self):
        if self.result or self.players[self.turn] is not None:
            return
        await asyncio.sleep(0.6)
        if not self.result:
            await self._place(self.turn, bot_move(self.board, self.MARKS[self.turn]))

    async def _place(self, seat, cell):
        self.played = True
        self.board[cell] = self.MARKS[seat]
        winner, line = check(self.board)
        if winner == "draw":
            await self.finish(None)
        elif winner:
            self.line = line
            await self.finish(seat)
        else:
            self.turn = 1 - seat
            await self.broadcast()
