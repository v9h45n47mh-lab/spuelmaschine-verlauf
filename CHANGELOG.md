# Änderungen

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
