# Spülmaschine Verlauf

Home-Assistant-Integration zum lokalen Speichern von Programmenden und Ausräumbestätigungen.

Version **0.2.0** enthält die Verlaufsspeicherung. NFC, Pushnachrichten und Dienstwechsel werden später ergänzt.

## Installation

Den Ordner `custom_components/spuelmaschine_verlauf` nach `/config/custom_components/` kopieren, Home Assistant neu starten und unter **Einstellungen → Geräte & Dienste → Integration hinzufügen → Spülmaschine Verlauf** einrichten.

Die vollständige Anleitung steht in [ANLEITUNG.md](ANLEITUNG.md). Eine Dashboard-Vorlage liegt in [dashboard.yaml](dashboard.yaml).

## Speicherung

Die Historie liegt lokal in `/config/spuelmaschine_verlauf.sqlite`. Sie wird nicht durch die normale Recorder-Aufbewahrung gelöscht. Die Datenbank gehört in die Sicherung der Home-Assistant-Konfiguration.

## Validierung

13 SQLite-Tests sind enthalten und erfolgreich. Ein Test in einer echten Home-Assistant-Instanz steht aus.

```sh
python3 -m unittest discover -s tests -v
```

## Neu in 0.1.1

Wird ein neuer Spülgang fertig, während der vorherige noch offen ist, erhält der vorherige als Ausräumer automatisch **Vera/Manuel**. Sein Status bleibt **nicht bestätigt**, weil niemand gescannt hat. Die tatsächliche Ausräumzeit ist unbekannt und bleibt leer. Bereits bestätigte Einträge werden nicht verändert. Der Dienst-Helfer bleibt unverändert. Keine rückwirkende Änderung bereits archivierter Spülgänge.

## Dashboard-Karte ab 0.2.0

Die neue Karte orientiert sich an Light Manager und Shutter Manager: HA-Akzentfarbe, kompakter Kopf mit Spülmaschinen-Symbol, Status, Einteilung sowie aufklappbarer Verlauf. Jeder Spülgang lässt sich für Fertigzeit, Bestätigungszeit, Person und Wartezeit aufklappen. Die Karte verwendet ausschließlich bereits lesbare HA-Entitäten und ruft keine Schreibaktionen auf.

Nach dem Update Home Assistant neu starten und die Dashboard-Seite bzw. Companion-App neu laden. Die JavaScript-Datei wird automatisch mit der Integration geladen; kein weiteres HACS-Frontend-Repository und kein manueller Ressourceneintrag nötig.

Die bisherige Markdown-Karte einmalig ersetzen:

```yaml
type: custom:spuelmaschine-verlauf-card
entity: sensor.spulmaschine_verlauf
duty_entity: input_select.spuelmaschine_dienst
title: Spülmaschine
history_open: false
max_entries: 30
```

Bei umbenanntem Verlaufssensor `entity` anpassen. `history_open: true` klappt den Verlauf initial auf. Access Control benötigt Leserechte auf beide konfigurierten Entitäten; weitere Rechte oder API-Freigaben kommen durch diese Karte nicht hinzu. Das alte Markdown-YAML bleibt nutzbar, wird aber nicht automatisch umgebaut.

Frontend-Prüfung mit Node.js und `linkedom`: `node tests/test_card.cjs`. Die DOM-Prüfungen decken Zustände, Zeitformatierung, aufklappbare Details und sicheres Einfügen von Text ab. Ein visueller Test in deiner HA-Instanz steht aus.

## Darstellung ab 0.2.1

Die Karte hat keine Versionszeile und keinen Status oben rechts. Der aufklappbare Verlauf zeigt ausschließlich Ausräumer und Ausräumzeit. Vera und Manuel erscheinen unter der gemeinsamen Bezeichnung **Vera & Manuel**. Automatisch zugeordnete Einträge ohne Ausräumzeit zeigen **Zeitpunkt unbekannt**. Offene Spülgänge stehen nur im Hauptbereich. Die vorhandene YAML-Konfiguration bleibt gültig. Die Begrenzung auf die letzten 30 Spülgänge des Verlaufssensors bleibt bestehen.
