import fs from 'node:fs';
import path from 'node:path';

export function assertPublicJson(directory, files) {
  for (const file of files) {
    const text = fs.readFileSync(path.join(directory, file), 'utf8');
    if (text.startsWith('version https://git-lfs.github.com/spec/v1') || /^(?:<<<<<<<|=======|>>>>>>>) /m.test(text)) {
      throw new Error(`Refusing to publish unresolved LFS or merge data: ${file}`);
    }
    const data = JSON.parse(text);
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
      throw new Error(`Refusing to publish an empty catalogue: ${file}`);
    }
  }
}

export function assertAtomicAssets(directory) {
  const html = fs.readFileSync(path.join(directory, 'index.html'), 'utf8');
  const references = [...html.matchAll(/(?:src|href)="([^\"]+\.(?:js|css))"/g)].map(match => match[1]);
  if (!references.length) throw new Error('Missing frontend entry assets');
  for (const reference of references) {
    if (!reference.startsWith('/assets/') || !fs.existsSync(path.join(directory, reference.slice(1)))) {
      throw new Error(`Frontend asset is outside the atomic deployment or missing: ${reference}`);
    }
  }
  for (const file of fs.readdirSync(path.join(directory, 'assets'))) {
    if (!/\.(?:js|css)$/.test(file)) continue;
    const text = fs.readFileSync(path.join(directory, 'assets', file), 'utf8');
    if (text.includes('https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/app/assets/')) {
      throw new Error(`Frontend chunk depends on a separately published asset: ${file}`);
    }
  }
}
