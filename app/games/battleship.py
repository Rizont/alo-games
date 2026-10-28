import asyncio
import random

from ..room import Room, as_int

SIZE = 10
FLEET = [5, 4, 3, 3, 2]  # длины кораблей
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def neighbors(cell: int) -> list[int]:
    r, c = divmod(cell, SIZE)
    return [(r + dr) * SIZE + c + dc for dr in (-1, 0, 1) for dc in (-1, 0, 1)
            if 0 <= r + dr < SIZE and 0 <= c + dc < SIZE]


def random_fleet() -> list[list[int]]:
    """Случайная расстановка. Корабли не касаются друг друга, даже углами."""
    while True:
        blocked: set[int] = set()
        ships: list[list[int]] = []
        for length in FLEET:
            for _ in range(100):
                horizontal = random.random() < 0.5
                r = random.randrange(SIZE if horizontal else SIZE - length + 1)
                c = random.randrange(SIZE - length + 1 if horizontal else SIZE)
                cells = [r * SIZE + c + k if horizontal else (r + k) * SIZE + c for k in range(length)]
                if blocked.isdisjoint(cells):
                    break
            else:
                break  # не нашли место — начинаем расстановку заново
            ships.append(cells)
            for x in cells:
                blocked.update(neighbors(x))
        else:
            return ships


def bot_shot(shots: set[int], hits: set[int], sunk: set[int]) -> int:
    """Бот добивает раненый корабль (продолжает линию), иначе стреляет по шахматной сетке."""
    live = hits - sunk
    strong, weak = [], []
    for h in live:
        r, c = divmod(h, SIZE)
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE and rr * SIZE + cc not in shots:
                br, bc = r - dr, c - dc
                back = br * SIZE + bc if 0 <= br < SIZE and 0 <= bc < SIZE else -1
                (strong if back in live else weak).append(rr * SIZE + cc)
    if strong or weak:
        return random.choice(strong or weak)
    free = [i for i in range(SIZE * SIZE) if i not in shots]
    parity = [i for i in free if (i // SIZE + i % SIZE) % 2 == 0]
    return random.choice(parity or free)


class BattleshipRoom(Room):
    def __init__(self, mode, players):
        super().__init__(mode, players)
        self.phase = "setup"  # "setup" -> "battle"
        self.ships = [random_fleet(), random_fleet()]
        self.ready = [p is None for p in players]  # бот готов сразу
        self.shots: list[set[int]] = [set(), set()]  # shots[i] — куда стрелял игрок i

    # --- вспомогательное ---
    def _sunk_cells(self, shooter: int) -> set[int]:
        out: set[int] = set()
        for ship in self.ships[1 - shooter]:
            if all(c in self.shots[shooter] for c in ship):
                out.update(ship)
        return out

    def _ships_left(self, owner: int) -> int:
        return sum(1 for ship in self.ships[owner] if not all(c in self.shots[1 - owner] for c in ship))

    # --- состояние для клиента ---
    def state(self, seat):
        me, opp = seat, 1 - seat
        mine = [""] * (SIZE * SIZE)
        for ship in self.ships[me]:
            for c in ship:
                mine[c] = "H" if c in self.shots[opp] else "S"
        for c in self.shots[opp]:
            if not mine[c]:
                mine[c] = "M"
        enemy_cells = {c for ship in self.ships[opp] for c in ship}
        sunk = self._sunk_cells(me)
        enemy = [""] * (SIZE * SIZE)
        for c in self.shots[me]:
            enemy[c] = "K" if c in sunk else "H" if c in enemy_cells else "M"
        if self.result == "win":  # в конце показываем, где стояли корабли соперника
            for c in enemy_cells:
                enemy[c] = enemy[c] or "S"
        s = self.base_state(seat)
        s.update(phase=self.phase, mine=mine, enemy=enemy, ready=self.ready,
                 left_me=self._ships_left(me), left_opp=self._ships_left(opp))
        return s

    # --- события ---
    async def on_message(self, seat, data):
        kind = data.get("type")
        if self.result:
            return
        if self.phase == "setup" and not self.ready[seat]:
            if kind == "shuffle":
                self.ships[seat] = random_fleet()
                await self.broadcast()
            elif kind == "ready":
                self.ready[seat] = True
                if all(self.ready):
                    self.phase = "battle"
                    self.turn = random.randrange(2)
                    self.played = True
                await self.broadcast()
                await self._bot_turns()
        elif self.phase == "battle" and kind == "fire" and seat == self.turn:
            cell = as_int(data.get("cell"))
            if cell is not None and 0 <= cell < SIZE * SIZE and cell not in self.shots[seat]:
                await self._fire(seat, cell)
                await self._bot_turns()

    async def after_start(self):
        await self._bot_turns()

    async def _fire(self, seat, cell):
        opp = 1 - seat
        self.shots[seat].add(cell)
        hit = any(cell in ship for ship in self.ships[opp])
        if hit and self._ships_left(opp) == 0:
            await self.finish(seat)
            return
        if not hit:  # промах — ход переходит; попадание — стреляешь ещё раз
            self.turn = opp
        await self.broadcast()

    async def _bot_turns(self):
        while not self.result and self.phase == "battle" and self.players[self.turn] is None:
            await asyncio.sleep(0.8)
            if self.result:
                return
            bot, human = self.turn, 1 - self.turn
            enemy_cells = {c for ship in self.ships[human] for c in ship}
            hits = self.shots[bot] & enemy_cells
            await self._fire(bot, bot_shot(self.shots[bot], hits, self._sunk_cells(bot)))
