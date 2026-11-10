import {UI_CSS, UI_VERSION, navigation, section, row, notice, versionInfo, escapeHtml, bindUI, statisticsTable, counter} from './family-ui/1.2.0/family-ui.js';
/* Spülmaschine Verlauf 0.4.2 — local, read-only dashboard card. */
const SV_VERSION = '0.4.2';
const svEscape=escapeHtml;
const svDate = (value, hass, date = true) => {
  if (!value) return '—';
  const parsed = new Date(value);
  if (!Number.isFinite(parsed.getTime())) return '—';
  const options = {hour:'2-digit', minute:'2-digit'};
  if (date) Object.assign(options, {day:'2-digit', month:'2-digit', year:'2-digit'});
  const zone = hass?.locale?.time_zone === 'local' ? undefined : hass?.config?.time_zone;
  if (zone) options.timeZone = zone;
  try { return new Intl.DateTimeFormat(hass?.locale?.language || hass?.language || 'de-DE', options).format(parsed); }
  catch { return parsed.toLocaleString('de-DE'); }
};
const svDuration = value => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
  const minutes = Math.max(0, Math.round(Number(value)));
  return minutes >= 60 ? `${Math.floor(minutes/60)} Std. ${minutes%60} Min.` : `${minutes} Min.`;
};
const svZone = hass => hass?.locale?.time_zone === 'local' ? undefined : hass?.config?.time_zone;
const svMonth = (value, hass) => {
  const date = new Date(value);
  if (!value || !Number.isFinite(date.getTime())) return 'unknown';
  const parts = new Intl.DateTimeFormat('en-CA', {year:'numeric',month:'2-digit',timeZone:svZone(hass)}).formatToParts(date);
  return `${parts.find(p=>p.type==='year').value}-${parts.find(p=>p.type==='month').value}`;
};
const svMonthTitle = key => /^\d{4}-\d{2}$/.test(key)
  ? new Intl.DateTimeFormat('de-DE',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(`${key}-01T12:00:00Z`)) : 'Monat unbekannt';
// Only domain-specific statistics layout; shared controls use UI_CSS.

