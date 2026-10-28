const LETTERS = "абвгдежзийклмнопрстуфхцчшщъыьэюя";
const wordEl = document.getElementById("word");
const abcEl = document.getElementById("abc");
const livesEl = document.getElementById("lives");
const hoppEl = document.getElementById("hopp");
const parts = [...document.querySelectorAll("[data-part]")];
let state = null;

const keys = {};
[...LETTERS].forEach((ch) => {
  const b = document.createElement("button");
  b.className = "key";
  b.textContent = ch;
  b.addEventListener("click", () => guess(ch));
  abcEl.appendChild(b);
  keys[ch] = b;
});

const active = () => state && !state.result && !state.failed;
function guess(ch) {
  if (active() && !state.guessed.includes(ch)) game.send({ type: "letter", letter: ch });
}
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (/^[а-яё]$/i.test(e.key)) guess(e.key.toLowerCase().replace("ё", "е"));
});

function render(s) {
  state = s;
  const wrong = s ? s.wrong : 0;
  parts.forEach((p) => p.classList.toggle("on", wrong >= Number(p.dataset.part)));
  wordEl.innerHTML = "";
  if (s) {
    s.masked.forEach((ch, i) => {
      const slot = document.createElement("span");
      slot.className = "slot";
      if (ch) slot.textContent = ch;
      else if (s.answer) { slot.textContent = s.answer[i]; slot.classList.add("missed"); }
      wordEl.appendChild(slot);
    });
  }
  Object.entries(keys).forEach(([ch, el]) => {
    const tried = s && s.guessed.includes(ch);
    const hit = tried && s.masked.includes(ch);
    el.className = "key" + (tried ? (hit ? " g" : " b") : "");
    el.disabled = !(s && !s.result && !s.failed) || tried;
  });
  livesEl.textContent = s ? `Ошибок: ${s.wrong} из ${s.lives}` : "";
  hoppEl.textContent = s && s.opp ? `Соперник: открыто ${s.opp.revealed} из ${s.opp.total}, ошибок ${s.opp.wrong} из ${s.lives}` : "";
  if (!s) return "";
  if (s.failed && !s.result) return "Ты повешен. Ждём, чем закончит соперник…";
  return "Назови букву.";
}

const game = createGame({ game: "hangman", render });
game.connect();
