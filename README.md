# Spülmaschine Verlauf

Home-Assistant-Integration zum lokalen Speichern von Programmenden und Ausräumbestätigungen.

Version **0.1.1** enthält die Verlaufsspeicherung. NFC, Pushnachrichten und Dienstwechsel werden später ergänzt.

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
