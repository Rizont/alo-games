const MARKS = ["X", "O"];
const ICONS = {
  X: '<svg viewBox="0 0 100 100" class="mark x"><path pathLength="1" d="M22 22 L78 78 M78 22 L22 78"/></svg>',
  O: '<svg viewBox="0 0 100 100" class="mark o"><circle pathLength="1" cx="50" cy="50" r="30"/></svg>',
};
const boardEl = document.getElementById("board");

const cells = [...Array(9)].map((_, i) => {
  const b = document.createElement("button");
  b.className = "cell";
  b.setAttribute("aria-label", `Клетка ${i + 1}`);
  b.addEventListener("click", () => game.send({ type: "move", cell: i }));
  boardEl.appendChild(b);
  return b;
});

function render(s) {
  cells.forEach((cell, i) => {
    const mark = s ? s.board[i] : "";
    if (cell.dataset.mark !== mark) {  // перерисовываем только изменившиеся клетки
      cell.dataset.mark = mark;
      cell.innerHTML = mark ? ICONS[mark] : "";
    }
    const myTurn = s && !s.result && s.turn === s.you;
    cell.disabled = !(myTurn && !mark);
    cell.classList.toggle("win", !!(s && s.line.includes(i)));
  });
  if (!s) return "";
  return `Вы — ${MARKS[s.you]}, соперник: ${s.names[1 - s.you]}. ` + (s.turn === s.you ? "Ваш ход." : "Ход соперника…");
}

const game = createGame({ game: "tictactoe", render });
game.connect();
