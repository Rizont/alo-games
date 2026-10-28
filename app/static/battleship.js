const N = 10;
const CLASS = { S: "ship", H: "hit", M: "miss", K: "sunk" };
const SIGN = { H: "✕", K: "✕", M: "•" };
const mineEl = document.getElementById("mine");
const theirsEl = document.getElementById("theirs");
const setupEl = document.getElementById("setup");

function buildGrid(el, clickable) {
  return [...Array(N * N)].map((_, i) => {
    const c = document.createElement(clickable ? "button" : "div");
    c.className = "bs-cell";
    if (clickable) c.addEventListener("click", () => game.send({ type: "fire", cell: i }));
    el.appendChild(c);
    return c;
  });
}
const mine = buildGrid(mineEl, false);
const theirs = buildGrid(theirsEl, true);

function paint(cells, values, canFire) {
  cells.forEach((c, i) => {
    const v = values ? values[i] : "";
    c.className = "bs-cell " + (CLASS[v] || "");
    c.textContent = SIGN[v] || "";
    if (c.tagName === "BUTTON") c.disabled = !(canFire && !v);
  });
}

document.getElementById("shuffle").addEventListener("click", () => game.send({ type: "shuffle" }));
document.getElementById("ready").addEventListener("click", () => game.send({ type: "ready" }));

function render(s) {
  paint(mine, s && s.mine, false);
  const battle = s && s.phase === "battle" && !s.result;
  paint(theirs, s && s.enemy, battle && s.turn === s.you);
  setupEl.hidden = !(s && s.phase === "setup" && !s.result && !s.ready[s.you]);
  if (!s) return "";
  if (s.phase === "setup") {
    return s.ready[s.you]
      ? "Флот готов. Ждём, когда соперник расставит корабли…"
      : "Расставь корабли: перемешивай, пока не понравится, и жми «Готов».";
  }
  const count = `Кораблей: у тебя ${s.left_me}, у соперника ${s.left_opp}. `;
  return count + (s.turn === s.you ? "Твой ход — стреляй по правому полю." : `Стреляет ${s.names[1 - s.you]}…`);
}

const game = createGame({ game: "battleship", render });
game.connect();
