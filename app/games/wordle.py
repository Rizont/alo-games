import random

from .puzzle import PuzzleRoom
from .words_ru import ALPHABET, WORDLE_WORDS, normalize

MAX_TRIES = 6
WORD_LEN = 5


def feedback(guess: str, answer: str) -> str:
    """'g' — буква на месте, 'y' — есть в слове, но не здесь, 'b' — в слове нет (или лишняя)."""
    result = ["b"] * WORD_LEN
    rest = list(answer)
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = "g"
            rest[i] = None
    for i, g in enumerate(guess):
        if result[i] == "b" and g in rest:
            result[i] = "y"
            rest[rest.index(g)] = None
    return "".join(result)


class WordleRoom(PuzzleRoom):
    def __init__(self, mode, players):
        super().__init__(mode, players, random.choice(WORDLE_WORDS))
        self.rows: list[list[tuple[str, str]]] = [[] for _ in players]  # (слово, подсказка)

    def state(self, seat):
        opp = self.opponent(seat)
        s = self.base_state(seat)
        s.update(
            rows=[{"word": w, "fb": f} for w, f in self.rows[seat]],
            opp=[f for _, f in self.rows[opp]] if opp is not None else [],  # у соперника видны только цвета
            max=MAX_TRIES, failed=seat in self.failed,
            answer=self.answer if self.result else None,
        )
        return s

    async def on_message(self, seat, data):
        if data.get("type") != "guess" or self.result or seat in self.failed:
            return
        word = normalize(str(data.get("word", "")))
        if len(word) != WORD_LEN or any(ch not in ALPHABET for ch in word):
            await self.error(seat, "Нужно слово из 5 русских букв")
            return
        self.played = True
        fb = feedback(word, self.answer)
        self.rows[seat].append((word, fb))
        solved = fb == "g" * WORD_LEN
        await self.settle(seat, solved, not solved and len(self.rows[seat]) >= MAX_TRIES)
