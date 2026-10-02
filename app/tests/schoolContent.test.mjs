import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseSchoolYear, normalizeSchool, schoolWorkTitles, buildSchoolReferences } from '../src/data/schoolContent.js';

const publicDir = fileURLToPath(new URL('../public/', import.meta.url));
const read = file => JSON.parse(fs.readFileSync(path.join(publicDir, file), 'utf8'));

test('date parsing preserves BCE, CE and ranges without treating unknown dates as ancient', () => {
  for (const [label, expected] of [['公元1905年',1905],['约公元前345—前285年',-345],['约前2600',-2600],['公元前5世纪',-500],['20世纪',1901],['公元1—3世纪',1],['-500',-500],['年代不详',null],['传统叙事中的族长时代',null]]) assert.equal(parseSchoolYear(label),expected,label);
});
test('legacy works and nested glossary retain content without executing input', () => {
  assert.deepEqual(schoolWorkTitles("['《逻辑研究》', '《观念》']"), ['《逻辑研究》','《观念》']);
  const data = normalizeSchool({ name:'例',thinkers:[{name:'甲',works:"['书']"}],cihai:[[{word:'词',def:'解释',source:'书'}]],timeline:[{year:'公元100年',event:'后'},{year:'前500年',event:'前'}]});
  assert.equal(data.cihai[0].def,'解释'); assert.deepEqual(data.thinkers[0].works,['书']); assert.equal(data.timeline[0].event,'前');
});
test('book matching never replaces a commentary with the original', () => {
  const refs = buildSchoolReferences({books:[{id:'original',title:'存在与时间',author:'海德格尔',chapterCount:13},{id:'commentary',title:'《存在与时间》释义',author:'张汝伦',chapterCount:21}]});
  assert.equal(refs.findBook('海德格尔《存在与时间》出版').id,'original');
  assert.equal(refs.findBook('《存在与时间》释义','张汝伦').id,'commentary');
  assert.equal(refs.findBook('《存在与时间》导读'),null);
  assert.equal(refs.findBook('存在与时间','张汝伦'),null);
});
test('person lookup rejects ambiguous surnames and contradictory historical identities', () => {
  const refs = buildSchoolReferences({philosophers:[{name:'大卫·休谟',era:'1711-1776'},{name:'盖伦',era:'129-216'},{name:'甲·米勒'},{name:'乙·米勒'}]});
  assert.equal(refs.findPerson('大卫'),null); assert.equal(refs.findPerson('米勒'),null); assert.equal(refs.findPerson('盖伦','1904-1976'),null); assert.equal(refs.findPerson('休谟').name,'大卫·休谟');
});
test('all published schools retain their image, route data, readable chapters and index entries', () => {
  const catalog = read('schools/catalog.json'), atlas = read('gene/atlas.json');
  assert.equal(catalog.schools.length,atlas.length);
  const files=fs.readdirSync(path.join(publicDir,'schools/data')).filter(file=>file.startsWith('school_')&&file.endsWith('.json'));
  assert.equal(catalog.schools.length,files.length);
  for (const entry of catalog.schools) {
    assert.ok(fs.existsSync(path.join(publicDir,entry.image)),entry.name+' image');
    const school=normalizeSchool(read('schools/data/'+entry.detailFile));
    assert.ok(school.overview&&school.conclusion,entry.name+' prose');
    for(const field of ['thinkers','timeline','cihai','quotes','works','subSchools']) assert.ok(school[field].length,entry.name+' '+field);
    for(const sub of school.subSchools) assert.ok(catalog.branches[sub.name]?.includes(entry.name),sub.name+' parent');
  }
});
