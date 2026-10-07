/** Every sampled text particle owns a separate destination and leaves a lasting star. */
export function startHomeSkyTransition({hero,canvas,sceneRef,birthStarsRef,onFinish}) {
  const W=hero.clientWidth,H=hero.clientHeight,dpr=Math.min(1.5,window.devicePixelRatio||1);
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const rand=Math.random;
  const smooth=(a,b,v)=>{const t=Math.min(1,Math.max(0,(v-a)/(b-a)));return t*t*(3-2*t)};
function uniqueStarDestinations(count){
const targets=[],buckets=new Map(),gap=3.1,key=(x,y)=>Math.floor(x/gap)+':'+Math.floor(y/gap);
const add=point=>{if(point.x<20||point.x>W-20||point.y<102||point.y>H-75)return false;const gx=Math.floor(point.x/gap),gy=Math.floor(point.y/gap);for(let x=gx-1;x<=gx+1;x++)for(let y=gy-1;y<=gy+1;y++)for(const q of buckets.get(x+':'+y)||[])if(Math.hypot(q.x-point.x,q.y-point.y)<gap)return false;targets.push(point);const k=key(point.x,point.y);if(!buckets.has(k))buckets.set(k,[]);buckets.get(k).push(point);return true};
for(const p of sceneRef.current?.getStars()||[])add({...p,existing:true});
let attempts=0;while(targets.length<count&&attempts<count*45){attempts++;const x=20+rand()*(W-40),y=102+rand()*(H-177);add({x,y,r:.34+Math.pow(rand(),3)*.48,a:.26+rand()*.35,rgb:rand()<.12?[226,214,192]:[217,224,231]})}
// A smaller preview may have no room for thousands of separate stars; sample its text less densely.
for(let i=targets.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[targets[i],targets[j]]=[targets[j],targets[i]]}return targets.slice(0,count);
}
const particleLayer=canvas.getContext('2d');
let ionizationRaf=0,ionizationToken=0;
function cancelIonization(){ionizationToken++;cancelAnimationFrame(ionizationRaf);hero.classList.remove('is-ionizing');particleLayer.clearRect(0,0,W,H)}
function ionize(){
if(reduced){onFinish?.();return}
cancelIonization();hero.classList.add('is-ionizing');
const token=ionizationToken,bounds=hero.getBoundingClientRect(),off=document.createElement('canvas');off.width=Math.ceil(W);off.height=Math.ceil(H);const oc=off.getContext('2d',{willReadFrequently:true});
const regions=[hero.querySelector('.home-hero-content')];
for(const region of regions){const walker=document.createTreeWalker(region,NodeFilter.SHOW_TEXT);let textNode;
while((textNode=walker.nextNode())){if(!textNode.textContent.trim())continue;const el=textNode.parentElement,cs=getComputedStyle(el);if(cs.display==='none'||cs.visibility==='hidden')continue;oc.font=[cs.fontStyle,cs.fontWeight,cs.fontSize,cs.fontFamily].join(' ');oc.textBaseline='alphabetic';oc.fillStyle=cs.color;const size=Number.parseFloat(cs.fontSize),range=document.createRange();
for(let i=0;i<textNode.length;i++){const ch=textNode.textContent[i];if(!ch.trim())continue;range.setStart(textNode,i);range.setEnd(textNode,i+1);const r=range.getBoundingClientRect();if(!r.width||!r.height)continue;const metrics=oc.measureText(ch),ascent=metrics.fontBoundingBoxAscent||size*.85,descent=metrics.fontBoundingBoxDescent||size*.22;const x=r.left-bounds.left,y=r.top-bounds.top+(r.height-ascent-descent)/2+ascent;oc.fillText(ch,x,y);}
range.detach();}}
const data=oc.getImageData(0,0,off.width,off.height).data,particles=[],cell=2.4;
const btn=hero.querySelector('.home-hero-cta'),br=btn.getBoundingClientRect(),bc=getComputedStyle(btn),button={x:br.left-bounds.left,y:br.top-bounds.top,w:br.width,h:br.height,color:bc.backgroundColor};
for(let y=0;y<off.height;y+=cell)for(let x=0;x<off.width;x+=cell){const px=Math.floor(x),py=Math.floor(y),i=(py*off.width+px)*4;if(data[i+3]<58)continue;
const scan=.11+Math.abs(x-W*.5)/W*.48+Math.max(0,(y-H*.22)/H)*.22+rand()*.22;
particles.push({x,y,delay:scan,r:.65+rand()*.5,alpha:data[i+3]/255,rgb:[data[i],data[i+1],data[i+2]],eraseX:px-1,eraseY:py-1,erased:false});}
// Thin only the moving particles; the intact letter layer is erased independently.
const moving=particles.length>6200?particles.filter(()=>rand()<6200/particles.length):particles;
const targets=uniqueStarDestinations(moving.length);if(targets.length<moving.length)moving.length=targets.length;
for(let i=0;i<moving.length;i++){const p=moving[i],target=targets[i],dx=target.x-p.x,dy=target.y-p.y,distance=Math.hypot(dx,dy),curl=(rand()-.5)*28;
p.destination=target;p.tx=target.x;p.ty=target.y;p.c1x=p.x+dx*.22-dy/(distance||1)*curl;p.c1y=p.y+dy*.22+dx/(distance||1)*curl;p.c2x=target.x-dx*.18;p.c2y=target.y-dy*.18;
p.duration=1.30+distance/Math.max(W,H)*.62+rand()*.3;p.settle=.35;p.endRGB=target.rgb;p.endRadius=target.r;p.endAlpha=target.a;p.arrived=false;}
canvas.width=Math.round(W*dpr);canvas.height=Math.round(H*dpr);canvas.style.width=W+'px';canvas.style.height=H+'px';particleLayer.setTransform(dpr,0,0,dpr,0,0);const at=performance.now();
const step=now=>{if(token!==ionizationToken)return;const t=(now-at)/1000;particleLayer.clearRect(0,0,W,H);
const buttonAlpha=1-smooth(.10,.54,t);if(buttonAlpha>0){particleLayer.globalAlpha=buttonAlpha;particleLayer.fillStyle=button.color;particleLayer.beginPath();particleLayer.roundRect(button.x,button.y,button.w,button.h,3);particleLayer.fill();particleLayer.globalAlpha=1;}
oc.globalCompositeOperation='destination-out';oc.fillStyle='#000';for(const p of particles){if(!p.erased&&t>=p.delay){oc.fillRect(p.eraseX,p.eraseY,cell+2,cell+2);p.erased=true}}oc.globalCompositeOperation='source-over';
particleLayer.globalAlpha=1-smooth(.54,.88,t);particleLayer.drawImage(off,0,0);particleLayer.globalAlpha=1;let alive=false;
for(const p of moving){const age=t-p.delay;if(age<0){alive=true;continue}const k=Math.min(1,age/p.duration),ease=k*k*(3-2*k),a=1-ease;if(k===1&&!p.arrived){p.arrived=true;const dest=p.destination;if(!dest.existing){const world=sceneRef.current?.toWorld(dest.x,dest.y)||[.5+(dest.x/W-.5)/2.6,.5+(dest.y/H-.5)/2.6];birthStarsRef.current.push({fx:world[0],fy:world[1],r:dest.r,a:dest.a,rgb:dest.rgb,zoom:sceneRef.current?.zoom()||2.6});dest.existing=true;}};
const x=a*a*a*p.x+3*a*a*ease*p.c1x+3*a*ease*ease*p.c2x+ease*ease*ease*p.tx,y=a*a*a*p.y+3*a*a*ease*p.c1y+3*a*ease*ease*p.c2y+ease*ease*ease*p.ty;
const tint=smooth(0,.38,age),rgb=p.rgb.map((v,j)=>Math.round(v+(p.endRGB[j]-v)*tint)),radius=p.r+(p.endRadius-p.r)*ease;
const landing=age>p.duration?smooth(0,p.settle,age-p.duration):0,alpha=(p.alpha*(1-ease)+p.endAlpha*ease)*(1-landing);
if(alpha>0.015){alive=true;particleLayer.fillStyle=`rgba(${rgb.join(',')},${alpha})`;particleLayer.beginPath();particleLayer.arc(x,y,radius,0,Math.PI*2);particleLayer.fill();}
}
if(alive)ionizationRaf=requestAnimationFrame(step);else{particleLayer.clearRect(0,0,W,H);hero.classList.remove('is-ionizing');sceneRef.current?.renderFrame();onFinish?.()}};
step(at);ionizationRaf=requestAnimationFrame(step);
}

ionize();return cancelIonization;
}
