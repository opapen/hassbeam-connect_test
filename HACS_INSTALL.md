# 📡 Hassbeam Connect - HACS Installation Guide

## Nach der HACS-Installation

Nach der erfolgreichen Installation über HACS sind **zwei Schritte** erforderlich:

### 1. Frontend-Ressource hinzufügen ⚡

HACS hat die Datei `hassbeam-card.js` verfügbar gemacht, aber Sie müssen sie manuell zu Home Assistant hinzufügen:

1. **Gehe zu:** `Settings` → `Dashboards` → `Resources`
2. **Klicke:** `Add Resource`
3. **URL:** `/hacsfiles/hassbeam-connect/hassbeam-card.js`
4. **Resource type:** `JavaScript Module`
5. **Klicke:** `Create`

### 2. Integration hinzufügen 🔧

1. **Gehe zu:** `Settings` → `Devices & Services` → `Integrations`
2. **Klicke:** `Add Integration`
3. **Suche:** `Hassbeam Connect`
4. **Folge** den Setup-Anweisungen

### 3. Karte verwenden 🎯

Nach beiden Schritten können Sie die Karte zu Ihrem Dashboard hinzufügen:

```yaml
type: custom:hassbeam-connect-card
```

## Warum ist das nötig?

HACS **installiert** Frontend-Dateien automatisch, aber **registriert** sie nicht automatisch als Ressourcen in Home Assistant. Das ist ein Sicherheitsfeature und verhindert ungewolltes Laden von JavaScript-Code.

## Fehlerbehebung 🔧

### "Custom element doesn't exist: hassbeam-connect-card"

**Lösung:** Die Frontend-Ressource wurde nicht hinzugefügt oder ist nicht geladen.

1. **Überprüfen:** Ist die Ressource hinzugefügt?
   - `Settings` → `Dashboards` → `Resources`
   - Sollte `/hacsfiles/hassbeam-connect/hassbeam-card.js` enthalten

2. **Browser-Cache leeren:**
   - Drücke `Ctrl+F5` (oder `Cmd+Shift+R` auf Mac)
   - Oder leere den Browser-Cache manuell

3. **Home Assistant neustarten**

### Ressource nicht gefunden (404)

**Grund:** HACS hat die Datei möglicherweise an einem anderen Ort platziert.

**Alternative URLs zum Testen:**

- `/hacsfiles/hassbeam-connect/hassbeam-card.js` (Standard)
- `/hacsfiles/BasilBerg-hassbeam-connect/hassbeam-card.js` (mit Benutzername)
- `/hacsfiles/hassbeam_connect/hassbeam-card.js` (mit Unterstrich)

**So finden Sie den korrekten Pfad:**

1. Öffnen Sie die Entwicklertools Ihres Browsers (F12)
2. Gehen Sie zum `Network`-Tab
3. Laden Sie Ihr Dashboard neu
4. Schauen Sie nach 404-Fehlern für `hassbeam-card.js`
5. Der fehlgeschlagene Pfad zeigt, wo Home Assistant die Datei sucht

## Erfolgreiche Installation überprüfen ✅

Nach der vollständigen Installation sollten Sie sehen:

1. **In Resources:** `/hacsfiles/hassbeam-connect/hassbeam-card.js` ist geladen (grüner Status)
2. **In Integrations:** `Hassbeam Connect` ist aktiv
3. **In Dashboard:** Die Karte `type: custom:hassbeam-connect-card` funktioniert
4. **Service verfügbar:** `hassbeam_connect.start_listening` in den Entwicklertools

## Support 💬

Wenn Sie immer noch Probleme haben:

1. **Home Assistant Logs überprüfen:**
   - `Settings` → `System` → `Logs`
   - Suchen Sie nach `hassbeam_connect` Fehlern

2. **Browser-Konsole überprüfen:**
   - F12 → `Console`
   - Schauen Sie nach JavaScript-Fehlern

3. **GitHub Issues:** [Hassbeam Connect Issues](https://github.com/BasilBerg/hassbeam-connect/issues)

---

**Tipp:** Nach erfolgreicher Einrichtung funktioniert alles automatisch - diese Schritte sind nur bei der ersten Installation nötig! 🚀
