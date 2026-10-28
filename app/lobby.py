import random

from fastapi import WebSocket, WebSocketDisconnect

from .database import User
from .games.battleship import BattleshipRoom
from .games.checkers import CheckersRoom
from .games.connect4 import ConnectFourRoom
from .games.hangman import HangmanRoom
from .games.tictactoe import TicTacToeRoom
from .games.wordle import WordleRoom
from .room import Player

# Реестр игр: какая комната и сколько игроков допустимо.
ROOMS = {
    "tictactoe": TicTacToeRoom, "battleship": BattleshipRoom, "connect4": ConnectFourRoom,
    "wordle": WordleRoom, "hangman": HangmanRoom, "checkers": CheckersRoom,
}
# Допустимые режимы: "bot" (с ботами), "pvp" (с людьми), "solo" (один, для головоломок).
MODES = {
    "tictactoe": ("bot", "pvp"), "battleship": ("bot", "pvp"), "connect4": ("bot", "pvp"),
    "wordle": ("solo", "pvp"), "hangman": ("solo", "pvp"), "checkers": ("bot", "pvp"),
}
# Допустимое число игроков в режиме pvp.
SIZES = {
    "tictactoe": (2,), "battleship": (2,), "connect4": (3, 4),
    "wordle": (2,), "hangman": (2,), "checkers": (2,),
}

queues: dict[tuple[str, int], list[Player]] = {}  # очереди ожидания по (игра, число игроков)


async def handle_game(ws: WebSocket, user: User, game: str, mode: str, size: int):
    await ws.accept()
    me = Player(ws, user.id, user.username)
    key = (game, size)
    room_class = ROOMS[game]
    try:
        if mode == "solo":
            await room_class("solo", [me]).start()
        elif mode == "bot":
            seats: list[Player | None] = [me] + [None] * (size - 1)
            random.shuffle(seats)
            await room_class("bot", seats).start()
        else:
            queue = queues.setdefault(key, [])
            queue[:] = [p for p in queue if p.user_id != me.user_id]  # второй вкладкой с тем же аккаунтом не играем
            queue.append(me)
            if len(queue) >= size:
                group = queue[:size]
                del queue[:size]
                random.shuffle(group)
                await room_class("pvp", group).start()
            else:
                for p in queue:
                    try:
                        await p.ws.send_json({"type": "waiting", "have": len(queue), "need": size})
                    except Exception:
                        pass

        while True:
            data = await ws.receive_json()
            if me.room and isinstance(data, dict):
                await me.room.on_message(me.seat, data)
    except (WebSocketDisconnect, ValueError):
        pass
    finally:
        queue = queues.get(key, [])
        if me in queue:
            queue.remove(me)
            for p in queue:
                try:
                    await p.ws.send_json({"type": "waiting", "have": len(queue), "need": size})
                except Exception:
                    pass
        if me.room:
            await me.room.leave(me.seat)
