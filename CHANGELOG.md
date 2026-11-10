# Änderungen

## 0.4.3

- Sämtliche lokalen visuellen CSS-Überschreibungen entfernt; Gestaltung ausschließlich aus HA UI Kit 1.2.0.
- Gemeinsame Wiederholungs-, Erledigungs-, Button-, Dialog- und Zählerbausteine direkt mit bestehenden Abläufen verbunden.
- Fachlogik, Berechtigungen, Live-Sync und NFC-Verarbeitung erhalten.

## 0.4.2

- HA UI Kit auf fest eingebundene Version 1.2.0 aktualisiert.
- Passende gemeinsame Aufgaben-, Auswahl- und Statistikbausteine direkt verwendet; lokale Kopien gemeinsamer Stile entfernt.
- Bestehende Aufgaben-, Live-Sync-, NFC- und Berechtigungslogik erhalten.

## 0.4.1

- Fest eingebundenes HA UI Kit auf 1.1.0 aktualisiert, einschließlich der neuesten gemeinsamen Komponenten und Symbole.
- Versionierter Modulpfad, Ressourcenkennung, Prüfsummen und Versionsanzeige aktualisiert. Funktionen und Berechtigungen bleiben unverändert.

## 0.4.0

- Vollständige Oberfläche auf lokal fest eingebundenes HA UI Kit 1.0.0 umgestellt: Navigation, Klappbereiche, Zeilen, Symbole, Farben, Schrift, Abstände und Versionsanzeige.
- Gemeinsame Buttons, Eingaben, Schalter und native Dialoge für Hausarbeiten; bestehende Aufgaben-, NFC- und Berechtigungslogik unverändert.
- Frontend-Verzeichnis liefert auch die versionierten Kit-Module aus; keine zusätzliche Integration und kein CDN erforderlich.

## 0.3.2

- Einstellungssymbol exakt wie im Shutter Manager: identisches SVG, 24 px, grau im Normalzustand und HA-Akzentfarbe mit getöntem Hintergrund bei geöffneten Einstellungen.

## 0.3.1

- Statistik als Gesamtübersicht je Benutzer über den vollständigen gespeicherten Zeitraum; keine Monatsunterteilung in den Einstellungen.
- Monatsgruppen im Verlauf bleiben erhalten.
- Eigenes transparentes Logo für Home Assistant und Marketplace im lokalen brand-Ordner (256/512 px).
- Einstellungen und Versionsnummer weiterhin nur für Vera/Manuel sichtbar.

## 0.3.0

- Verlauf nach Monat/Jahr gruppiert; jede Monatsgruppe lässt sich auf- und zuklappen.
- Elternanzeige einheitlich Vera / Manuel.
- Zahnrad öffnet Einstellungen mit Monatsstatistik über die vollständige gespeicherte Historie: Gesamt und Anzahl je Maximilian, Paul und Vera / Manuel.
- Automatische Elternzuordnungen ohne Scan werden in den Monatszahlen mitgezählt und separat gekennzeichnet; bei unbekannter Ausräumzeit gilt der Monat des Programmendes.
- Einstellungen und Versionsnummer nur für Vera/Manuel sichtbar; kein allgemeiner Admin-Zugriff auf die Einstellungsansicht.
- Bestehende NFC-Automation bleibt unverändert.

## 0.2.2

- Importierbare NFC-Automation: Scan speichert das Ausräumen sofort, ohne Dialog oder Push-Rückfrage.
- Vera/Manuel dürfen jeden offenen Spülgang abschließen; Kinder nur bei passender aktueller Einteilung und Spülgang-Zuordnung.
- Dienstwechsel nur nach erfolgreichem Kinder-Scan; Eltern ändern die Einteilung nicht.
- Unbekannte Geräte, fehlende offene Spülgänge und doppelte Scans bleiben ohne Änderung.
- Die bisherige separate NFC-Automation muss einmalig ersetzt werden; das HACS-Update allein ändert sie nicht.

## 0.2.1

- Versionsanzeige im Kartenfuß und Status oben rechts entfernt.
- Verlauf auf Ausräumer und Ausräumzeit reduziert; offene Spülgänge erscheinen weiterhin nur im Hauptbereich.
- Vera, Manuel und automatische Vera/Manuel-Zuordnungen werden einheitlich als Vera & Manuel dargestellt.
- Unbekannte Ausräumzeiten bleiben als unbekannt gekennzeichnet; gespeicherte Daten werden nicht umgeschrieben.

## 0.2.0

- Eigene Dashboard-Karte im Stil von Light Manager und Shutter Manager.
- Kompakter Kopfbereich mit Symbol, Status und Diensteinteilung.
- Aufklappbarer Verlauf und Details je Spülgang, mobile Darstellung und HA-Themenfarben.
- Automatisches Laden der Karte mit der Integration.
- Kein zusätzlicher Schreibzugriff; vorhandene Speicher- und Automationslogik bleibt erhalten.

## 0.1.1

- Neuer fertiger Spülgang schließt den vorherigen offenen Vorgang mit Ausräumer **Vera/Manuel** ab.
- Automatische Zuordnung bleibt als **nicht bestätigt** erkennbar; keine erfundene Ausräumzeit.
- Keine Änderung bestätigter Datensätze, keine rückwirkende Umschreibung archivierter Vorgänge und kein automatischer Dienstwechsel.
- 13 Tests erfolgreich, einschließlich Neustart und Erhalt persönlicher Bestätigungen.

## 0.1.0

- Erste Version der dauerhaften lokalen Verlaufsspeicherung.
