import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

export default function phiagentPwa() {
  return {
    name:'phiagent-pwa', apply:'build', enforce:'post',
    generateBundle(_, bundle) {
      const read = name => readFileSync(new URL(name, import.meta.url));
      const manifest = read('manifest.webmanifest');
      const offline = read('offline.html');
      const worker = read('sw-template.js').toString();
      const version = createHash('sha256').update(Object.keys(bundle).sort().join('\n'))
        .update(manifest).update(offline).update(worker).update(read('icon-192.png'))
        .update(read('../src/assets/phiagent-icon.png')).digest('hex').slice(0,16);
      const files = {
        'manifest.webmanifest':manifest, 'offline.html':offline,
        'sw.js':worker.replaceAll('__PWA_VERSION__',version),
        'pwa/icon-192.png':read('icon-192.png'),
        'pwa/icon-512.png':read('../src/assets/phiagent-icon.png'),
      };
      for (const [fileName,source] of Object.entries(files)) this.emitFile({type:'asset',fileName,source});
    },
  };
}
