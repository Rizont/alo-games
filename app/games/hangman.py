import random

from .puzzle import PuzzleRoom
from .words_ru import ALPHABET, HANGMAN_WORDS, normalize

LIVES = 6  # столько ошибок можно сделать


class HangmanRoom(PuzzleRoom):
    def __init__(self, mode, players):
        super().__init__(mode, players, random.choice(HANGMAN_WORDS))
        self.guessed: list[set[str]] = [set() for _ in players]
        self.wrong = [0] * self.n

    def _revealed(self, seat: int) -> int:
        return sum(1 for ch in self.answer if ch in self.guessed[seat])

    def state(self, seat):
        opp = self.opponent(seat)
        s = self.base_state(seat)
        s.update(
            masked=[ch if ch in self.guessed[seat] else "" for ch in self.answer],
            guessed=sorted(self.guessed[seat]), wrong=self.wrong[seat], lives=LIVES,
            failed=seat in self.failed, answer=self.answer if self.result else None,
            opp=None if opp is None else {"revealed": self._revealed(opp), "total": len(self.answer), "wrong": self.wrong[opp]},
        )
        return s

    async def on_message(self, seat, data):
        if data.get("type") != "letter" or self.result or seat in self.failed:
            return
        letter = normalize(str(data.get("letter", "")))
        if len(letter) != 1 or letter not in ALPHABET:
            await self.error(seat, "Нужна одна русская буква")
            return
        if letter in self.guessed[seat]:
            await self.error(seat, "Эта буква уже была")
            return
        self.played = True
        self.guessed[seat].add(letter)
        if letter not in self.answer:
            self.wrong[seat] += 1
        solved = all(ch in self.guessed[seat] for ch in self.answer)
        await self.settle(seat, solved, not solved and self.wrong[seat] >= LIVES)
