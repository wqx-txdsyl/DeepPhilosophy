/** Keep relationship names clear of the docked card and each other. */
export function layoutHomeSkyLabels(layer, card, nodes, width, height, project) {
  const rect=card.getBoundingClientRect(),parent=layer.getBoundingClientRect();
  const occupied=[{x:rect.left-parent.left-12,y:rect.top-parent.top-12,w:rect.width+24,h:rect.height+24}];
  const overlap=(a,b)=>a.x<b.x+b.w+5&&a.x+a.w+5>b.x&&a.y<b.y+b.h+5&&a.y+a.h+5>b.y;
  const elements=layer.querySelectorAll('button');
  nodes.forEach((node,i)=>{
    const el=elements[i],[x,y]=project(node.fx,node.fy);
    if(!el)return;
    if(x<8||x>width-8||y<100||y>height-30){el.hidden=true;return;}
    el.hidden=false;const w=el.offsetWidth,h=el.offsetHeight;
    const candidates=[{x:x+10,y:y-h-7},{x:x-w-10,y:y-h-7},{x:x+10,y:y+8},{x:x-w-10,y:y+8},{x:x-w/2,y:y-h-18},{x:x-w/2,y:y+18}];
    for(let distance=40;distance<=100;distance+=20)for(let angle=0;angle<8;angle++)candidates.push({x:x+Math.cos(angle*Math.PI/4)*distance-w/2,y:y+Math.sin(angle*Math.PI/4)*distance-h/2});
    const spot=candidates.map(p=>({...p,w,h})).find(p=>p.x>=12&&p.x+w<=width-12&&p.y>=95&&p.y+h<=height-24&&!occupied.some(r=>overlap(p,r)));
    if(!spot){el.hidden=true;return;}
    el.style.left=spot.x+'px';el.style.top=spot.y+'px';occupied.push(spot);
  });
}
