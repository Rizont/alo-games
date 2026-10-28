"""Русские шашки 8×8.
Правила: ходят по тёмным клеткам; простая шашка ходит вперёд на 1, а бьёт в любую сторону;
бить обязательно; дамка ходит и бьёт на любое расстояние по диагонали; шашка, дошедшая до
последней линии во время боя, продолжает бить как дамка; сбитые фигуры снимаются после хода."""
import asyncio
import random

from ..room import Room, as_int

N = 8
DIAGS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
BOT_DEPTH = 4
QUIET_LIMIT = 40  # столько ходов подряд без взятий и ходов простых шашек — ничья


def inb(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def color_of(piece: str) -> str:
    return piece.lower()  # "w" / "b" / ""


def initial_board() -> list[list[str]]:
    board = [[""] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            if (r + c) % 2 == 1:
                if r < 3:
                    board[r][c] = "b"
                elif r > 4:
                    board[r][c] = "w"
    return board


def promotion_row(color: str) -> int:
    return 0 if color == "w" else N - 1


def jumps(board, r, c, king, color, captured):
    """Все одиночные взятия из клетки: (куда приземлились, кого сбили)."""
    out = []
    for dr, dc in DIAGS:
        if king:
            rr, cc = r + dr, c + dc
            while inb(rr, cc) and board[rr][cc] == "":
                rr, cc = rr + dr, cc + dc
            if inb(rr, cc) and (rr, cc) not in captured and color_of(board[rr][cc]) != color:
                lr, lc = rr + dr, cc + dc
                while inb(lr, lc) and board[lr][lc] == "":
                    out.append((lr, lc, rr, cc))
                    lr, lc = lr + dr, lc + dc
        else:
            mr, mc, lr, lc = r + dr, c + dc, r + 2 * dr, c + 2 * dc
            if (inb(lr, lc) and (mr, mc) not in captured and board[mr][mc] != ""
                    and color_of(board[mr][mc]) != color and board[lr][lc] == ""):
                out.append((lr, lc, mr, mc))
    return out


def sequences(board, r, c, king, color, captured, path):
    """Все полные цепочки взятий из (r, c). Сбитые фигуры остаются на доске до конца хода
    (через них нельзя прыгать дважды), а если бой можно продолжить — продолжать обязательно."""
    groups: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for lr, lc, vr, vc in jumps(board, r, c, king, color, captured):
        groups.setdefault((vr, vc), []).append((lr, lc))
    result = []
    for victim, landings in groups.items():
        cap = captured | {victim}
        cont, stop = [], []
        for lr, lc in landings:
            now_king = king or lr == promotion_row(color)
            further = sequences(board, lr, lc, now_king, color, cap, path + [(lr, lc)])
            if further:
                cont.extend(further)
            else:
                stop.append((path + [(lr, lc)], cap))
        result.extend(cont or stop)
    return result


def legal_moves(board, color):
    """Ходы цвета: список (путь, сбитые). Если есть взятие — возвращаются только взятия."""
    captures = []
    for r in range(N):
        for c in range(N):
            piece = board[r][c]
            if piece and color_of(piece) == color:
                board[r][c] = ""  # ходящая фигура освобождает свою клетку
                captures.extend(sequences(board, r, c, piece.isupper(), color, frozenset(), [(r, c)]))
                board[r][c] = piece
    if captures:
        return captures
    moves = []
    step = -1 if color == "w" else 1
    for r in range(N):
        for c in range(N):
            piece = board[r][c]
            if not piece or color_of(piece) != color:
                continue
            if piece.isupper():
                for dr, dc in DIAGS:
                    rr, cc = r + dr, c + dc
                    while inb(rr, cc) and board[rr][cc] == "":
                        moves.append(([(r, c), (rr, cc)], frozenset()))
                        rr, cc = rr + dr, cc + dc
            else:
                for dc in (-1, 1):
                    rr, cc = r + step, c + dc
                    if inb(rr, cc) and board[rr][cc] == "":
                        moves.append(([(r, c), (rr, cc)], frozenset()))
    return moves


def apply_move(board, move):
    path, captured = move
    new = [row[:] for row in board]
    r0, c0 = path[0]
    r1, c1 = path[-1]
    piece = new[r0][c0]
    new[r0][c0] = ""
    for vr, vc in captured:
        new[vr][vc] = ""
    if piece.islower() and any(r == promotion_row(piece) for r, _ in path[1:]):
        piece = piece.upper()
    new[r1][c1] = piece
    return new


# ---------- бот ----------
def evaluate(board, color) -> float:
    score = 0.0
    for r in range(N):
        for c in range(N):
            p = board[r][c]
            if not p:
                continue
            if p.isupper():
                value = 30
            else:
                value = 10 + ((N - 1 - r) if color_of(p) == "w" else r) * 0.6
            score += value if color_of(p) == color else -value
    return score


def _search(board, color, depth, alpha, beta) -> float:
    moves = legal_moves(board, color)
    if not moves:
        return -10_000 - depth  # нет ходов — поражение (чем раньше, тем хуже)
    if depth == 0:
        return evaluate(board, color)
    best = float("-inf")
    other = "b" if color == "w" else "w"
    for move in moves:
        score = -_search(apply_move(board, move), other, depth - 1, -beta, -alpha)
        best = max(best, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best


def best_move(board, color, depth=BOT_DEPTH):
    moves = legal_moves(board, color)
    other = "b" if color == "w" else "w"
    scored = [(-_search(apply_move(board, m), other, depth - 1, float("-inf"), float("inf")) + random.random() * 0.5, m)
              for m in moves]
    return max(scored, key=lambda x: x[0])[1]


# ---------- комната ----------
class CheckersRoom(Room):
    COLORS = "wb"  # место 0 — белые (ходят первыми, снизу), место 1 — чёрные

    def __init__(self, mode, players):
        super().__init__(mode, players)
        self.board = initial_board()
        self.quiet = 0
        self.last: list[int] = []
        self.legal = legal_moves(self.board, "w")

    def state(self, seat):
        s = self.base_state(seat)
        moves: dict[str, list[int]] = {}
        if seat == self.turn and not self.result:
            for path, _ in self.legal:
                moves.setdefault(str(path[0][0] * N + path[0][1]), []).append(path[-1][0] * N + path[-1][1])
        s.update(
            board=[self.board[i // N][i % N] for i in range(N * N)],
            moves=moves, last=self.last,
            must_capture=bool(self.legal and self.legal[0][1]),
        )
        return s

    async def after_start(self):
        await self._bot_turn()

    async def on_message(self, seat, data):
        if data.get("type") != "move" or self.result or seat != self.turn:
            return
        src, dst = as_int(data.get("from")), as_int(data.get("to"))
        if src is None or dst is None:
            return
        options = [m for m in self.legal
                   if m[0][0] == divmod(src, N) and m[0][-1] == divmod(dst, N)]
        if not options:
            return
        await self._play(seat, max(options, key=lambda m: len(m[1])))
        await self._bot_turn()

    async def _bot_turn(self):
        if self.result or self.players[self.turn] is not None:
            return
        await asyncio.sleep(0.5)
        color = self.COLORS[self.turn]
        move = await asyncio.to_thread(best_move, [row[:] for row in self.board], color)
        if not self.result:
            await self._play(self.turn, move)

    async def _play(self, seat, move):
        path, captured = move
        r0, c0 = path[0]
        was_man = self.board[r0][c0].islower()
        self.board = apply_move(self.board, move)
        self.played = True
        self.last = [r * N + c for r, c in path]
        self.quiet = 0 if (captured or was_man) else self.quiet + 1
        self.turn = 1 - seat
        self.legal = legal_moves(self.board, self.COLORS[self.turn])
        if not self.legal:  # у соперника нет ходов или фигур
            await self.finish(seat)
        elif self.quiet >= QUIET_LIMIT:
            await self.finish(None, "Слишком долго без взятий")
        else:
            await self.broadcast()
