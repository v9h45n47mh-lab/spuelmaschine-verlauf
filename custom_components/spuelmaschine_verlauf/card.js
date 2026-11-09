/* Spülmaschine Verlauf 0.2.0 — local, read-only dashboard card. */
const SV_VERSION = '0.2.0';
const svEscape = value => String(value ?? '').replace(/[&<>"']/g,
  char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
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
const SV_STYLE = `
:host{display:block;color:var(--primary-text-color,#212121);font-family:var(--ha-font-family-body,Roboto,Arial,sans-serif);font-size:14px;--sv-accent:var(--primary-color,#03a9f4);--sv-muted:var(--secondary-text-color,#727272);--sv-line:var(--divider-color,#e0e0e0);--sv-bg:var(--ha-card-background,var(--card-background-color,#fff))}
*{box-sizing:border-box}ha-card{display:block;background:var(--sv-bg);border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--sv-line));border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow,none);overflow:hidden}
.header{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--sv-line);min-height:56px}.header ha-icon{color:var(--sv-accent);--mdc-icon-size:24px;flex-shrink:0}.title{font-size:16px;font-weight:500;flex:1;min-width:0;overflow-wrap:anywhere}.status{font-size:12px;line-height:1.5;color:var(--sv-muted);display:flex;align-items:center;gap:6px;white-space:nowrap}.dot{width:7px;height:7px;border-radius:50%;background:var(--sv-muted)}.status.open{color:var(--sv-accent)}.open .dot{background:var(--sv-accent)}
.content{padding:0 16px}.assignment{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:15px 0}.label{color:var(--sv-muted);font-size:13px}.person{font-size:16px;font-weight:500;overflow-wrap:anywhere;text-align:right}.notice{padding:0 0 16px;line-height:1.6;color:var(--sv-muted);font-size:13px}.notice.waiting{border-left:3px solid var(--sv-accent);padding:1px 0 1px 12px;margin:0 0 16px}.notice strong{display:block;color:var(--primary-text-color,#212121);font-size:14px;font-weight:500}.notice small{display:block;font-size:12px}.warning{color:var(--error-color,#db4437);font-size:13px;padding:12px 0;line-height:1.5}
details{border-top:1px solid var(--sv-line)}summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;padding:13px 0;min-height:46px;user-select:none}summary::-webkit-details-marker{display:none}summary:focus-visible{outline:2px solid var(--sv-accent);outline-offset:-2px;border-radius:4px}.fold-title{font-size:14px;font-weight:500}.count{font-size:12px;color:var(--sv-muted);margin-left:auto}.chevron{width:18px;height:18px;color:var(--sv-muted);transition:transform .15s;flex-shrink:0}details[open]>summary>.chevron{transform:rotate(180deg)}.entry{border-top:1px solid var(--sv-line)}.entry summary{padding:12px 0;gap:10px}.entry-main{display:flex;flex-direction:column;gap:4px;flex:1;min-width:0}.entry-title{font-size:14px;font-weight:500;overflow-wrap:anywhere}.entry-sub{font-size:12px;color:var(--sv-muted);line-height:1.45}.badge{font-size:11px;line-height:1.4;padding:3px 8px;border-radius:12px;background:var(--secondary-background-color,#f5f5f5);color:var(--sv-muted);flex-shrink:0}.badge.pending{color:var(--sv-accent);background:color-mix(in srgb,var(--sv-accent) 10%,transparent)}.fields{padding:0 0 12px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:8px 12px;font-size:12px;line-height:1.5}.fields dt{color:var(--sv-muted)}.fields dd{margin:0;text-align:right;overflow-wrap:anywhere}.hint{font-size:12px;color:var(--sv-muted);line-height:1.6;margin:0 0 12px}.empty{font-size:13px;color:var(--sv-muted);padding:0 0 16px;line-height:1.6}.footer{border-top:1px solid var(--sv-line);padding:9px 0;color:var(--sv-muted);font-size:11px;text-align:right}
@media(max-width:380px){.header{padding:12px;gap:8px}.content{padding:0 12px}.title{font-size:15px}.entry summary{gap:7px}.badge{padding:3px 6px;font-size:10px}.fields{gap:7px}.status{font-size:11px}}
@media(prefers-reduced-motion:reduce){.chevron{transition:none}}
`;
const SV_CHEVRON = '<svg class="chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

class SpuelmaschineVerlaufCard extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:'open'}); this._signature = ''; }
  setConfig(config) {
    this._config = {entity:'sensor.spulmaschine_verlauf', duty_entity:'input_select.spuelmaschine_dienst', title:'Spülmaschine', history_open:false, max_entries:30, ...config};
    if (!Number.isInteger(this._config.max_entries) || this._config.max_entries < 1 || this._config.max_entries > 30)
      throw new Error('max_entries muss eine ganze Zahl zwischen 1 und 30 sein.');
    this._signature = ''; this._render();
  }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 4; }
  static getStubConfig() { return {entity:'sensor.spulmaschine_verlauf',duty_entity:'input_select.spuelmaschine_dienst'}; }
  _entry(row, opened) {
    const done = row.status === 'erledigt';
    const pending = row.status === 'offen';
    const assumed = !done && row.emptied_by === 'Vera/Manuel';
    const person = row.emptied_by || row.assigned_to || 'Unbekannt';
    const headline = pending ? `${row.assigned_to || 'Unbekannt'} ist dran` : done ? `${person} hat ausgeräumt` : assumed ? 'Vera/Manuel übernommen' : 'Ohne Bestätigung';
    const badge = pending ? 'Offen' : done ? 'Bestätigt' : assumed ? 'Angenommen' : 'Unbestätigt';
    return `<details class="entry" data-cycle="${svEscape(row.id)}" ${opened ? 'open' : ''}>
      <summary><span class="entry-main"><span class="entry-title">${svEscape(headline)}</span><span class="entry-sub">Fertig ${svEscape(svDate(row.finished_at,this._hass))}${row.observed_after_restart ? ' ≈' : ''}</span></span><span class="badge ${pending ? 'pending' : ''}">${badge}</span>${SV_CHEVRON}</summary>
      <dl class="fields"><dt>Zuständig</dt><dd>${svEscape(row.assigned_to || '—')}</dd><dt>Programm fertig</dt><dd>${svEscape(svDate(row.finished_at,this._hass))}${row.observed_after_restart ? ' ≈' : ''}</dd><dt>Ausgeräumt</dt><dd>${svEscape(svDate(row.emptied_at,this._hass))}</dd><dt>Ausgeräumt von</dt><dd>${svEscape(row.emptied_by || '—')}</dd><dt>Wartezeit</dt><dd>${svEscape(svDuration(row.waiting_minutes))}</dd></dl>
      ${assumed ? '<p class="hint">Automatisch zugeordnet, weil der nächste Spülgang fertig wurde. Keine persönliche Bestätigung; Ausräumzeit unbekannt.</p>' : ''}
      ${row.observed_after_restart ? '<p class="hint">≈ Nach HA-Neustart erkannt. Die tatsächliche Fertigzeit ist unbekannt.</p>' : ''}
    </details>`;
  }
  _render() {
    if (!this._config || !this._hass) return;
    const history = this._hass.states[this._config.entity];
    const duty = this._hass.states[this._config.duty_entity];
    const unavailable = !history || ['unknown','unavailable'].includes(history.state);
    const dutyValue = duty && !['unknown','unavailable'].includes(duty.state) ? duty.state : 'Nicht verfügbar';
    const attributes = history?.attributes || {};
    const rows = Array.isArray(attributes.eintraege) ? attributes.eintraege : [];
    const openId = attributes.offener_spuelgang;
    const current = rows.find(row => row.id === openId);
    const signature = JSON.stringify([this._config,unavailable,history?.state,rows,openId,dutyValue,this._hass.locale,this._hass.config?.time_zone]);
    if (this._signature === signature) return;
    this._signature = signature;
    const fold = this.shadowRoot.querySelector('details.history');
    const historyOpen = fold ? fold.open : Boolean(this._config.history_open);
    const opened = new Set([...this.shadowRoot.querySelectorAll('details.entry[open]')].map(e => e.dataset.cycle));
    const visible = rows.slice(0,this._config.max_entries);
    const status = unavailable ? 'Nicht verfügbar' : openId ? 'Ausräumen offen' : 'Bereit';
    this.shadowRoot.innerHTML = `<style>${SV_STYLE}</style><ha-card>
      <div class="header"><ha-icon icon="mdi:dishwasher" aria-hidden="true"></ha-icon><span class="title">${svEscape(this._config.title)}</span><span class="status ${openId && !unavailable ? 'open' : ''}"><span class="dot"></span>${status}</span></div>
      <div class="content"><div class="assignment"><span class="label">Als Nächstes</span><strong class="person">${svEscape(dutyValue)}</strong></div>
      ${unavailable ? `<div class="warning">Verlaufssensor nicht verfügbar. Entität und Leseberechtigung prüfen: ${svEscape(this._config.entity)}</div>` : openId ? `<div class="notice waiting"><strong>${svEscape(current?.assigned_to || dutyValue)} ist mit dem Ausräumen dran.</strong>${current ? `<small>Fertig seit ${svEscape(svDate(current.finished_at,this._hass))}${current.observed_after_restart ? ' ≈' : ''}</small>` : ''}<small>Nach dem Ausräumen den NFC-Tag scannen.</small></div>` : '<div class="notice">Aktuell kein Ausräumen offen.</div>'}
      <details class="history" ${historyOpen ? 'open' : ''}><summary><span class="fold-title">Verlauf</span><span class="count">${svEscape(unavailable ? '—' : history.state)} Spülgänge</span>${SV_CHEVRON}</summary>
      ${unavailable ? '<div class="empty">Der Verlauf kann derzeit nicht angezeigt werden.</div>' : visible.length ? visible.map(row => this._entry(row,opened.has(row.id))).join('') + `<p class="hint">Letzte ${visible.length} von ${svEscape(history.state)} Spülgängen. Ältere Einträge bleiben gespeichert.</p>` : '<div class="empty">Noch keine Spülgänge gespeichert.</div>'}</details>
      <div class="footer">Spülmaschine Verlauf · ${SV_VERSION}</div></div></ha-card>`;
  }
}
if (!customElements.get('spuelmaschine-verlauf-card')) customElements.define('spuelmaschine-verlauf-card',SpuelmaschineVerlaufCard);
window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === 'spuelmaschine-verlauf-card')) window.customCards.push({type:'spuelmaschine-verlauf-card',name:'Spülmaschine Verlauf',description:'Spülmaschinendienst und aufklappbarer Verlauf im Manager-Stil',preview:true});
