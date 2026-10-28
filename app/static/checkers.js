const N = 8;
const boardEl = document.getElementById("ckboard");
let state = null, selected = null, flipped = false;

const idx = (k) => (flipped ? N * N - 1 - k : k);  // у чёрных доска повёрнута, чтобы их шашки были снизу

const squares = [...Array(N * N)].map((_, k) => {
  const b = document.createElement("button");
  b.className = "sq";
  b.addEventListener("click", () => onClick(k));
  boardEl.appendChild(b);
  return b;
});

function onClick(k) {
  if (!state || state.result || state.turn !== state.you) return;
  const i = idx(k);
  if (state.moves[i]) {
    selected = selected === i ? null : i;
  } else if (selected !== null && state.moves[selected].includes(i)) {
    game.send({ type: "move", from: selected, to: i });
    selected = null;
  } else {
    selected = null;
  }
  draw();
}

function draw() {
  squares.forEach((sq, k) => {
    const i = idx(k);
    const dark = ((i >> 3) + (i & 7)) % 2 === 1;
    const piece = state ? state.board[i] : "";
    const dests = state && selected !== null && state.moves[selected] ? state.moves[selected] : [];
    let cls = "sq" + (dark ? " dark" : "");
    if (state && state.moves[i]) cls += " movable";
    if (selected === i) cls += " selected";
    if (dests.includes(i)) cls += " dest";
    if (state && state.last.includes(i)) cls += " last";
    sq.className = cls;
    sq.disabled = !dark;
    sq.innerHTML = piece
      ? `<span class="piece ${piece.toLowerCase()}">${piece === piece.toUpperCase() ? "♛" : ""}</span>`
      : "";
  });
}

function render(s) {
  state = s;
  flipped = !!s && s.you === 1;
  if (!s || selected === null || !s.moves[selected]) selected = null;
  draw();
  if (!s) return "";
  const mine = s.you === 0 ? "w" : "b";
  const count = (c) => s.board.filter((p) => p && p.toLowerCase() === c).length;
  const info = `Ты играешь ${s.you === 0 ? "белыми" : "чёрными"}. Шашек: у тебя ${count(mine)}, у соперника ${count(mine === "w" ? "b" : "w")}. `;
  if (s.turn !== s.you) return info + `Ходит ${s.names[1 - s.you]}…`;
  return info + (s.must_capture ? "Твой ход. Бить обязательно!" : "Твой ход.");
}

const game = createGame({ game: "checkers", render });
game.connect();
