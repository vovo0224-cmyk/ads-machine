const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function render() {
  const excalidrawFile = path.join(__dirname, 'blueprint.excalidraw');
  const outputFile = path.join(__dirname, 'blueprint.png');
  const data = JSON.parse(fs.readFileSync(excalidrawFile, 'utf8'));

  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  await page.goto('https://excalidraw.com', { waitUntil: 'networkidle2', timeout: 30000 });

  // Wait for app to load
  await page.waitForSelector('.excalidraw', { timeout: 15000 });

  // Load the scene data
  await page.evaluate((sceneData) => {
    const event = new CustomEvent('loadScene', { detail: sceneData });
    window.dispatchEvent(event);
  }, data);

  // Give it time to render
  await new Promise(r => setTimeout(r, 3000));

  // Use the Excalidraw export API
  const pngData = await page.evaluate(async (elements) => {
    // Try to use the app's export
    const app = document.querySelector('.excalidraw');
    if (!app) return null;

    // Fallback: screenshot the canvas
    return null;
  }, data.elements);

  // Screenshot approach
  await page.screenshot({ path: outputFile, fullPage: false });

  await browser.close();
  console.log('Saved to', outputFile);
}

render().catch(console.error);
