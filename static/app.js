const $ = id => document.getElementById(id);
let game = null, lo = 1, hi = 100, used = 0;

const post = (url, body) => fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)})
  .then(async r => ({ok:r.ok, data:await r.json()}));

function renderRange() {
  $("lo").textContent = lo; $("hi").textContent = hi;
  const span = game.high;
  $("fill").style.left = ((lo-1)/span*100) + "%";
  $("fill").style.width = Math.max(((hi-lo+1)/span*100), 2) + "%";
}
function renderDots() {
  $("dots").innerHTML = "";
  for (let i = 0; i < game.max; i++) {
    const d = document.createElement("i"); if (i < used) d.className = "used"; $("dots").appendChild(d);
  }
}
function setMsg(t, cls="") { $("msg").textContent = t; $("msg").className = "msg " + cls; }
function addLog(text, cls) { const li = document.createElement("li"); li.textContent = text; li.className = cls; $("log").appendChild(li); }

$("setup").addEventListener("submit", async e => {
  e.preventDefault();
  const level = document.querySelector("input[name=level]:checked").value;
  const {ok, data} = await post("/api/start", {player:$("player").value, difficulty:level});
  if (!ok) return;
  game = {id:data.game_id, high:data.high, max:data.max_attempts};
  lo = 1; hi = game.high; used = 0;
  $("log").innerHTML = ""; $("setup").hidden = true; $("play").hidden = false; $("again").hidden = true;
  $("guessForm").hidden = false;
  setMsg(`I'm thinking of a number from 1 to ${game.high}.`);
  renderRange(); renderDots(); $("guess").focus();
});

$("guessForm").addEventListener("submit", async e => {
  e.preventDefault();
  const value = Number($("guess").value);
  const {ok, data} = await post("/api/guess", {game_id:game.id, guess:value});
  if (!ok) return setMsg(data.error);
  used = data.attempts; renderDots(); $("guess").value = "";
  if (data.hint === "higher") { lo = Math.max(lo, value+1); addLog(value+" ↑", "up"); }
  if (data.hint === "lower")  { hi = Math.min(hi, value-1); addLog(value+" ↓", "down"); }
  renderRange();
  if (data.status === "won") { addLog(value+" ✓", "ok"); setMsg(`Correct! You got it in ${data.attempts} ${data.attempts===1?"try":"tries"}.`, "win"); finish(); }
  else if (data.status === "lost") { setMsg(`Out of tries. The number was ${data.secret}.`, "lose"); finish(); }
  else setMsg(`Go ${data.hint}. ${data.attempts_left} ${data.attempts_left===1?"try":"tries"} left.`);
  $("guess").focus();
});

function finish() { $("guessForm").hidden = true; $("again").hidden = false; loadBoard(); }
$("again").addEventListener("click", () => { $("play").hidden = true; $("setup").hidden = false; });

async function loadBoard() {
  const rows = await (await fetch("/api/leaderboard")).json();
  const st = await (await fetch("/api/stats")).json();
  $("stats").textContent = st.played ? `${st.won} won of ${st.played} games played` : "";
  $("scores").innerHTML = ""; $("noScores").hidden = rows.length > 0;
  rows.forEach(r => {
    const li = document.createElement("li");
    li.textContent = `${r.player} `;
    const s = document.createElement("small");
    s.textContent = `${r.attempts} ${r.attempts===1?"try":"tries"}, ${r.difficulty}`;
    li.appendChild(s); $("scores").appendChild(li);
  });
}
loadBoard();
