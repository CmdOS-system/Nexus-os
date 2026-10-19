const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

async function main() {
  const url = process.env.NEXUS_PWA_URL;
  const screenshot = process.env.NEXUS_PWA_SCREENSHOT;
  if (!url || !screenshot) throw new Error("NEXUS_PWA_URL and NEXUS_PWA_SCREENSHOT are required");

  const browser = await chromium.launch({
    headless: false,
    args: [
      "--no-sandbox",
      "--disable-gpu",
      "--disable-software-rasterizer",
      "--disable-dev-shm-usage",
      "--password-store=basic",
      "--no-first-run",
      "--no-default-browser-check",
    ],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));
    await page.goto(url, { waitUntil: "load", timeout: 30_000 });
    await page.waitForFunction(() => {
      const title = document.title;
      const status = document.querySelector("#runtime")?.textContent ?? "";
      const match = title.match(/frame\s+(\d+)/i);
      return match && Number(match[1]) >= 10 && /WebAssembly is executing/.test(status);
    }, { timeout: 30_000 });

    const state = await page.evaluate(() => {
      const canvas = document.querySelector("canvas");
      const context = canvas?.getContext("2d");
      const pixel = context?.getImageData(0, 0, 1, 1).data ?? [];
      return {
        title: document.title,
        status: document.querySelector("#runtime")?.textContent ?? "",
        canvasWidth: canvas?.width ?? 0,
        pixel: Array.from(pixel),
      };
    });
    if (pageErrors.length) throw new Error(`PWA JavaScript errors: ${pageErrors.join("; ")}`);
    if (!state.canvasWidth || state.pixel[3] === 0) throw new Error("Canvas did not produce visible pixels");
    fs.mkdirSync(path.dirname(screenshot), { recursive: true });
    await page.screenshot({ path: screenshot });
    if (fs.statSync(screenshot).size < 4096) throw new Error("Chromium screenshot is unexpectedly small");
    console.log(`${state.title}; ${state.status}; captured ${screenshot}`);
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
