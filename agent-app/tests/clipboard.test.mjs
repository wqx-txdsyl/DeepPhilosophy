import assert from 'node:assert/strict';
import { copyAnswerText } from '../src/utils/clipboard.js';
function documentFixture(success) {
  let removed=false, selected=false, restored=false, copiedValue;
  const node={style:{},setAttribute(){},focus(){},select(){selected=true},setSelectionRange(){},remove(){removed=true}};
  const doc={activeElement:{focus(){restored=true}},body:{appendChild(){}},createElement(){return node},execCommand(command){assert.equal(command,'copy');copiedValue=node.value;return success}};
  return {doc,check(){assert.ok(removed&&selected&&restored);assert.equal(copiedValue,'回答及出处链接')}};
}
let d=documentFixture(true);
assert.equal(await copyAnswerText('回答及出处链接',{nav:{},doc:d.doc}),true); d.check();
d=documentFixture(false); let written;
assert.equal(await copyAnswerText('回答及出处链接',{nav:{clipboard:{writeText:async s=>written=s}},doc:d.doc}),true);
assert.equal(written,'回答及出处链接'); d.check();
d=documentFixture(false);
assert.equal(await copyAnswerText('回答及出处链接',{nav:{clipboard:{writeText:async()=>{throw new Error('denied')}}},doc:d.doc}),false); d.check();
console.log('Clipboard: mobile selection copy, native fallback, denied permission and focus cleanup passed');
