#!/usr/bin/env node
// Lightweight rendered UI probe for frontend-ux-review.
// Requires Playwright. Optional: pngjs enables pixel-sampled contrast.

import { mkdir, writeFile } from "node:fs/promises";
import { resolve, join } from "node:path";
import { createRequire } from "node:module";

const args = parseArgs(process.argv.slice(2));
if (!args._[0]) die("usage: rendered-probe.mjs <url> [--out DIR] [--viewports desktop=1440x900,mobile=390x844]");

const targetUrl = args._[0];
const outDir = resolve(args.out ?? "/tmp/frontend-ux-review");
const viewports = parseViewports(args.viewports ?? "desktop=1440x900,mobile=390x844");
const timeoutMs = Number(args.timeout ?? 30000);

const { chromium } = await loadPackage("playwright").catch((err) => {
  die(`Playwright is required and must be resolvable from this skill or the current working directory: ${err.message}`);
});

const pngjs = await loadPackage("pngjs").catch(() => null);
const PNG = pngjs?.PNG;

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const report = {
  schemaVersion: "1.0",
  target: targetUrl,
  generatedAt: new Date().toISOString(),
  pixelContrast: Boolean(PNG),
  viewports: [],
  findings: [],
};

try {
  for (const vp of viewports) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    try {
      await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: timeoutMs });
      await settle(page);

      const screenshotPath = join(outDir, `${vp.name}-${vp.width}x${vp.height}.png`);
      const pngBuffer = await page.screenshot({ path: screenshotPath, fullPage: true });
      const dom = await collectDomFacts(page);
      if (PNG) addPixelContrast(dom, pngBuffer, vp);

      const viewportReport = { ...vp, screenshotPath, ...dom };
      report.viewports.push(viewportReport);
      report.findings.push(...findViewportIssues(viewportReport));
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

const reportPath = join(outDir, "frontend-ux-report.json");
await writeFile(reportPath, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ reportPath, screenshots: report.viewports.map((v) => v.screenshotPath), findings: report.findings.length }, null, 2));

function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith("--")) out[key] = true;
      else out[key] = argv[++i];
    } else {
      out._.push(a);
    }
  }
  return out;
}

async function loadPackage(name) {
  try {
    return await import(name);
  } catch (directError) {
    try {
      const requireFromCwd = createRequire(join(process.cwd(), "package.json"));
      return requireFromCwd(name);
    } catch {
      throw directError;
    }
  }
}

function parseViewports(value) {
  return String(value)
    .split(",")
    .map((part) => {
      const [name, size] = part.split("=");
      const [width, height] = String(size ?? "").split("x").map(Number);
      if (!name || !width || !height) die(`invalid viewport: ${part}`);
      return { name, width, height };
    });
}

async function settle(page) {
  await page.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(500);
}

async function collectDomFacts(page) {
  return await page.evaluate(() => {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const doc = document.documentElement;

    const visible = (el) => {
      const cs = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return cs.display !== "none" && cs.visibility !== "hidden" && Number(cs.opacity) > 0.01 && rect.width > 0 && rect.height > 0;
    };

    const rectOf = (el) => {
      const r = el.getBoundingClientRect();
      return {
        x: Math.round(r.x + window.scrollX),
        y: Math.round(r.y + window.scrollY),
        width: Math.round(r.width),
        height: Math.round(r.height),
      };
    };

    const selectorOf = (el) => {
      if (el.id) return `#${CSS.escape(el.id)}`;
      const test = (attr) => el.getAttribute(attr);
      for (const attr of ["data-testid", "data-test", "name", "aria-label"]) {
        const value = test(attr);
        if (value) return `${el.tagName.toLowerCase()}[${attr}="${CSS.escape(value)}"]`;
      }
      const cls = [...el.classList].slice(0, 2).map((c) => `.${CSS.escape(c)}`).join("");
      return `${el.tagName.toLowerCase()}${cls}`;
    };

    const directText = (el) =>
      [...el.childNodes]
        .filter((n) => n.nodeType === Node.TEXT_NODE)
        .map((n) => n.textContent.trim())
        .filter(Boolean)
        .join(" ")
        .replace(/\s+/g, " ");

    const accessibleName = (el) => {
      const aria = el.getAttribute("aria-label");
      if (aria?.trim()) return aria.trim();
      const labelledBy = el.getAttribute("aria-labelledby");
      if (labelledBy) {
        const label = labelledBy
          .split(/\s+/)
          .map((id) => document.getElementById(id)?.innerText?.trim())
          .filter(Boolean)
          .join(" ");
        if (label) return label;
      }
      if (el.id) {
        const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.innerText?.trim();
        if (label) return label;
      }
      return (el.innerText || el.getAttribute("title") || el.getAttribute("placeholder") || "").trim();
    };

    const textElements = [];
    for (const el of document.querySelectorAll("body *")) {
      if (!visible(el)) continue;
      const text = directText(el);
      if (!text) continue;
      const cs = getComputedStyle(el);
      const rect = rectOf(el);
      textElements.push({
        selector: selectorOf(el),
        text: text.slice(0, 100),
        rect,
        fontSize: Number.parseFloat(cs.fontSize),
        fontWeight: Number.parseInt(cs.fontWeight, 10) || 400,
        color: cs.color,
        backgroundColor: cs.backgroundColor,
        overflowX: el.scrollWidth > el.clientWidth + 1,
        overflowY: el.scrollHeight > el.clientHeight + 1,
      });
    }

    const controls = [];
    for (const el of document.querySelectorAll('a[href],button,input,select,textarea,[role="button"],[role="link"],[tabindex]:not([tabindex="-1"])')) {
      if (!visible(el)) continue;
      const cs = getComputedStyle(el);
      const rect = rectOf(el);
      controls.push({
        selector: selectorOf(el),
        tag: el.tagName.toLowerCase(),
        role: el.getAttribute("role") || "",
        type: el.getAttribute("type") || "",
        name: accessibleName(el).slice(0, 120),
        rect,
        disabled: Boolean(el.disabled) || el.getAttribute("aria-disabled") === "true",
        cursor: cs.cursor,
      });
    }

    const headings = [...document.querySelectorAll("h1,h2,h3")]
      .filter(visible)
      .map((el) => ({ tag: el.tagName.toLowerCase(), text: el.innerText.trim().slice(0, 160), rect: rectOf(el) }));

    return {
      url: location.href,
      title: document.title,
      viewport: { width: vw, height: vh },
      document: {
        width: doc.scrollWidth,
        height: doc.scrollHeight,
        horizontalOverflow: doc.scrollWidth > vw + 1,
      },
      headings,
      textElements,
      controls,
    };
  });
}

