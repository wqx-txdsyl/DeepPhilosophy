import assert from 'node:assert/strict';
import vm from 'node:vm';
import phiagentPwa from '../pwa/build-plugin.js';

const emitted = new Map();
phiagentPwa().generateBundle.call({emitFile:asset=>emitted.set(asset.fileName,asset.source)}, {}, {'assets/main-a.js':{}});
const manifest=JSON.parse(emitted.get('manifest.webmanifest').toString());
assert.equal(manifest.display,'standalone');assert.equal(manifest.scope,'/');assert.equal(manifest.start_url,'/agent');
for (const size of [192,512]) {
  const image=emitted.get(`pwa/icon-${size}.png`);
  assert.equal(image.readUInt32BE(16),size);assert.equal(image.readUInt32BE(20),size);
  assert.ok(manifest.icons.some(icon=>icon.sizes===`${size}x${size}`));
}
const script=emitted.get('sw.js');assert.ok(!script.includes('__PWA_VERSION__'));
const other=[];phiagentPwa().generateBundle.call({emitFile:asset=>other.push(asset)}, {}, {'assets/main-b.js':{}});
assert.notEqual(script,other.find(asset=>asset.fileName==='sw.js').source,'app code changes invalidate the worker cache');
const entries=new Map();const listeners=new Map();let online=true;let fetchCount=0;
const key=request=>typeof request==='string'?request:new URL(request.url).pathname;
const caches={
  async keys(){return [...entries.keys()];},async delete(name){return entries.delete(name);},
  async open(name){
    if(!entries.has(name))entries.set(name,new Map());const data=entries.get(name);
    return {async addAll(urls){for(const url of urls)data.set(url,new Response(url==='/offline.html'?'OFFLINE':'ICON'));},
      async match(request){return data.get(key(request))?.clone();},
      async put(request,response){data.set(key(request),response);}};
  },
  async match(request){for(const data of entries.values()){if(data.has(key(request)))return data.get(key(request)).clone();}}
};
let claimed=false;
vm.runInNewContext(script,{URL,Response,caches,self:{location:{origin:'https://phi.test'},
  addEventListener:(name,fn)=>listeners.set(name,fn),skipWaiting(){throw Error('Must not interrupt active pages');},
  clients:{async claim(){claimed=true;}}},fetch:async request=>{
    fetchCount++;if(!online)throw Error('offline');const path=new URL(request.url).pathname;
    return new Response(path.includes('html-fallback')?'PRIVATE HTML':path.includes('agent')?'PRIVATE ACCOUNT PAGE':'PUBLIC ASSET',
      {headers:{'content-type':path.includes('html-fallback')||path.includes('agent')?'text/html':'text/javascript'}});
  }});
let install;listeners.get('install')({waitUntil:promise=>install=promise});await install;
entries.set('phiagent-pwa-old',new Map());entries.set('unrelated-app',new Map());
let activate;listeners.get('activate')({waitUntil:promise=>activate=promise});await activate;
assert.ok(claimed && !entries.has('phiagent-pwa-old') && entries.has('unrelated-app'));
const request=(path,options={})=>({url:'https://phi.test'+path,method:'GET',headers:new Headers(),mode:'cors',...options});
async function dispatch(req){let result;listeners.get('fetch')({request:req,respondWith:promise=>result=promise});return result;}
for (const req of [request('/api/agent/stream_lg',{method:'POST'}),request('/api/agent/conversations'),
  request('/assets/private.js',{headers:new Headers({Authorization:'Bearer private'})}),request('/private/file'),
  request('/assets/code.js?token=private'),request('/assets/code.js',{url:'https://other.test/assets/code.js'})]) {
  assert.equal(await dispatch(req),undefined,'private, API and external traffic must bypass the worker');
}
const before=fetchCount;await dispatch(request('/assets/code-a.js'));online=false;
assert.equal(await (await dispatch(request('/assets/code-a.js'))).text(),'PUBLIC ASSET');assert.equal(fetchCount,before+1);
assert.equal(await (await dispatch(request('/agent/c/one',{mode:'navigate'}))).text(),'OFFLINE');
online=true;assert.equal(await (await dispatch(request('/agent',{mode:'navigate'}))).text(),'PRIVATE ACCOUNT PAGE');
await dispatch(request('/assets/html-fallback.js'));online=false;
await assert.rejects(dispatch(request('/assets/html-fallback.js')),/offline/,'HTML fallback cannot become a cached script');
assert.equal(await (await dispatch(request('/agent',{mode:'navigate'}))).text(),'OFFLINE','private navigation responses were not cached');

const browser=new EventTarget();browser.matchMedia=()=>({matches:false});
globalThis.window=browser;
Object.defineProperty(globalThis,'navigator',{configurable:true,value:{serviceWorker:{async register(url,options){
  assert.equal(url,'/api/pwa/worker');assert.equal(options.updateViaCache,'none');return {async update(){}};
}}}});
const pwa=await import('../src/utils/pwa.js');
const offer=new Event('beforeinstallprompt',{cancelable:true});browser.dispatchEvent(offer);
assert.equal(pwa.installPrompt(),offer);assert.ok(offer.defaultPrevented,'capture before component hydration');
assert.ok(await pwa.registerPwa());assert.equal(pwa.standaloneApp(),false);
browser.dispatchEvent(new Event('appinstalled'));assert.equal(pwa.installPrompt(),null);
console.log('PWA: install manifest, real icon dimensions, safe caching, offline fallback, non-interrupting updates and early install capture passed');
