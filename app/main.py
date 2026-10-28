import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, WebSocket
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection

from .database import Base, SessionLocal, User, engine
from .lobby import SIZES, handle_game
from .security import hash_password, verify_password

BASE_DIR = Path(__file__).resolve().parent

GAMES = [
    {"slug": "tictactoe", "title": "Крестики-нолики", "text": "Три в ряд на поле 3×3. С ботом или с живым соперником.", "players": "2 игрока", "ready": True},
    {"slug": "battleship", "title": "Морской бой", "text": "Расставь флот и потопи корабли соперника. Попал — стреляешь ещё раз.", "players": "2 игрока", "ready": True},
    {"slug": "connect4", "title": "Четыре в ряд", "text": "Фишки падают вниз. Собери четыре в линию раньше остальных.", "players": "3–4 игрока", "ready": True},
    {"slug": "rps", "title": "Камень, ножницы, бумага", "text": "Скоро", "players": "", "ready": False},
]
PLAYABLE = {g["slug"] for g in GAMES if g["ready"]}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="ALO Games", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-only-change-me"), same_site="lax")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def current_user(conn: HTTPConnection) -> User | None:
    user_id = conn.session.get("uid")
    if not user_id:
        return None
    with SessionLocal() as db:
        return db.get(User, user_id)


def render(request: Request, name: str, status_code: int = 200, **context):
    context["user"] = current_user(request)
    return templates.TemplateResponse(request, name, context, status_code=status_code)


@app.get("/")
def index(request: Request):
    return render(request, "index.html", games=GAMES)


@app.get("/games/{slug}")
def game_page(request: Request, slug: str):
    if slug not in PLAYABLE:
        raise HTTPException(status_code=404)
    if not current_user(request):
        return RedirectResponse("/login", status_code=303)
    return render(request, f"{slug}.html")


@app.get("/leaderboard")
def leaderboard(request: Request):
    with SessionLocal() as db:
        players = db.scalars(select(User).order_by(User.alo.desc(), User.wins.desc(), User.id).limit(50)).all()
    return render(request, "leaderboard.html", players=players)


@app.get("/register")
def register_page(request: Request):
    return render(request, "auth.html", mode="register", error=None)


@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    error = None
    if not re.fullmatch(r"\w{3,20}", username):
        error = "Имя: от 3 до 20 символов — буквы, цифры и подчёркивание."
    elif len(password) < 6:
        error = "Пароль должен быть не короче 6 символов."
    else:
        with SessionLocal() as db:
            if db.scalar(select(User).where(User.username == username)):
                error = "Это имя уже занято. Выбери другое."
            else:
                user = User(username=username, password_hash=hash_password(password))
                db.add(user)
                db.commit()
                request.session["uid"] = user.id
                return RedirectResponse("/", status_code=303)
    return render(request, "auth.html", status_code=400, mode="register", error=error)


@app.get("/login")
def login_page(request: Request):
    return render(request, "auth.html", mode="login", error=None)


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username.strip()))
    if user and verify_password(password, user.password_hash):
        request.session["uid"] = user.id
        return RedirectResponse("/", status_code=303)
    return render(request, "auth.html", status_code=400, mode="login", error="Неверное имя или пароль.")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.websocket("/ws/{game}")
async def ws_game(ws: WebSocket, game: str, mode: str = "bot", size: int = 2):
    user = current_user(ws)
    if user is None or mode not in ("bot", "pvp") or size not in SIZES.get(game, ()):
        await ws.close(code=4401)
        return
    await handle_game(ws, user, game, mode, size)
