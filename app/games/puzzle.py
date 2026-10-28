from ..room import Room


class PuzzleRoom(Room):
    """Общая часть Wordle и «Виселицы»: одно загаданное слово, режимы solo и pvp-дуэль.
    В дуэли побеждает тот, кто первым угадал слово; если проиграли оба — ничья."""

    def __init__(self, mode, players, answer: str):
        super().__init__(mode, players)
        self.answer = answer
        self.failed: set[int] = set()

    def opponent(self, seat: int) -> int | None:
        return 1 - seat if self.n == 2 else None

    async def settle(self, seat: int, solved: bool, failed: bool):
        reason = f"Слово: {self.answer.upper()}"
        if solved:
            await self.finish(seat, reason)
            return
        if failed:
            self.failed.add(seat)
            active = [i for i in range(self.n) if i not in self.failed and i not in self.gone]
            if not active:  # попытки закончились у всех
                await self.finish(None, reason, loss_all=self.n == 1)
                return
        await self.broadcast()
