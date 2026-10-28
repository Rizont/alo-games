from dataclasses import dataclass

from fastapi import WebSocket

from .scoring import apply_result


@dataclass(eq=False)
class Player:
    ws: WebSocket
    user_id: int
    username: str
    room: "Room | None" = None
    seat: int | None = None


def as_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class Room:
    """Базовая партия. players[i] — это игрок на месте i, None — бот.
    Конкретная игра наследуется и переопределяет state(), on_message(), after_start()."""

    def __init__(self, mode: str, players: list[Player | None]):
        self.mode = mode  # "bot" или "pvp"
        self.players = players
        self.n = len(players)
        self.turn = 0
        self.result: str | None = None  # None | "win" | "draw" | "abandoned"
        self.winner: int | None = None
        self.reason = ""
        self.deltas: dict[int, int] = {}
        self.gone: set[int] = set()  # места, чьи игроки вышли
        self.played = False  # был ли сделан хотя бы один ход
        bots = players.count(None)
        counter = 0
        self.names = []
        for p in players:
            if p:
                self.names.append(p.username)
            else:
                counter += 1
                self.names.append("Бот" if bots == 1 else f"Бот {counter}")

    # --- что переопределяют игры ---
    def state(self, seat: int) -> dict:
        return self.base_state(seat)

    async def on_message(self, seat: int, data: dict):
        pass

    async def after_start(self):
        pass

    async def on_leave(self, seat: int):
        winner = 1 - seat if self.n == 2 else None
        await self.finish(winner, "Соперник вышел из игры")

    # --- общая механика ---
    def base_state(self, seat: int) -> dict:
        return {
            "type": "state", "you": seat, "names": self.names, "turn": self.turn,
            "result": self.result, "winner": self.winner, "reason": self.reason,
            "delta": self.deltas.get(seat), "gone": sorted(self.gone),
        }

    async def start(self):
        for seat, player in enumerate(self.players):
            if player:
                player.room, player.seat = self, seat
        await self.broadcast()
        await self.after_start()

    async def broadcast(self):
        for seat, player in enumerate(self.players):
            if player and seat not in self.gone:
                try:
                    await player.ws.send_json(self.state(seat))
                except Exception:
                    pass  # игрок уже отключился

    async def leave(self, seat: int):
        if self.result:
            return
        self.gone.add(seat)
        if not self.played:  # партия не началась — очки не меняются
            self.result, self.reason = "abandoned", "Партия отменена: кто-то вышел до начала игры"
            await self.broadcast()
        else:  # выход посреди партии = поражение
            await self.on_leave(seat)

    async def finish(self, winner: int | None, reason: str = ""):
        if self.result:
            return
        self.result = "draw" if winner is None else "win"
        self.winner, self.reason = winner, reason
        score_mode = "bot" if self.mode == "bot" else ("pvp" if self.n == 2 else "multi")
        for seat, player in enumerate(self.players):
            if player is None:
                continue
            if seat == winner:
                outcome = "win"
            elif seat in self.gone or winner is not None:
                outcome = "loss"
            else:
                outcome = "draw"
            self.deltas[seat] = apply_result(player.user_id, score_mode, outcome)
        await self.broadcast()
