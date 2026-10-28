# ALO Games

Шаблон сайта с минииграми на FastAPI: крестики-нолики, морской бой, «Четыре в ряд» на 3–4 игрока, шашки, Wordle на русском и виселица. В играх с ботами можно играть с ботом, в Wordle и виселице — одному или в дуэли с человеком. За партии начисляются очки ALO, по ним строится рейтинг.

## Запуск

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Открой http://127.0.0.1:8000. Чтобы проверить игру с человеком, зарегистрируй двух игроков в двух разных браузерах (или обычном окне и режиме инкогнито).

Переменная `SECRET_KEY` подписывает сессии — перед публикацией задай свою.

## Структура

    app/main.py              страницы, регистрация, вход, WebSocket /ws/{игра}
    app/database.py          модель User (SQLite, файл alo.db)
    app/security.py          хеширование паролей
    app/scoring.py           начисление ALO (таблица очков POINTS)
    app/room.py              базовая партия (Room): места, выход, итог, очки
    app/lobby.py             реестр игр, поиск соперников, цикл сообщений
    app/games/tictactoe.py   крестики-нолики: логика, бот, комната
    app/games/battleship.py  морской бой
    app/games/connect4.py    четыре в ряд на 3-4 игрока
    app/games/checkers.py    русские шашки: правила, бот (минимакс), комната
    app/games/puzzle.py      общая часть Wordle и виселицы (solo / дуэль)
    app/games/wordle.py      Wordle
    app/games/hangman.py     виселица
    app/games/words_ru.py    словари слов (дополняй своими)
    app/templates/           Jinja2-шаблоны
    app/static/              CSS и JS (common.js — общая часть всех игр)

## Как добавить новую игру

1. Новый файл `app/games/<игра>.py` с классом-наследником `Room`: переопределяешь `state(seat)` (что видит игрок) и `on_message(seat, data)` (что он прислал). Окончание партии — `await self.finish(победитель_или_None)`, очки начислятся сами.
2. Добавь класс в `ROOMS`, допустимые режимы в `MODES` и число игроков для pvp в `SIZES` в `app/lobby.py`.
3. Добавь запись в `GAMES` в `main.py`, шаблон `templates/<slug>.html` и скрипт, который вызывает `createGame({game, render})` из `common.js`.
