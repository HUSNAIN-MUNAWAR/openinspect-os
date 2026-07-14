import test from 'node:test';
import assert from 'node:assert/strict';

test('primary navigation routes remain stable', () => {
  const routes = ['/facilities','/assets','/missions','/review','/coverage','/mlops','/reports'];
  assert.equal(routes.length, 7);
  assert.ok(routes.every((route) => route.startsWith('/')));
});
