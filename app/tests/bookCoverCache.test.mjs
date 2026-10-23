import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { staticImageSources } from '../src/data/ossUrls.js';
import { BOOK_COVER_VERSIONS } from '../src/data/bookCoverVersions.js';

test('replacement cover hashes match the files actually being deployed', () => {
  for (const [path, version] of Object.entries(BOOK_COVER_VERSIONS)) {
    const bytes = readFileSync(new URL(`../public${path}`, import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0, 12), version);
  }
});

test('cached template URLs are refreshed on both CDN and same-origin fallback', () => {
  const path = '/covers/06906af574a4_cover.webp';
  const result = staticImageSources(path, 320);
  const primary = new URL(result.primary);
  const fallback = new URL(result.fallback, 'https://deepphilosophy.top');
  assert.equal(primary.pathname, path);
  assert.equal(primary.searchParams.get('v'), BOOK_COVER_VERSIONS[path]);
  assert.equal(fallback.searchParams.get('v'), BOOK_COVER_VERSIONS[path]);
  assert.equal(primary.searchParams.get('x-oss-process'), 'image/resize,w_320/format,webp/quality,q_82');
});

test('a newer explicitly versioned book record is preserved', () => {
  const result = staticImageSources('/covers/06906af574a4_cover.webp?v=newer-record', 320);
  assert.equal(new URL(result.primary).searchParams.get('v'), 'newer-record');
  assert.match(result.fallback, /\?v=newer-record$/);
});

test('unmodified covers and external image URLs retain their behavior', () => {
  const unmodified = staticImageSources('/covers/unchanged.webp', 320);
  assert.equal(new URL(unmodified.primary).searchParams.has('v'), false);
  assert.equal(unmodified.fallback, '/covers/unchanged.webp');
  assert.equal(staticImageSources('https://example.com/image.jpg').primary, 'https://example.com/image.jpg');
});
