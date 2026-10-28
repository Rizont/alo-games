import asyncio
import random

from ..room import Room, as_int

COLS, ROWS = 9, 7  # поле побольше обычного: играют 3-4 человека
EMPTY = -1


def landing(board: list[int], col: int) -> int | None:
    """Индекс клетки, куда упадёт фишка в колонке, или None, если колонка полна."""
    for r in range(ROWS - 1, -1, -1):
        if board[r * COLS + col] == EMPTY:
            return r * COLS + col
    return None


def check(board: list[int], idx: int) -> list[int]:
    """Если фишка в idx замкнула 4+ в ряд — возвращает эти клетки."""
    seat = board[idx]
    r, c = divmod(idx, COLS)
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        line = [idx]
        for sign in (1, -1):
            rr, cc = r + dr * sign, c + dc * sign
            while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr * COLS + cc] == seat:
                line.append(rr * COLS + cc)
                rr += dr * sign
                cc += dc * sign
        if len(line) >= 4:
            return line
    return []


def _wins(board, idx, seat) -> bool:
    board[idx] = seat
    ok = bool(check(board, idx))
    board[idx] = EMPTY
    return ok


def bot_choice(board: list[int], seat: int, n: int) -> int:
    """Бот: выигрывает, если может; блокирует чужую победу; не подставляет соперникам ход; любит центр."""
    moves = [(c, landing(board, c)) for c in range(COLS) if landing(board, c) is not None]
    for c, i in moves:
        if _wins(board, i, seat):
            return c
    for opp in range(n):
        if opp != seat:
            for c, i in moves:
                if _wins(board, i, opp):
                    return c
    safe = []
    for c, i in moves:
        board[i] = seat
        above = landing(board, c)
        danger = above is not None and any(_wins(board, above, o) for o in range(n) if o != seat)
        board[i] = EMPTY
        if not danger:
            safe.append(c)
    pool = safe or [c for c, _ in moves]
    return min(pool, key=lambda c: abs(c - COLS // 2) + random.random())


class ConnectFourRoom(Room):
    def __init__(self, mode, players):
        super().__init__(mode, players)
        self.board = [EMPTY] * (COLS * ROWS)
        self.line: list[int] = []

    def state(self, seat):
        s = self.base_state(seat)
        s.update(board=self.board, line=self.line, cols=COLS, rows=ROWS)
        return s

    async def after_start(self):
        await self._bot_turns()

    async def on_message(self, seat, data):
        col = as_int(data.get("col"))
        if data.get("type") != "drop" or col is None:
            return
        if self.result or seat != self.turn or not 0 <= col < COLS or landing(self.board, col) is None:
            return
        await self._drop(seat, col)
        await self._bot_turns()

    async def on_leave(self, seat):
        humans_left = [i for i, p in enumerate(self.players) if p and i not in self.gone]
        if not humans_left:
            await self.finish(None, "Все игроки вышли")
            return
        if self.turn in self.gone:
            self._next_turn()
            await self.broadcast()
            await self._bot_turns()

    def _next_turn(self):
        self.turn = (self.turn + 1) % self.n
        while self.turn in self.gone:
            self.turn = (self.turn + 1) % self.n

    async def _drop(self, seat, col):
        self.played = True
        idx = landing(self.board, col)
        self.board[idx] = seat
        line = check(self.board, idx)
        if line:
            self.line = line
            await self.finish(seat)
        elif all(v != EMPTY for v in self.board[:COLS]):  # верхний ряд заполнен — поле полное
            await self.finish(None)
        else:
            self._next_turn()
            await self.broadcast()

    async def _bot_turns(self):
        while not self.result and self.players[self.turn] is None:
            await asyncio.sleep(0.7)
            if self.result:
                return
            await self._drop(self.turn, bot_choice(self.board, self.turn, self.n))
