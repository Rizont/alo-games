const COLS = 9, ROWS = 7;
const boardEl = document.getElementById("c4board");
const legendEl = document.getElementById("legend");

const cells = [...Array(COLS * ROWS)].map((_, i) => {
  const b = document.createElement("button");
  b.className = "c4-cell";
  b.setAttribute("aria-label", `Колонка ${(i % COLS) + 1}`);
  b.addEventListener("click", () => game.send({ type: "drop", col: i % COLS }));
  boardEl.appendChild(b);
  return b;
});

function render(s) {
  const myTurn = s && !s.result && s.turn === s.you;
  cells.forEach((cell, i) => {
    const seat = s ? s.board[i] : -1;
    cell.dataset.seat = seat;
    cell.classList.toggle("win", !!(s && s.line.includes(i)));
    const colFull = s ? s.board[i % COLS] !== -1 : true;  // верхняя клетка колонки занята
    cell.disabled = !(myTurn && !colFull);
  });
  legendEl.innerHTML = "";
  if (!s) return "";
  s.names.forEach((name, seat) => {
    const li = document.createElement("li");
    li.dataset.seat = seat;
    if (!s.result && s.turn === seat) li.classList.add("turn");
    const gone = s.gone.includes(seat);
    li.textContent = name + (seat === s.you ? " (ты)" : "") + (gone ? " — вышел" : "");
    legendEl.appendChild(li);
  });
  return s.turn === s.you ? "Твой ход: выбери колонку." : `Ходит ${s.names[s.turn]}…`;
}

const game = createGame({ game: "connect4", render });
game.connect();
