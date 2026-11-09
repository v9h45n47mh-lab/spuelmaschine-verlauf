/* Run with `npm install --no-save linkedom` then `node tests/test_card.cjs`. */
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {parseHTML} = require('linkedom');
const {window} = parseHTML('<html><body></body></html>');
// linkedom does not implement the native details.open reflection.
if (!('open' in window.HTMLElement.prototype)) Object.defineProperty(window.HTMLElement.prototype,'open',{
  get(){return this.hasAttribute('open');},set(value){value?this.setAttribute('open',''):this.removeAttribute('open');}
});
vm.runInNewContext(readFileSync(path.join(__dirname,'../custom_components/spuelmaschine_verlauf/card.js'),'utf8'),
  {window,HTMLElement:window.HTMLElement,customElements:window.customElements,Intl,Date,Set,Number,JSON,String});
const Card=window.customElements.get('spuelmaschine-verlauf-card');
const card=new Card();
card.setConfig({title:'Spülmaschine'});
const hass={locale:{language:'de-DE',time_zone:'server'},config:{time_zone:'Europe/Berlin'},states:{
  'input_select.spuelmaschine_dienst':{state:'Paul'},
  'sensor.spulmaschine_verlauf':{state:'0',attributes:{offener_spuelgang:null,eintraege:[]}}
}};
card.hass=hass;
assert.match(card.shadowRoot.querySelector('ha-card').textContent,/Paul/);
assert.match(card.shadowRoot.querySelector('ha-card').textContent,/Noch keine Spülgänge gespeichert/);
assert.equal(card.shadowRoot.querySelector('.history').open,false);
card.shadowRoot.querySelector('.history').open=true;
const rows=[
 {id:'new',status:'offen',assigned_to:'Paul',finished_at:'2026-11-09T19:30:00Z'},
 {id:'parent',status:'nicht_bestaetigt',assigned_to:'Paul',emptied_by:'Vera/Manuel',finished_at:'2026-11-08T13:00:00Z',emptied_at:null,waiting_minutes:null},
 {id:'confirmed',status:'erledigt',assigned_to:'Maximilian',emptied_by:'Maximilian',finished_at:'2026-11-07T13:00:00Z',emptied_at:'2026-11-07T14:20:00Z',waiting_minutes:80},
 {id:'old',status:'nicht_bestaetigt',assigned_to:'Paul',finished_at:'2026-11-06T13:00:00Z',observed_after_restart:true}
];
hass.states['sensor.spulmaschine_verlauf']={state:'4',attributes:{offener_spuelgang:'new',eintraege:rows}};
card.hass=hass;
assert.equal(card.shadowRoot.querySelector('.history').open,true);
assert.match(card.shadowRoot.querySelector('.status').textContent,/Ausräumen offen/);
assert.match(card.shadowRoot.querySelector('ha-card').textContent,/20:30/); // UTC -> HA Europe/Berlin
assert.match(card.shadowRoot.querySelector('[data-cycle="parent"]').textContent,/Automatisch zugeordnet/);
assert.match(card.shadowRoot.querySelector('[data-cycle="confirmed"]').textContent,/1 Std. 20 Min./);
assert.match(card.shadowRoot.querySelector('[data-cycle="old"] .badge').textContent,/Unbestätigt/);
card.shadowRoot.querySelector('[data-cycle="parent"]').open=true;
hass.states['sensor.spulmaschine_verlauf'].state='5';
card.hass=hass;
assert.equal(card.shadowRoot.querySelector('[data-cycle="parent"]').open,true);
const unchanged=card.shadowRoot.querySelector('ha-card');
hass.states['light.unrelated']={state:'on'};
card.hass=hass;
assert.equal(card.shadowRoot.querySelector('ha-card'),unchanged);
hass.states['input_select.spuelmaschine_dienst'].state='<img src=x onerror=alert(1)>';
rows[0].assigned_to='<script>alert(1)</script>';
card.hass=hass;
assert.equal(card.shadowRoot.querySelectorAll('img,script').length,0);
assert.match(card.shadowRoot.querySelector('ha-card').textContent,/<img src=x/);
delete hass.states['sensor.spulmaschine_verlauf'];
card.hass=hass;
assert.match(card.shadowRoot.querySelector('.warning').textContent,/Verlaufssensor nicht verfügbar/);
assert.match(card.shadowRoot.querySelector('.status').textContent,/Nicht verfügbar/);
assert.throws(()=>card.setConfig({max_entries:0}),/max_entries/);
console.log('Frontend DOM checks passed: empty/open/unavailable states, timezone, fallback labels, durations, disclosure preservation, escaping and configuration.');
