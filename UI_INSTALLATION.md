# UI Installation Guide - Hassbeam Connect

Diese Anleitung zeigt Ihnen, wie Sie die Benutzeroberfläche für Hassbeam Connect einrichten.

## Schritt 1: Integration installieren

### Option A: HACS Installation (empfohlen)

1. **Über HACS installieren:**
   - Öffnen Sie HACS in Home Assistant
   - Gehen Sie zu "Integrationen" 
   - Klicken Sie auf "Benutzerdefinierte Repositories"
   - Fügen Sie die Repository-URL hinzu: `https://github.com/BasilBerg/hassbeam-connect`
   - Kategorie: "Integration"
   - Installieren Sie "Hassbeam Connect"

2. **Nach HACS-Installation befinden sich die Dateien hier:**
   ```
   # Integration:
   config/custom_components/hassbeam_connect/
   
   # Frontend-Karte (automatisch von HACS verwaltet):
   config/www/community/hassbeam-connect/hassbeam-card.js
   ```

### Option B: Manuelle Installation

1. **Dateien kopieren:**
   - Kopieren Sie `custom_components/hassbeam_connect/` nach `config/custom_components/`
   - Kopieren Sie `hassbeam-card.js` nach `config/www/`

2. **Home Assistant neustarten:**

   ```bash
   # Home Assistant Core
   systemctl restart home-assistant
   
   # Home Assistant Supervised/Container
   docker restart homeassistant
   ```

## Schritt 2: Integration hinzufügen

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf **+ Integration hinzufügen**
3. Suchen Sie nach "Hassbeam Connect"
4. Folgen Sie dem Setup-Assistenten

## Schritt 3: Frontend-Resource registrieren

### Für HACS-Installation:

1. Gehen Sie zu **Einstellungen** → **Dashboards** → **Ressourcen**
2. Klicken Sie auf **+ Ressource hinzufügen**
3. **URL:** `/hacsfiles/hassbeam-connect/hassbeam-card.js`
4. **Ressourcentyp:** `JavaScript Modul`
5. Klicken Sie auf **Erstellen**

### Für manuelle Installation:

1. Gehen Sie zu **Einstellungen** → **Dashboards** → **Ressourcen**
2. Klicken Sie auf **+ Ressource hinzufügen**
3. **URL:** `/local/hassbeam-card.js`
4. **Ressourcentyp:** `JavaScript Modul`
5. Klicken Sie auf **Erstellen**

## Schritt 4: Karte zum Dashboard hinzufügen

### Über die UI:
1. Gehen Sie zu Ihrem Dashboard
2. Klicken Sie auf **Bearbeiten** (Stift-Symbol oben rechts)
3. Klicken Sie auf **+ Karte hinzufügen**
4. Wählen Sie **Manuell** am Ende der Liste
5. Fügen Sie dieses YAML ein:
   ```yaml
   type: custom:hassbeam-connect-card
   ```
6. Klicken Sie auf **Speichern**

### Über YAML:
```yaml
type: custom:hassbeam-connect-card
```

## Schritt 5: HassBeam Gerät konfigurieren

Stellen Sie sicher, dass Ihr HassBeam-Gerät korrekt konfiguriert ist und Events vom Typ `esphome.hassbeam.ir_received` sendet.

Beispiel ESPHome-Konfiguration:
```yaml
esphome:
  name: hassbeam
  platform: ESP32
  board: esp32dev

wifi:
  ssid: "Ihr_WLAN"
  password: "Ihr_Passwort"

api:
  encryption:
    key: "Ihr_API_Key"

ota:
  password: "Ihr_OTA_Passwort"

logger:

remote_receiver:
  pin: GPIO14
  dump: all
  on_raw:
    - homeassistant.event:
        event: esphome.hassbeam.ir_received
        data:
          raw_data: !lambda 'return x;'
          protocol: !lambda 'return protocol;'
```

## Nutzung der UI

1. **Öffnen Sie die Hassbeam Connect Karte** in Ihrem Dashboard
2. **Geben Sie einen Gerätenamen ein** (z.B. "TV", "Soundbar", "Klimaanlage")
3. **Geben Sie eine Aktion ein** (z.B. "power", "volume_up", "kanal_1")
4. **Klicken Sie auf "IR-Code aufnehmen"**
5. **Richten Sie Ihre Fernbedienung auf das HassBeam-Gerät** und drücken Sie die gewünschte Taste
6. **Der Code wird automatisch gespeichert** und in der Liste der zuletzt aufgenommenen Codes angezeigt

## Verfügbare Services

Nach der Installation stehen folgende Services zur Verfügung:

### `hassbeam_connect.start_listening`
Startet das Abhören für einen IR-Code:
```yaml
service: hassbeam_connect.start_listening
data:
  device: "tv"
  action: "power"
```

### `hassbeam_connect.get_recent_codes`
Ruft zuletzt aufgenommene IR-Codes ab:
```yaml
service: hassbeam_connect.get_recent_codes
data:
  device: "tv"  # optional: nur für bestimmtes Gerät
  limit: 10     # optional: max. Anzahl Codes
```

## Problembehandlung

### Die Karte wird nicht angezeigt
1. Überprüfen Sie, ob die Datei `www/hassbeam-card.js` existiert
2. Stellen Sie sicher, dass die Resource korrekt registriert ist
3. Leeren Sie den Browser-Cache (Strg+F5)
4. Überprüfen Sie die Browser-Konsole auf Fehler

### Services funktionieren nicht
1. Überprüfen Sie, ob die Integration korrekt installiert ist
2. Prüfen Sie die Home Assistant Logs auf Fehler
3. Stellen Sie sicher, dass das HassBeam-Gerät erreichbar ist

### IR-Codes werden nicht empfangen
1. Überprüfen Sie die ESPHome-Konfiguration
2. Stellen Sie sicher, dass der IR-Empfänger korrekt angeschlossen ist
3. Prüfen Sie, ob Events in Home Assistant ankommen:
   ```yaml
   # In einer Automatisierung testen
   trigger:
     - platform: event
       event_type: esphome.hassbeam.ir_received
   action:
     - service: notify.notify
       data:
         message: "IR Event empfangen!"
   ```

## Erweiterte Konfiguration

Sie können die Karte auch mit zusätzlichen Optionen konfigurieren:

```yaml
type: custom:hassbeam-connect-card
title: "Mein IR Code Manager"  # optional: eigener Titel
show_recent: true              # optional: kürzlich aufgenommene Codes anzeigen
max_recent: 5                  # optional: max. Anzahl anzuzeigender Codes
```

## Support

Bei Problemen:
1. Überprüfen Sie die Home Assistant Logs
2. Öffnen Sie die Browser-Konsole für JavaScript-Fehler
3. Erstellen Sie ein Issue auf GitHub mit detaillierten Informationen
