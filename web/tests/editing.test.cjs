const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { buildSync } = require('esbuild');
const root = path.resolve(__dirname, '../..');

// Bundle the real TypeScript modules in memory using Vite's esbuild dependency.
const { text } = buildSync({
  stdin: { contents: 'export * from "./web/src/bind"; export * from "./web/src/drawing";', resolveDir: root },
  bundle: true, platform: 'node', format: 'cjs', write: false,
}).outputFiles[0];
const compiled = { exports: {} };
new Function('module', 'exports', text)(compiled, compiled.exports);
const { bindDrawing, instanceToDrawing, emptyDrawing } = compiled.exports;
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));

for (const key of ['easyasabc', 'fuzuli', 'skyscrapers', 'starbattle']) {
  test(`${key}: preserve sample parameters through drawing and resize`, () => {
    const spec = read(`impls/${key}.json`);
    const sample = read(`impls/samples/${key}.json`);
    const drawing = instanceToDrawing(sample, spec);
    const rebound = bindDrawing(drawing, spec);
    for (const [name, value] of Object.entries(sample.params)) assert.deepEqual(rebound.params[name], value);
    assert.equal(rebound.title, sample.title);
    const resized = bindDrawing({ ...drawing, rows: sample.rows + 1, cols: sample.cols + 1 }, spec);
    for (const name of ['k', 'stars']) if (name in sample.params) assert.equal(resized.params[name], sample.params[name]);
  });
}

test('switching puzzle does not leak instance parameters into another rule', () => {
  const drawing = instanceToDrawing(read('impls/samples/fuzuli.json'), read('impls/fuzuli.json'));
  assert.equal(bindDrawing(drawing, read('impls/easyasabc.json')).params.k, 3);
});
