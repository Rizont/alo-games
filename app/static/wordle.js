const LEN = 5, TRIES = 6;
const LAYOUT = ["йцукенгшщзхъ", "фывапролджэ", "ячсмитьбю"];
const gridEl = document.getElementById("wgrid");
const kbEl = document.getElementById("kb");
const oppEl = document.getElementById("wopp");
const oppGrid = document.getElementById("woppgrid");

let cur = "", shown = -1, state = null;

const tiles = [...Array(TRIES * LEN)].map((_, i) => {
  const t = document.createElement("div");
  t.className = "tile";
  t.style.setProperty("--i", i % LEN);
  gridEl.appendChild(t);
  return t;
});
const miniTiles = [...Array(TRIES * LEN)].map(() => {
  const t = document.createElement("i");
  t.className = "mini";
  oppGrid.appendChild(t);
  return t;
});

const keyEls = {};
function addKey(label, onClick, cls = "") {
  const b = document.createElement("button");
  b.className = "key " + cls;
  b.textContent = label;
  b.addEventListener("click", onClick);
  return b;
}
LAYOUT.forEach((letters, rowIdx) => {
  const row = document.createElement("div");
  row.className = "kb-row";
  if (rowIdx === 2) row.appendChild(addKey("Ввод", submit, "wide"));
  [...letters].forEach((ch) => {
    const b = addKey(ch, () => type(ch));
    keyEls[ch] = b;
    row.appendChild(b);
  });
  if (rowIdx === 2) row.appendChild(addKey("⌫", backspace, "wide"));
  kbEl.appendChild(row);
});

const active = () => state && !state.result && !state.failed;
function type(ch) { if (active() && cur.length < LEN) { cur += ch; draw(); } }
function backspace() { if (active()) { cur = cur.slice(0, -1); draw(); } }
function submit() {
  if (!active()) return;
  if (cur.length !== LEN) { game.toast("Нужно 5 букв"); return; }
  game.send({ type: "guess", word: cur });
}
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (e.key === "Enter") submit();
  else if (e.key === "Backspace") backspace();
  else if (/^[а-яё]$/i.test(e.key)) type(e.key.toLowerCase().replace("ё", "е"));
});

function draw() {
  const rows = state ? state.rows : [];
  tiles.forEach((tile, i) => {
    const r = Math.floor(i / LEN), c = i % LEN;
    let letter = "", cls = "tile";
    if (r < rows.length) {
      letter = rows[r].word[c];
      cls += " " + rows[r].fb[c];
      if (r >= shown && shown >= 0) cls += " flip";
    } else if (r === rows.length && active()) {
      letter = cur[c] || "";
      if (letter) cls += " typing";
    }
    tile.className = cls;
    tile.textContent = letter;
  });
  shown = state ? rows.length : -1;

  // цвета клавиш: лучшая из известных подсказок по букве
  const rank = { b: 1, y: 2, g: 3 }, best = {};
  rows.forEach(({ word, fb }) => [...word].forEach((ch, i) => {
    if (!best[ch] || rank[fb[i]] > rank[best[ch]]) best[ch] = fb[i];
  }));
  Object.entries(keyEls).forEach(([ch, el]) => (el.className = "key " + (best[ch] || "")));

  const duel = state && state.names.length === 2;
  oppEl.hidden = !duel;
  miniTiles.forEach((t, i) => {
    const r = Math.floor(i / LEN), c = i % LEN;
    t.className = "mini " + (duel && state.opp[r] ? state.opp[r][c] : "");
  });
}

function render(s) {
  if (!s) { cur = ""; state = null; shown = -1; draw(); return ""; }
  if (shown >= 0 && s.rows.length > shown) cur = "";  // слово принято сервером
  else if (shown < 0) cur = "";
  state = s;
  draw();
  if (s.failed && !s.result) return "Попытки закончились. Ждём соперника…";
  const duel = s.names.length === 2;
  return `Попытка ${Math.min(s.rows.length + 1, s.max)} из ${s.max}.` + (duel ? ` Соперник: ${s.opp.length} из ${s.max}.` : "");
}

const game = createGame({ game: "wordle", render });
game.connect();
