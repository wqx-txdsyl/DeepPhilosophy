import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { assertAtomicAssets, assertPublicJson } from '../buildSafety.mjs';
function fixture(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'dp-build-safety-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  fs.mkdirSync(path.join(directory, 'assets'));
  return directory;
}
test('rejects the incident LFS conflict payload and malformed catalogue', t => {
  const directory = fixture(t);
  for (const text of ['version https://git-lfs.github.com/spec/v1\n<<<<<<< HEAD\noid sha256:123\n', '{"name":', '{}']) {
    fs.writeFileSync(path.join(directory, 'philosophers.json'), text);
    assert.throws(() => assertPublicJson(directory, ['philosophers.json']));
  }
  fs.writeFileSync(path.join(directory, 'philosophers.json'), '{"孔子":{"name":"孔子"}}');
  assert.doesNotThrow(() => assertPublicJson(directory, ['philosophers.json']));
});
test('rejects split-deployment entry and lazy CSS dependencies', t => {
  const directory = fixture(t);
  const cdn = 'https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/app/assets/';
  fs.writeFileSync(path.join(directory, 'index.html'), `<script src="${cdn}entry.js"></script>`);
  assert.throws(() => assertAtomicAssets(directory));
  fs.writeFileSync(path.join(directory, 'index.html'), '<script src="/assets/entry.js"></script>');
  assert.throws(() => assertAtomicAssets(directory));
  fs.writeFileSync(path.join(directory, 'assets/entry.js'), `const css="${cdn}route.css";`);
  assert.throws(() => assertAtomicAssets(directory));
  fs.writeFileSync(path.join(directory, 'assets/entry.js'), 'import("./route.js");');
  fs.writeFileSync(path.join(directory, 'assets/route.js'), 'export default 1;');
  assert.doesNotThrow(() => assertAtomicAssets(directory));
});