function addPixelContrast(dom, pngBuffer, viewport) {
  const png = PNG.sync.read(pngBuffer);
  for (const el of dom.textElements) {
    const fg = parseRgb(el.color);
    const bg = sampleRingMedian(png, el.rect);
    if (!fg || !bg) continue;
    const ratio = contrastRatio(fg, bg);
    const large = el.fontSize >= 24 || (el.fontSize >= 19 && el.fontWeight >= 700);
    el.pixelBackground = `rgb(${bg[0]}, ${bg[1]}, ${bg[2]})`;
    el.contrastRatio = Number(ratio.toFixed(2));
    el.wcagAA = large ? ratio >= 3 : ratio >= 4.5;
    el.viewportName = viewport.name;
  }
}

function sampleRingMedian(png, rect) {
  const xs = [];
  const ys = [];
  const x0 = Math.max(0, rect.x - 3);
  const y0 = Math.max(0, rect.y - 3);
  const x1 = Math.min(png.width - 1, rect.x + rect.width + 3);
  const y1 = Math.min(png.height - 1, rect.y + rect.height + 3);
  for (let x = x0; x <= x1; x += Math.max(1, Math.floor((x1 - x0) / 12))) {
    xs.push([x, y0], [x, y1]);
  }
  for (let y = y0; y <= y1; y += Math.max(1, Math.floor((y1 - y0) / 12))) {
    ys.push([x0, y], [x1, y]);
  }
  const samples = [...xs, ...ys].map(([x, y]) => pixelAt(png, x, y)).filter(Boolean);
  if (!samples.length) return null;
  return [median(samples.map((p) => p[0])), median(samples.map((p) => p[1])), median(samples.map((p) => p[2]))];
}

function pixelAt(png, x, y) {
  if (x < 0 || y < 0 || x >= png.width || y >= png.height) return null;
  const i = (Math.floor(y) * png.width + Math.floor(x)) * 4;
  return [png.data[i], png.data[i + 1], png.data[i + 2]];
}

function findViewportIssues(vp) {
  const findings = [];
  const push = (category, severity, message, extra = {}) => findings.push({ viewport: vp.name, category, severity, message, ...extra });

  if (vp.document.horizontalOverflow) {
    push("layout.overflow", "high", `Document width ${vp.document.width}px exceeds viewport ${vp.width}px.`, { evidence: vp.screenshotPath });
  }

  for (const el of vp.textElements) {
    if (el.overflowX || el.overflowY) {
      push("layout.clipping", "medium", `Text may be clipped in ${el.selector}: "${el.text}"`, { selector: el.selector, rect: el.rect });
    }
    if (typeof el.contrastRatio === "number" && !el.wcagAA) {
      push("readability.contrast", "medium", `Text contrast ${el.contrastRatio}:1 fails WCAG AA in ${el.selector}: "${el.text}"`, { selector: el.selector, rect: el.rect });
    }
  }

  for (const control of vp.controls) {
    if (!control.name && ["button", "a", "input", "select", "textarea"].includes(control.tag)) {
      push("a11y.accessible-name", "medium", `Interactive control has no accessible name: ${control.selector}`, { selector: control.selector, rect: control.rect });
    }
    if ((control.rect.width < 32 || control.rect.height < 32) && !control.disabled) {
      push("a11y.target-size", "low", `Small interactive target ${control.rect.width}x${control.rect.height}: ${control.selector}`, { selector: control.selector, rect: control.rect });
    }
  }

  if (vp.headings.length === 0) {
    push("hierarchy.visual-priority", "low", "No visible h1/h2/h3 headings detected.");
  }

  return findings;
}

function parseRgb(value) {
  const m = String(value).match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const [r, g, b] = m[1].split(",").slice(0, 3).map((n) => Number.parseFloat(n.trim()));
  return [r, g, b].every((n) => Number.isFinite(n)) ? [r, g, b] : null;
}

function contrastRatio(a, b) {
  const l1 = relLum(a);
  const l2 = relLum(b);
  const hi = Math.max(l1, l2);
  const lo = Math.min(l1, l2);
  return (hi + 0.05) / (lo + 0.05);
}

function relLum(rgb) {
  const [r, g, b] = rgb.map((c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function die(message) {
  console.error(message);
  process.exit(1);
}