class SpuelmaschineVerlaufCard extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this._signature='';this._settings=false;this._folds=new Map();this._bindUI();}
  _bindUI(){this._unbindUI ||= bindUI(this.shadowRoot,({action,data})=>{if(action==='navigate'&&(data.page!=='settings'||this._canSettings())){this._rememberFolds();this._settings=data.page==='settings';this._signature='';this._render();}});}
  connectedCallback(){this._bindUI();}
  disconnectedCallback(){this._unbindUI?.();this._unbindUI=null;}
  setConfig(config) {
    this._config = {entity:'sensor.spulmaschine_verlauf', duty_entity:'input_select.spuelmaschine_dienst', title:'Spülmaschine', history_open:false, max_entries:30, ...config};
    if (!Number.isInteger(this._config.max_entries) || this._config.max_entries < 1 || this._config.max_entries > 30)
      throw new Error('max_entries muss eine ganze Zahl zwischen 1 und 30 sein.');
    if (this._config.settings_users !== undefined && (!Array.isArray(this._config.settings_users) || this._config.settings_users.some(id=>typeof id !== 'string' || !id.trim())))
      throw new Error('settings_users muss eine Liste von Home-Assistant-Benutzer-IDs sein.');
    this._signature = ''; this._render();
  }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 4; }
  static getStubConfig() { return {entity:'sensor.spulmaschine_verlauf',duty_entity:'input_select.spuelmaschine_dienst'}; }
  _entry(entry) {
    const person = ['Vera', 'Manuel', 'Vera/Manuel', 'Vera & Manuel', 'Vera / Manuel'].includes(entry.emptied_by) ? 'Vera / Manuel' : entry.emptied_by;
    const time = entry.emptied_at ? svDate(entry.emptied_at,this._hass) : 'Zeitpunkt unbekannt';
    return row({title:person,trailing:`<small class="entry-sub">${svEscape(time)}</small>`}).replace('class="setting-row"',`class="setting-row history-row" data-cycle="${svEscape(entry.id)}"`).replace('<strong>','<strong class="entry-title">');
  }
  _canSettings() {
    const user = this._hass?.user;
    if (!user) return false;
    // Explicit HA account IDs take precedence. Admin status alone grants no access.
    if (Array.isArray(this._config.settings_users)) return this._config.settings_users.includes(user.id);
    const firstName = String(user.name || '').trim().split(/\s+/)[0].toLocaleLowerCase('de-DE');
    return ['vera', 'manuel'].includes(firstName);
  }
  _rememberFolds(){this.shadowRoot.querySelectorAll('[data-fold]').forEach(el=>{const fold=el.querySelector('.settings-fold');if(fold)this._folds.set(el.dataset.fold,fold.getAttribute('aria-expanded')==='true');});}
  _history(visible,unavailable){
    const groups=new Map();visible.forEach(entry=>{const month=svMonth(entry.emptied_at||entry.finished_at,this._hass);if(!groups.has(month))groups.set(month,[]);groups.get(month).push(entry);});
    const months=[...groups.keys()].sort().reverse();
    const content=unavailable?notice('Der Verlauf kann derzeit nicht angezeigt werden.'):months.length?months.map(key=>`<div class="month fui-history-month" data-fold="${svEscape(key)}">${section({id:'month-'+key,title:svMonthTitle(key),expanded:this._folds.get(key)||false,trailing:`<small>${groups.get(key).length}</small>`,content:groups.get(key).map(entry=>this._entry(entry)).join('')})}</div>`).join(''):notice('Noch kein Ausräumen gespeichert.');
    return `<div class="history" data-fold="history">${section({id:'history',title:'Verlauf',expanded:this._folds.get('history')??this._config.history_open,trailing:`<small>${unavailable?'—':visible.length} Einträge</small>`,content})}</div>`;
  }
  _statistics(stats, unavailable) {
    const total = {count:0,assumed:0,people:{'Maximilian':0,'Paul':0,'Vera / Manuel':0}};
    if (Array.isArray(stats)) stats.forEach(month=>{
      total.count += Number(month.total) || 0;
      total.assumed += Number(month.assumed) || 0;
      Object.keys(total.people).forEach(person=>{total.people[person] += Number(month.people?.[person]) || 0;});
    });
    const content=unavailable?notice('Statistik nicht verfügbar.'):!Array.isArray(stats)?notice('Statistik noch nicht verfügbar. Integration aktualisieren und Home Assistant neu starten.'):`<p class="hint">Gesamter gespeicherter Zeitraum</p>${statisticsTable({label:'Gesamtstatistik',columns:[{label:'Benutzer'},{label:'Anzahl',align:'right'}],rows:Object.keys(total.people).map(person=>[person,total.people[person]]),totals:['Gesamt',total.count]})}${total.assumed?notice('Davon '+total.assumed+' automatisch Vera / Manuel zugeordnet, ohne Scan.'):''}${notice('Alle gespeicherten Ausräumvorgänge, auch ältere als die letzten 30 Spülgänge. Offene Spülgänge zählen nicht.')}`;
    return `<div class="statistics">${section({id:'statistics',title:'Statistik',content})}${versionInfo({frontend:SV_VERSION,ui:UI_VERSION})}</div>`;
  }
  _render() {
    if (!this._config || !this._hass) return;
    if (!this._canSettings()) this._settings = false;
    const history = this._hass.states[this._config.entity];
    const duty = this._hass.states[this._config.duty_entity];
    const unavailable = !history || ['unknown','unavailable'].includes(history.state);
    const dutyValue = duty && !['unknown','unavailable'].includes(duty.state) ? duty.state : 'Nicht verfügbar';
    const attributes = history?.attributes || {};
    const rows = Array.isArray(attributes.eintraege) ? attributes.eintraege : [];
    const openId = attributes.offener_spuelgang;
    const current = rows.find(row => row.id === openId);
    const signature = JSON.stringify([this._config,unavailable,history?.state,rows,attributes.statistik,this._settings,this._canSettings(),this._hass.user?.id,openId,dutyValue,this._hass.locale,this._hass.config?.time_zone]);
    if (this._signature === signature) return;
    this._signature = signature;
    this._rememberFolds();
    const visible = rows.filter(row => row.emptied_by && row.status !== 'offen').slice(0,this._config.max_entries);
    this.shadowRoot.innerHTML=`<style>${UI_CSS}</style><ha-card>
    ${navigation({label:this._config.title,items:[{id:'overview',label:this._config.title}],active:this._settings?'settings':'overview',settings:this._canSettings(),help:false})}
    <main>${this._settings?this._statistics(attributes.statistik,unavailable):row({title:'Als Nächstes',trailing:`<strong>${svEscape(dutyValue)}</strong>`})+
    (unavailable?notice('Verlaufssensor nicht verfügbar. Entität und Leseberechtigung prüfen: '+this._config.entity,{error:true}):openId?row({title:(current?.assigned_to||dutyValue)+' ist mit dem Ausräumen dran.',description:(current?'Fertig seit '+svDate(current.finished_at,this._hass)+(current.observed_after_restart?' ≈':'')+' · ':'')+'Nach dem Ausräumen den NFC-Tag scannen.'}):notice('Aktuell kein Ausräumen offen.'))+this._history(visible,unavailable)}
    </main></ha-card>`;
  }
}
if (!customElements.get('spuelmaschine-verlauf-card')) customElements.define('spuelmaschine-verlauf-card',SpuelmaschineVerlaufCard);
window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === 'spuelmaschine-verlauf-card')) window.customCards.push({type:'spuelmaschine-verlauf-card',name:'Spülmaschine Verlauf',description:'Spülmaschinendienst und aufklappbarer Verlauf im Manager-Stil',preview:true});
