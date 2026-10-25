// Keep HTML, entry modules, lazy chunks, CSS and fonts in one Pages deployment.
// Referencing new OSS hashes before their separate upload caused blank pages.
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { assertAtomicAssets, assertPublicJson } from './buildSafety.mjs';

const distDir = path.join(import.meta.dirname, 'dist');
assertPublicJson(distDir, ['books.json', 'philosophers.json', 'philosopher/catalog.json', 'schools/catalog.json']);
assertAtomicAssets(distDir);
let commitHash = 'master';
try {
  commitHash = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim() || 'master';
} catch {}
const htmlPath = path.join(distDir, 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');
for (const reference of ['/favicon.png', '/manifest.json']) {
  if (!html.includes(`"${reference}`)) throw new Error(`Missing public reference: ${reference}`);
}
fs.writeFileSync(htmlPath, html.replace('</head>', `  <meta name="dp-commit" content="${commitHash}" />\n</head>`));
console.log('[postbuild] Atomic frontend assets and complete public JSON verified');
