# Spülmaschine Verlauf 0.1.1

Lokale Home-Assistant-Integration für die Verlaufsspeicherung. Keine Cloud und keine zusätzlichen Python-Pakete erforderlich.

## Installation

1. ZIP auf dem Computer entpacken.
2. Den enthaltenen Ordner `custom_components/spuelmaschine_verlauf` nach `/config/custom_components/spuelmaschine_verlauf` in Home Assistant kopieren, zum Beispiel mit Studio Code Server oder Samba. `manifest.json` muss direkt in diesem Zielordner liegen. Eine ZIP lässt sich nicht direkt als HA-Integration hochladen.
3. Home Assistant neu starten.
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Spülmaschine Verlauf**.
5. Als Betriebszustand `sensor.geschirrspuler_betriebszustand` und als Diensteinteilung `input_select.spuelmaschine_dienst` auswählen.
6. Im Dropdown-Helfer **Paul** einstellen. Die Integration selbst ändert den Helfer in dieser Version nicht.
7. Optional eine manuelle Dashboard-Karte hinzufügen und den Inhalt von `dashboard.yaml` einfügen. Unter Entwicklerwerkzeuge → Zustände den tatsächlichen Namen des neuen Verlaufssensors prüfen. Erwartet wird `sensor.spulmaschine_verlauf`; bei einer abweichenden ID diese an beiden Stellen in der Karte ersetzen.

Keine Änderung an configuration.yaml erforderlich. Noch keine neue Automation erforderlich: Programmenden werden automatisch beobachtet. Die vorhandene Benachrichtigungsautomation kann zunächst bestehen bleiben.

## Was jetzt funktioniert

- Neue Übergänge auf den exakten Zustand `finished` werden automatisch gespeichert.
- Pro Spülgang: ID, Erkennungszeit des Programmendes, zugeteiltes Kind, Status, später Ausräumzeit und bestätigende Person.
- Unabhängige dauerhafte SQLite-Datei `/config/spuelmaschine_verlauf.sqlite`. Keine automatische zeitliche Löschung, keine Abhängigkeit von der Recorder-Aufbewahrung. Diese Datei in die Sicherung der HA-Konfiguration aufnehmen.
- Der Verlaufssensor stellt die letzten 30 Datensätze bereit. Alle älteren Einträge bleiben in der Datenbank und sind über die Aktion `spuelmaschine_verlauf.get_history` seitenweise abrufbar.
- Gleicher Zustand `finished`, HA-Neustart sowie zwischenzeitlich `unknown`/`unavailable` erzeugen keinen weiteren Eintrag desselben Abschlusses. Ein neuer gültiger Nicht-finished-Zustand und anschließend `finished` bilden einen neuen Abschluss.
- Bei einem weiteren Abschluss ohne vorherige Bestätigung wird der ältere offene Spülgang als **nicht bestätigt** archiviert. Als Ausräumer wird gemäß Haushaltsregel **Vera/Manuel** eingetragen. Das ist eine automatische Annahme, keine persönliche Bestätigung. Die unbekannte Ausräumzeit und Wartezeit bleiben leer. Die Einteilung wird dadurch nicht gewechselt. Nur der neueste Spülgang bleibt offen.
- Beim erstmaligen Einrichten mit bereits fertiger Maschine wird keine historische Fertigzeit erfunden. Erst nach einem neuen Statuswechsel kann ein neuer Abschluss erfasst werden.
- Bei HA-Ausfall kann die tatsächliche Fertigzeit nicht rekonstruiert werden. War vor dem Ausfall ein anderer gültiger Zustand gespeichert und beim Start `finished` sichtbar, wird die Erkennungszeit gespeichert und mit `observed_after_restart: true` markiert. Mehrere vollständig während eines Ausfalls abgelaufene Programme sind nicht rekonstruierbar.

## Was später angeschlossen wird

Diese Version ist ausschließlich der Speicherbaustein. Noch NICHT enthalten: NFC-Scanauswertung, iPhone-Bestätigungsdialog, Push-Versand, Dienstwechsel und Benutzer-/Geräteprüfung. Bestehende Haushalts-App-Verbindungen werden nicht verändert. Die Integration braucht dafür noch keine iPhone-IDs.

### Bestätigte Erledigung speichern

Nach Installation unter Entwicklerwerkzeuge → Aktionen, YAML-Modus:

```yaml
action: spuelmaschine_verlauf.record_emptied
data:
  cycle_id: "HIER_DIE_ID_DES_OFFENEN_SPUELGANGS"
  person: Paul
```

Die Spülgang-ID steht im Verlaufssensor im Attribut `offener_spuelgang`. Der Server erlaubt Maximilian/Paul nur beim passend zugeteilten Spülgang, Vera/Manuel bei jedem offenen Spülgang. Die Person wird hier ausdrücklich als Aktionsparameter übergeben; das ist kein Identitätsnachweis. Die spätere NFC-Automation muss das Gerät und die zugehörige Antwort serverseitig prüfen, bevor sie diese Aktion aufruft. Nicht direkt als ungeschützten Kinder-Dashboard-Button verwenden.

Derselbe bereits bestätigte Vorgang und dieselbe Person sind idempotent. Ein älterer, nicht mehr offener Vorgang lässt sich nicht nachträglich über diese Aktion bestätigen. Ein Aufruf verändert den Dienst-Helfer nicht.

Nach tatsächlicher Änderung wird das Ereignis `spuelmaschine_verlauf_emptied` ausgelöst. Der spätere Dienstwechsel muss an dieses Ereignis und die gespeicherte Person gekoppelt werden. Wiederholte Bestätigungen senden dieses Ereignis nicht erneut. In dieser Version wird der Dienst noch nicht gewechselt.

### Gesamten Verlauf abrufen

```yaml
action: spuelmaschine_verlauf.get_history
data:
  limit: 100
  offset: 0
response_variable: verlauf
```

Die Rückgabe enthält `total`, `open_id` und `entries`. Für weitere Seiten `offset` erhöhen, maximal 1000 Einträge pro Abruf. `response_variable` ist für Skripte/Automationen gedacht; in Entwicklerwerkzeuge → Aktionen die dort angebotene Antwortanzeige verwenden.

### Manueller Eintrag für externe Auslöser

`spuelmaschine_verlauf.record_finished` akzeptiert einen eindeutigen `cycle_key`. Wiederholung mit demselben Schlüssel erzeugt keinen neuen Datensatz. Diese Aktion ist für spätere externe Quellen gedacht. NICHT zusätzlich zum automatischen Beobachter für denselben Abschluss aufrufen, da sonst ein weiterer Spülgang entsteht.

## Prüfung vor Produktivbetrieb

Die beiliegenden 13 Tests prüfen die echte SQLite-Speicherung in temporären Dateien: Neustart, doppelte Abschlüsse, falsches Kind, Elternbestätigung, veraltete Antworten, Idempotenz, Seitenabruf und Transaktions-Rollback. Python-Syntax und JSON wurden ebenfalls geprüft. Ein Lauf in einer echten HA-Instanz war hier nicht möglich; Einrichtung und Erfassung deshalb zunächst in deinem HA testen. Bestehende Spüldienstlogik erst nach dem vollständigen Umstieg deaktivieren.

Testaufruf: `python3 -m unittest discover -s tests -v`.
