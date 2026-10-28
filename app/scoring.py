from .database import SessionLocal, User

# Сколько ALO даётся за исход партии. Меняй числа здесь.
POINTS = {
    "bot": {"win": 10, "draw": 2, "loss": -3},
    "pvp": {"win": 25, "draw": 5, "loss": -15},      # 1 на 1 с человеком
    "multi": {"win": 40, "draw": 8, "loss": -10},    # партия на 3-4 человека
}
COUNTER = {"win": "wins", "draw": "draws", "loss": "losses"}


def apply_result(user_id: int, mode: str, outcome: str) -> int:
    """Начисляет ALO и возвращает реальное изменение (ALO не уходит ниже 0)."""
    with SessionLocal() as db:
        user = db.get(User, user_id)
        new_alo = max(0, user.alo + POINTS[mode][outcome])
        delta = new_alo - user.alo
        user.alo = new_alo
        counter = COUNTER[outcome]
        setattr(user, counter, getattr(user, counter) + 1)
        db.commit()
        return delta
