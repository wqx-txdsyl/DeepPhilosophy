import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { SCHOOL_ARTWORK_VERSIONS } from '../src/data/schoolArtworkVersions.js';
import { OSS_BASE, ossImg, ossFallback, staticImageSources } from '../src/data/ossUrls.js';

test('replacement versions match the actual image bytes', () => {
  assert.ok(Object.keys(SCHOOL_ARTWORK_VERSIONS).length > 0);
  for (const [path, version] of Object.entries(SCHOOL_ARTWORK_VERSIONS)) {
    const bytes = readFileSync(new URL(`../public${path}`, import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0, 12), version);
  }
});

test('resized replacement images and same-origin fallback retain their version', () => {
  const [path, version] = Object.entries(SCHOOL_ARTWORK_VERSIONS)[0];
  const primary = ossImg(path, { w: 380 });
  const url = new URL(primary);
  assert.equal(url.searchParams.get('v'), version);
  assert.equal(url.searchParams.get('x-oss-process'), 'image/resize,w_380');
  const element = { src: primary, dataset: {} };
  ossFallback({ currentTarget: element });
  const fallback = new URL(element.src, 'https://deepphilosophy.top');
  assert.equal(decodeURIComponent(fallback.pathname), path);
  assert.equal(fallback.searchParams.get('v'), version);
  assert.equal(fallback.searchParams.has('x-oss-process'), false);
  const once = element.src;
  ossFallback({ currentTarget: element });
  assert.equal(element.src, once);
  const resized = staticImageSources(path, 192);
  assert.equal(new URL(resized.primary).searchParams.get('x-oss-process'), 'image/resize,w_192/format,webp/quality,q_82');
  assert.equal(new URL(resized.fallback, 'https://deepphilosophy.top').searchParams.get('v'), version);
});

test('unmodified images and JSON keep their existing cache and resize URLs', () => {
  assert.equal(ossImg('/schools/儒家.webp', { w: 380 }), `${OSS_BASE}/schools/儒家.webp?x-oss-process=image/resize,w_380`);
  assert.equal(ossImg('/gene/atlas.json'), `${OSS_BASE}/gene/atlas.json`);
  assert.equal(staticImageSources('/philosopher/example.webp', 192).fallback, '/philosopher/example.webp');
});
