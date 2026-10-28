/* Real browser + real HTTP + temporary SQLite. Run from any directory. */
const {chromium} = require('playwright');
const {expect} = require('playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const {spawn} = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'evidence');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const records = [];
let server, browser, page, base, port, folder;
function pass(scenario, expected, actual) {
  records.push({scenario, expected, actual, status: 'PASS'});
  console.log(`PASS: ${scenario} — ${actual}`);
}
async function start() {
  server = spawn(process.env.PYTHON || 'python3', [path.join(root,'project/server.py'), '--port', String(port), '--database', path.join(folder,'tasks.sqlite3')], {stdio: ['ignore','pipe','pipe']});
  let logs = '';
  server.stderr.on('data', data => {logs += data;});
  for (let i=0; i<100; i++) {
    if(server.exitCode !== null) throw Error(`server exited: ${logs}`);
    try { if((await fetch(base+'/api/tasks')).ok) return; } catch {}
    await sleep(50);
  }
  throw Error('server readiness timeout: '+logs);
}
async function stop() {
  if(!server || server.exitCode !== null) return;
  const stopped = new Promise(resolve => server.once('exit', resolve));
  server.kill('SIGTERM'); await stopped;
}
async function tasks() { return (await page.request.get(base+'/api/tasks')).json(); }
async function open(title) {
  await page.getByRole('button',{name:`Изменить: ${title}`,exact:true}).click();
  await expect(page.locator('#editor')).toBeVisible();
  await expect(page.locator('#edit-title')).toBeFocused();
}
async function save() {
  await page.locator('#edit-save').click();
  await expect(page.locator('#editor')).not.toBeVisible();
  await page.waitForLoadState('networkidle');
}
(async()=>{
  fs.mkdirSync(output,{recursive:true}); folder=fs.mkdtempSync(path.join(os.tmpdir(),'practice5-e2e-'));
  const probe=net.createServer(); await new Promise(resolve=>probe.listen(0,'127.0.0.1',resolve)); port=probe.address().port;
  await new Promise(resolve=>probe.close(resolve)); base=`http://127.0.0.1:${port}`;
  await start();
  browser=await chromium.launch(process.env.PLAYWRIGHT_CHANNEL ? {channel:process.env.PLAYWRIGHT_CHANNEL} : {});
  const context=await browser.newContext({viewport:{width:1280,height:900},locale:'ru-RU',timezoneId:'Europe/Moscow'});
  await context.tracing.start({screenshots:true,snapshots:true});
  page=await context.newPage(); const errors=[]; page.on('pageerror',error=>errors.push(String(error)));
  await page.goto(base); await expect(page.getByText('Начнём с одной задачи')).toBeVisible();
  // Seed through visible UI, then complete with the old checkbox operation.
  await page.locator('#form [name=title]').fill('ДЗ5 исходная');
  await page.locator('#form [name=subject]').fill('AI');
  await page.locator('#form [name=deadline]').fill('2026-11-01');
  await page.getByRole('button',{name:'Добавить',exact:true}).click();
  await page.getByRole('checkbox',{name:'Выполнено: ДЗ5 исходная',exact:true}).check();
  await expect(page.locator('#done')).toHaveText('1');
  const id=(await tasks())[0].id;
  await open('ДЗ5 исходная');
  await expect(page.locator('#edit-subject')).toHaveValue('AI');
  await page.locator('#edit-title').fill('ДЗ5 исправленная');
  await page.locator('#edit-subject').fill('Инженерные инструменты');
  await page.locator('#edit-deadline').fill('2026-11-03');
  await page.screenshot({path:path.join(output,'demo-editor.png'),fullPage:true});
  await save();
  assert.deepEqual((await tasks())[0],{id,title:'ДЗ5 исправленная',subject:'Инженерные инструменты',deadline:'2026-11-03',done:1});
  await expect(page.getByRole('button',{name:'Изменить: ДЗ5 исправленная',exact:true})).toBeFocused();
  await page.screenshot({path:path.join(output,'demo-result.png'),fullPage:true});
  await page.setViewportSize({width:375,height:812});
  await page.screenshot({path:path.join(output,'demo-mobile.png'),fullPage:true});
  await open('ДЗ5 исправленная');
  await page.screenshot({path:path.join(output,'demo-mobile-editor.png'),fullPage:true});
  await page.keyboard.press('Escape'); await page.setViewportSize({width:1280,height:900});
  await page.reload(); await expect(page.getByText('ДЗ5 исправленная',{exact:true})).toBeVisible();
  await stop(); await start(); await page.reload();
  await expect(page.getByRole('checkbox',{name:'Выполнено: ДЗ5 исправленная',exact:true})).toBeChecked();
  pass('AC1 save/reload/server restart','three fields persist; id/done unchanged','real UI → PUT → SQLite → fresh process → UI agrees');
  // Cancellation by button and by Escape must not send a PUT.
  let puts=0; const counter=req=>{if(req.method()==='PUT') puts++;}; page.on('request',counter);
  await open('ДЗ5 исправленная'); await page.locator('#edit-title').fill('Не сохранять'); await page.locator('#edit-cancel').click();
  await open('ДЗ5 исправленная'); await page.locator('#edit-title').fill('Не сохранять Escape'); await page.keyboard.press('Escape');
  await expect(page.locator('#editor')).not.toBeVisible(); assert.equal(puts,0); page.off('request',counter);
  pass('AC3 cancellation','no PUT or database change','button + Escape sent zero PUTs');
  // Native dialog focus remains inside during keyboard traversal.
  await open('ДЗ5 исправленная');
  for(let i=0;i<8;i++){await page.keyboard.press('Tab'); assert(await page.evaluate(()=>document.querySelector('#editor').contains(document.activeElement)));}
  await page.locator('#edit-title').fill(' '); await page.locator('#edit-save').click();
  await expect(page.locator('#edit-error')).toBeVisible(); await expect(page.locator('#edit-title')).toHaveValue(' ');
  assert.equal((await tasks())[0].title,'ДЗ5 исправленная');
  pass('AC2 server validation in UI','400 retains draft and old data','blank title rejected visibly without write');
  await page.locator('#edit-title').fill('x'.repeat(161)); await page.locator('#edit-save').click();
  await expect(page.locator('#edit-error')).toContainText('160');
  // Boundary strings use Python code points, not UTF-16 maxlength.
  await page.locator('#edit-title').fill('😀'.repeat(160));
  await page.locator('#edit-subject').fill('Я'.repeat(80)); await page.locator('#edit-deadline').fill(''); await save();
  assert.equal(Array.from((await tasks())[0].title).length,160);
  await open('😀'.repeat(160)); await page.locator('#edit-title').fill('Очистка'); await page.locator('#edit-subject').fill('');
  await page.locator('#edit-title').press('Enter'); await expect(page.locator('#editor')).not.toBeVisible();
  await page.waitForLoadState('networkidle');
  const cleared=(await tasks())[0]; assert.equal(cleared.subject,'');assert.equal(cleared.deadline,'');
  pass('AC2 Unicode boundary and clear','160 code points / 80 subject accepted; empty values clear','emoji boundary persisted, optional fields cleared');
  // Network failure is deterministic fault injection; backend remains real.
  await open('Очистка'); await page.locator('#edit-title').fill('Черновик сети');
  await page.route('**/api/tasks/*',async route=>route.request().method()==='PUT'?route.abort('failed'):route.continue());
  await page.locator('#edit-save').click(); await expect(page.locator('#edit-error')).toContainText('Результат сохранения неизвестен');
  await expect(page.locator('#edit-title')).toHaveValue('Черновик сети');
  await page.unroute('**/api/tasks/*'); await page.locator('#edit-cancel').click();
  pass('AC3 network failure','draft retained and retry/cancel enabled','injected PUT abort; draft retained, cancel works');
  // Delayed response tests duplicate protection and blocked Escape while saving.
  await open('Очистка'); await page.locator('#edit-title').fill('После задержки');
  let release; const gate=new Promise(resolve=>{release=resolve;}); let delayed=0;
  await page.route('**/api/tasks/*',async route=>{
    if(route.request().method()!=='PUT') return route.continue();
    delayed++; await gate; await route.continue();
  });
  await page.locator('#edit-save').click(); await expect(page.locator('#edit-save')).toBeDisabled();
  await page.keyboard.press('Escape'); await expect(page.locator('#editor')).toBeVisible();
  await page.evaluate(()=>document.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true})));
  assert.equal(delayed,1); release(); await expect(page.locator('#editor')).not.toBeVisible(); await page.waitForLoadState('networkidle'); await page.unroute('**/api/tasks/*');
  pass('AC3 saving lock','one PUT; no close while pending','delayed PUT, blocked Escape and second submit');
  // PUT succeeds while GET fails: must never report a failed save.
  await open('После задержки'); await page.locator('#edit-title').fill('Сохранено без GET');
  await page.route('**/api/tasks',async route=>route.request().method()==='GET'?route.fulfill({status:503,contentType:'application/json',body:'{"error":"injected GET failure"}'}):route.continue());
  await save(); await expect(page.locator('#error')).toHaveText('Задача сохранена, но список не обновлён');
  await expect(page.getByText('Сохранено без GET',{exact:true})).toBeVisible();
  assert.equal((await (await fetch(base+'/api/tasks')).json())[0].title,'Сохранено без GET');
  await page.unroute('**/api/tasks');
  pass('AC3 PUT success + GET failure','saved data visible with distinct refresh warning','real PUT committed; injected GET 503; confirmed local data retained');
  // Filters/search survive an edit which removes the task from the visible subset.
  await page.getByRole('button',{name:'Готово',exact:true}).click(); await page.locator('#search').fill('Сохранено');
  await open('Сохранено без GET'); await page.locator('#edit-title').fill('Другое название'); await save();
  await expect(page.locator('#search')).toHaveValue('Сохранено');
  await expect(page.locator('[data-filter=done]')).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('#search')).toBeFocused();
  await expect(page.getByText('Здесь пока пусто')).toBeVisible();
  await page.locator('#search').fill('');
  pass('AC4 filter/search/focus','selection preserved; hidden row falls back to search','done filter and query unchanged, edited row disappeared with correct focus');
  // HTML-like text remains inert, controls still work.
  await open('Другое название'); const literal='<img src=x onerror="window.hacked=1">';
  await page.locator('#edit-title').fill(literal); await page.locator('#edit-subject').fill('AI'); await save();
  await expect(page.getByText(literal,{exact:true})).toBeVisible(); assert.equal(await page.evaluate(()=>window.hacked),undefined);
  assert.equal(await page.locator('#tasks img').count(),0);
  await page.getByRole('button',{name:'Все',exact:true}).click();
  await page.getByRole('checkbox',{name:`Выполнено: ${literal}`,exact:true}).uncheck(); await expect(page.locator('#open')).toHaveText('1');
  await page.getByRole('checkbox',{name:`Выполнено: ${literal}`,exact:true}).check(); await expect(page.locator('#done')).toHaveText('1');
  pass('AC4/AC5 old done and safe text','markup inert, PATCH done works both ways','no img/script execution; checkbox roundtrip persisted');
  // Mobile: list and editor have no horizontal overflow.
  await page.setViewportSize({width:375,height:812});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await open(literal); assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.keyboard.press('Escape');
  pass('AC5 keyboard/mobile','modal traps Tab, focus restored, width 375px fits','8 Tab transitions inside dialog, desktop+mobile screenshots saved');
  // Real 404 from a concurrent delete retains edit draft.
  await open(literal); await page.locator('#edit-title').fill('Черновик удалённой');
  assert.equal((await page.request.delete(base+`/api/tasks/${id}`)).status(),200);
  await page.locator('#edit-save').click(); await expect(page.locator('#edit-error')).toContainText('не найдена');
  await expect(page.locator('#edit-title')).toHaveValue('Черновик удалённой'); await page.locator('#edit-cancel').click(); await page.reload();
  await expect(page.getByText('Начнём с одной задачи')).toBeVisible();
  pass('AC3 missing task','real 404 retains draft, no recreation','concurrent DELETE then PUT returned 404; empty DB confirmed');
  // Existing delete confirmation remains available from visible UI.
  await page.locator('#form [name=title]').fill('Удалить через UI'); await page.getByRole('button',{name:'Добавить',exact:true}).click();
  page.once('dialog',dialog=>dialog.accept()); await page.getByRole('button',{name:'Удалить: Удалить через UI',exact:true}).click();
  await expect(page.getByText('Начнём с одной задачи')).toBeVisible();
  assert.deepEqual(await tasks(),[]); assert.deepEqual(errors,[]);
  pass('AC4 create/delete regression','UI create/delete work; no JS errors','confirmation accepted, empty temporary DB; zero page errors');
  await context.tracing.stop({path:path.join(output,'browser-trace.zip')});
})().catch(error=>{
  console.error(error); records.push({status:'FAIL',error:String(error),stack:error.stack});process.exitCode=1;
}).finally(async()=>{
  fs.writeFileSync(path.join(output,'browser-results.json'),JSON.stringify({command:'make e2e',browser:process.env.PLAYWRIGHT_CHANNEL||'chromium',temporaryDatabase:true,records},null,2)+'\n');
  if(browser) await browser.close(); await stop(); if(folder) fs.rmSync(folder,{recursive:true,force:true});
});
