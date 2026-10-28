// Общая часть всех игр: подключение, выбор режима, статус, итог партии.
// Игра передаёт render(state) — он рисует поле и возвращает строку статуса.
function createGame({ game, render }) {
  const $ = (id) => document.getElementById(id);
  const statusEl = $("status"), deltaEl = $("delta"), againBtn = $("again");
  let ws = null, mode = "bot", size = 2, state = null;

  const activeSize = document.querySelector(".size.active");
  if (activeSize) size = Number(activeSize.dataset.size);

  function setStatus(text, showAgain = false) {
    statusEl.textContent = text;
    againBtn.hidden = !showAgain;
  }

  function finishText(s) {
    if (s.result === "abandoned") return s.reason;
    let text = "Ничья.";
    if (s.result === "win") text = s.winner === s.you ? "Победа!" : `Поражение. Победил: ${s.names[s.winner]}.`;
    return s.reason ? `${text} ${s.reason}.` : text;
  }

  function connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const sock = new WebSocket(`${proto}://${location.host}/ws/${game}?mode=${mode}&size=${size}`);
    if (ws) ws.close();
    ws = sock;
    state = null;
    deltaEl.hidden = true;
    render(null);
    setStatus("Подключаемся…");

    sock.onmessage = (e) => {
      if (sock !== ws) return;
      const msg = JSON.parse(e.data);
      if (msg.type === "waiting") {
        state = null;
        render(null);
        setStatus(`Ищем игроков: ${msg.have} из ${msg.need}. Для проверки открой сайт в другом браузере под другим аккаунтом.`);
      } else if (msg.type === "state") {
        state = msg;
        const text = render(msg);
        if (msg.result) {
          setStatus(finishText(msg), true);
          if (msg.delta !== null && msg.delta !== undefined) {
            deltaEl.textContent = `${msg.delta > 0 ? "+" : ""}${msg.delta} ALO`;
            deltaEl.hidden = false;
          }
        } else {
          setStatus(text);
        }
      }
    };
    sock.onclose = () => {
      if (sock === ws && !(state && state.result)) setStatus("Связь потеряна. Нажми «Сыграть ещё».", true);
    };
  }

  document.querySelectorAll(".mode").forEach((btn) =>
    btn.addEventListener("click", () => {
      mode = btn.dataset.mode;
      document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("active", b === btn));
      connect();
    })
  );
  document.querySelectorAll(".size").forEach((btn) =>
    btn.addEventListener("click", () => {
      size = Number(btn.dataset.size);
      document.querySelectorAll(".size").forEach((b) => b.classList.toggle("active", b === btn));
      connect();
    })
  );
  againBtn.addEventListener("click", connect);

  return { connect, send: (obj) => ws && ws.readyState === WebSocket.OPEN && ws.send(JSON.stringify(obj)) };
}
