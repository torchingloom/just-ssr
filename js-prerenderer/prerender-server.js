#!/usr/bin/env node
const prerender = require('./lib');
const server = prerender({
    chromeFlags: ['--no-sandbox', '--headless', '--disable-gpu', '--remote-debugging-port=9222', '--hide-scrollbars']
});
if (process.env.CACHE_MAXSIZE) {
    server.use(require('prerender-memory-cache'))
}
server.use(prerender.forwardHeaders()([
    'X-Prerender-Cache-Url',
    'X-Prerender-Cache-Key',
    'X-Prerender-Cache-Key-Sec'
]));
// server.use(prerender.removeScriptTags());
server.start();
