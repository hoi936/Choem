import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('D:/CHO_EM/Cho_em_HanhTrinh/.tools/python/playwright/driver/package/index.js');

const ROOT_DIR = 'D:/CHO_EM/Cho_em_HanhTrinh';
const ARTIFACT_DIR = 'C:/Users/ADMIN/.gemini/antigravity/brain/0ebcdec5-7335-49af-b5f3-22936dc15f0d';

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.mp4': 'video/mp4',
};

function startStaticServer(rootDir) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const reqUrl = new URL(req.url, 'http://127.0.0.1');
      let relPath = decodeURIComponent(reqUrl.pathname);
      if (relPath === '/') relPath = '/index.html';
      const filePath = path.join(rootDir, relPath);

      if (!filePath.startsWith(path.resolve(rootDir))) {
        res.writeHead(403);
        res.end('Forbidden');
        return;
      }

      fs.stat(filePath, (err, stats) => {
        if (err || !stats.isFile()) {
          res.writeHead(404);
          res.end('Not found: ' + relPath);
          return;
        }
        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        fs.createReadStream(filePath).pipe(res);
      });
    });

    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ server, url: `http://127.0.0.1:${port}` });
    });
  });
}

async function runVerification() {
  const { server, url } = await startStaticServer(ROOT_DIR);
  const browser = await chromium.launch({ headless: true });

  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];

  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();

    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => {
      pageErrors.push(err.message);
    });
    page.on('requestfailed', (req) => {
      // Ignore canceled video range requests
      if (req.resourceType() === 'media') return;
      failedRequests.push(`${req.method()} ${req.url()} -> ${req.failure()?.errorText}`);
    });

    await page.goto(url, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(400);

    // 1. Capture Hero Desktop Screenshot
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'fe_verify_01_hero_desktop.png'),
      fullPage: false,
    });

    // 2. Check for Mathematical Alphanumeric Unicode, replacement chars, or generic captions in DOM
    const textAudit = await page.evaluate(() => {
      const bodyText = document.body.innerText || '';
      const hasMathUnicode = /[\u{1D400}-\u{1D7FF}]/u.test(bodyText);
      const hasReplacementChar = bodyText.includes('\uFFFD');
      const hasGenericMobileCaption = bodyText.includes('Tải lên từ di động');
      const overflowPx = document.documentElement.scrollWidth - window.innerWidth;
      return {
        hasMathUnicode,
        hasReplacementChar,
        hasGenericMobileCaption,
        overflowPx,
      };
    });

    // 3. Test Season Hub: Click Season 3 & Sub-tab "Bài đăng đã phân loại"
    await page.locator('#seasons-hub').scrollIntoViewIfNeeded();
    await page.locator('[data-season-idx="2"]').click();
    await page.waitForTimeout(250);
    await page.locator('[data-subtab="posts"]').click();
    await page.waitForTimeout(250);

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'fe_verify_02_season_explorer.png'),
      fullPage: false,
    });

    // Switch back to photos sub-tab on Season 7
    await page.locator('[data-season-idx="6"]').click();
    await page.waitForTimeout(200);
    await page.locator('[data-subtab="photos"]').click();
    await page.waitForTimeout(250);

    // 4. Test Impact Ledger & Timeline Year Filter
    await page.locator('.ledger-timeline-grid').scrollIntoViewIfNeeded();
    await page.locator('[data-year="2024"]').click();
    await page.waitForTimeout(200);
    const milestones2024 = await page.locator('#milestone-list .milestone-item').count();
    await page.locator('[data-year="all"]').click();
    await page.waitForTimeout(200);
    await page.locator('#milestone-list .milestone-item').nth(1).hover();
    await page.waitForTimeout(200);

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'fe_verify_03_impact_ledger.png'),
      fullPage: false,
    });

    // 5. Test Full Archive Search ("Tà Long") + Mode Switch + Lightbox Modal
    await page.locator('#full-archive').scrollIntoViewIfNeeded();
    await page.fill('#archive-search-input', 'Tà Long');
    await page.waitForTimeout(250);
    const taLongPhotoCount = await page.locator('#archive-results-grid .photo-card').count();

    // Open Lightbox on first matching photo
    await page.locator('#archive-results-grid .photo-card').first().click();
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'fe_verify_04_lightbox_modal.png'),
      fullPage: false,
    });

    const lightboxVisible = await page.locator('#lightbox-modal').isVisible();
    await page.locator('#lightbox-close').click();
    await page.waitForTimeout(200);

    // Reset search & check loaded images
    await page.locator('#archive-reset-all').click();
    await page.waitForTimeout(250);

    const imageAudit = await page.evaluate(async () => {
      const imgs = Array.from(document.querySelectorAll('img'));
      for (const img of imgs) {
        img.loading = 'eager';
        img.scrollIntoView({ behavior: 'instant', block: 'center' });
      }
      await new Promise((r) => setTimeout(r, 400));
      const broken = imgs
        .filter((img) => !img.complete || img.naturalWidth === 0)
        .map((img) => img.getAttribute('src'));
      return { totalVisibleImages: imgs.length, broken };
    });

    // 6. Test Mobile Viewport (390 x 844)
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);

    const mobileOverflowPx = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth
    );

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'fe_verify_05_mobile_390.png'),
      fullPage: false,
    });

    const report = {
      status:
        consoleErrors.length === 0 &&
        pageErrors.length === 0 &&
        failedRequests.length === 0 &&
        !textAudit.hasMathUnicode &&
        !textAudit.hasReplacementChar &&
        !textAudit.hasGenericMobileCaption &&
        textAudit.overflowPx <= 0 &&
        mobileOverflowPx <= 0 &&
        imageAudit.broken.length === 0
          ? 'PASS'
          : 'FAIL',
      consoleErrors,
      pageErrors,
      failedRequests,
      textAudit,
      milestones2024,
      taLongPhotoCount,
      lightboxVisible,
      imageAudit,
      mobileOverflowPx,
    };

    console.log(JSON.stringify(report, null, 2));
    if (report.status !== 'PASS') process.exitCode = 1;
  } finally {
    await browser.close();
    server.close();
  }
}

runVerification();
