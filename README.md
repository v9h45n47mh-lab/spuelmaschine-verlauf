# Spülmaschine Verlauf

Home-Assistant-Integration zum lokalen Speichern von Programmenden und Ausräumbestätigungen.

Version **0.1.0** enthält die Verlaufsspeicherung. NFC, Pushnachrichten und Dienstwechsel werden später ergänzt.

## Installation

Den Ordner `custom_components/spuelmaschine_verlauf` nach `/config/custom_components/` kopieren, Home Assistant neu starten und unter **Einstellungen → Geräte & Dienste → Integration hinzufügen → Spülmaschine Verlauf** einrichten.

Die vollständige Anleitung steht in [ANLEITUNG.md](ANLEITUNG.md). Eine Dashboard-Vorlage liegt in [dashboard.yaml](dashboard.yaml).

## Speicherung

Die Historie liegt lokal in `/config/spuelmaschine_verlauf.sqlite`. Sie wird nicht durch die normale Recorder-Aufbewahrung gelöscht. Die Datenbank gehört in die Sicherung der Home-Assistant-Konfiguration.

## Validierung

Zehn SQLite-Tests sind enthalten und erfolgreich. Ein Test in einer echten Home-Assistant-Instanz steht aus.

```sh
python3 -m unittest discover -s tests -v
```
