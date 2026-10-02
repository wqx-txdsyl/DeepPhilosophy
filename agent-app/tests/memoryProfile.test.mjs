import assert from 'node:assert/strict';
import { memorySections, memoryDirty } from '../src/data/memoryProfile.js';
assert.deepEqual(memorySections('## 阅读与研究\n在读康德。\n\n比较休谟。\n\n## 交流偏好\n喜欢简洁。'),[
  {title:'阅读与研究',level:2,paragraphs:['在读康德。','比较休谟。']},
  {title:'交流偏好',level:2,paragraphs:['喜欢简洁。']},
]);
assert.deepEqual(memorySections('普通段落\n仍是同段'),[{title:'',level:2,paragraphs:['普通段落\n仍是同段']}]);
assert.deepEqual(memorySections(''),[]);
assert.equal(memorySections('<script>alert(1)</script>')[0].paragraphs[0],'<script>alert(1)</script>');
assert.equal(memoryDirty({text:'草稿',enabled:true},'草稿',true),false);
assert.equal(memoryDirty({text:'草稿',enabled:true},'',true),true);
assert.equal(memoryDirty({text:'草稿',enabled:true},'草稿',false),true);
console.log('Memory document parsing and draft checks passed');

assert.equal(memorySections('### 因果性\n独立的子主题')[0].level,3);
