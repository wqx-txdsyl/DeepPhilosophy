import test from 'node:test';
import assert from 'node:assert/strict';
import { formatBookTitle } from '../src/data/bookTitles.js';

test('title punctuation handles raw, wrapped and multiply wrapped catalog entries', () => {
  for (const title of ['汉谟拉比法典', '《汉谟拉比法典》', '《《汉谟拉比法典》》', ' 《 《汉谟拉比法典》 》 ']) {
    assert.equal(formatBookTitle(title), '《汉谟拉比法典》');
  }
});
test('commentary titles retain the original title with correctly nested marks', () => {
  assert.equal(formatBookTitle('《存在与时间》释义'), '《〈存在与时间〉释义》');
  assert.equal(formatBookTitle('《〈存在与时间〉释义》'), '《〈存在与时间〉释义》');
  assert.equal(formatBookTitle(''), '');
});
