const canvas = document.querySelector("#scene");
const context = canvas.getContext("2d");
const status = document.querySelector("#runtime");

const { instance } = await WebAssembly.instantiateStreaming(fetch("/app.wasm"));
const advance = instance.exports.advance;
if (typeof advance !== "function") throw new Error("WebAssembly advance export is missing");

function render() {
  const frame = advance();
  const time = performance.now() / 1000;
  context.clearRect(0, 0, canvas.width, canvas.height);
  const gradient = context.createLinearGradient(0, 0, canvas.width, canvas.height);
  gradient.addColorStop(0, "#10233a");
  gradient.addColorStop(1, "#0B0F19");
  context.fillStyle = gradient;
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = "#00F0FF";
  context.lineWidth = 3;
  context.beginPath();
  context.arc(450 + Math.sin(time) * 230, 170, 48, 0, Math.PI * 2);
  context.stroke();
  context.fillStyle = "#edf7ff";
  context.font = "bold 27px Inter, sans-serif";
  context.fillText("Nexus live WebAssembly + Canvas", 34, 58);
  context.fillStyle = "#70f5ff";
  context.font = "20px monospace";
  context.fillText(`WASM frame: ${frame}`, 34, 104);
  status.textContent = `WebAssembly is executing · frame ${frame}`;
  document.title = `Nexus Live Canvas - frame ${frame}`;
  requestAnimationFrame(render);
}

render();
navigator.serviceWorker?.register("/sw.js").catch((error) => console.warn("PWA worker registration:", error));
