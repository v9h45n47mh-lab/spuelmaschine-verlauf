# Validierung der UI-Kit-Umstellung

Stand: 2026-11-10. HA UI Kit 1.2.1, unverändert lokal eingebunden und per SHA-256 einschließlich Lizenz geprüft. Karten verwenden ausschließlich UI_CSS; keine lokalen visuellen CSS-Überschreibungen oder SVG-Kopien.

## Desktop, Mobil und Themes

- Erfolgreiche Chromium-Prüfung mit tatsächlichem Produktionsmodul und UI-Kit-Referenz: 1100, 430, 390, 375 und 320 px, jeweils hell und dunkel.
- Exakter Vergleich von Zahnradgeometrie, Schrift, Farbe und Inhaltsabständen mit der Referenz. Keine überlaufenden Seiten oder Zeilen. Die Spülmaschinenkarte enthält keine Eingabedialoge; diese werden in der Haushaltsapp geprüft.
- Desktop- und Mobil-Screenshots beider Themes zusätzlich gesichtet. Screenshots aller Kombinationen liegen im Workflow-Artefakt ui-browser-evidence.
- [Erfolgreicher Browserlauf](https://github.com/v9h45n47mh-lab/spuelmaschine-verlauf/actions/runs/42870214272). Testfixture bildet HA-Benutzer, Zustände und WebSocket-Antworten nach; kein Test an einer laufenden HA-Instanz.

## Funktionen und Berechtigungen

- 27 Backendtests sowie DOM-Tests bestanden. Berechtigungs- und Datenlogik unverändert; kein zusätzliches Access-Control-Recht erforderlich.
- Monatsgruppen, gespeicherter Klappzustand, gesamthafte Statistik, minimale Verlaufszeilen und Zusammenfassung Vera / Manuel geprüft. NFC-, Dienstwechsel- und Speicherlogik unverändert.

## Installation

In HACS aktualisieren, Home Assistant neu starten und Dashboard/App neu laden. Bestehende Daten, Karten-YAML und Freigaben bleiben gültig. Der gesamte Frontendordner wird am bisherigen URL-Präfix ausgeliefert; kein CDN und keine weitere HA-Integration erforderlich.
