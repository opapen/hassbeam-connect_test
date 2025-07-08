# HACS Installation - Hassbeam Connect

## 🏠 HACS Installation (Home Assistant Community Store)

Diese Anleitung zeigt die Installation über HACS - die empfohlene Methode.

### Schritt 1: Repository hinzufügen

1. **HACS öffnen:**
   - Gehen Sie zu HACS in der Seitenleiste
   - Klicken Sie auf "Integrationen"

2. **Custom Repository hinzufügen:**
   - Klicken Sie auf die drei Punkte (⋮) oben rechts
   - Wählen Sie "Benutzerdefinierte Repositories"
   - **Repository:** `https://github.com/BasilBerg/hassbeam-connect`
   - **Kategorie:** Integration
   - Klicken Sie "Hinzufügen"

### Schritt 2: Integration installieren

1. **Hassbeam Connect finden:**
   - Suchen Sie nach "Hassbeam Connect"
   - Klicken Sie auf das Repository

2. **Installation:**
   - Klicken Sie "Herunterladen"
   - Starten Sie Home Assistant neu

### Schritt 3: Integration einrichten

1. **Integration hinzufügen:**
   - Gehen Sie zu Einstellungen → Geräte & Dienste
   - Klicken Sie "+ Integration hinzufügen"
   - Suchen Sie "Hassbeam Connect"
   - Folgen Sie dem Setup-Assistenten

### Schritt 4: Frontend-Karte registrieren

1. **Resource registrieren:**
   - Gehen Sie zu Einstellungen → Dashboards → Ressourcen
   - Klicken Sie "+ Ressource hinzufügen"
   - **URL:** `/hacsfiles/hassbeam-connect/hassbeam-card.js`
   - **Typ:** JavaScript Modul
   - Speichern

### Schritt 5: Karte zum Dashboard hinzufügen

1. **Dashboard bearbeiten:**
   - Gehen Sie zu Ihrem Dashboard
   - Klicken Sie "Bearbeiten" (Stift-Symbol)
   - Klicken Sie "+ Karte hinzufügen"

2. **Karte konfigurieren:**
   - Wählen Sie "Manuell" ganz unten
   - Fügen Sie ein:
     ```yaml
     type: custom:hassbeam-connect-card
     ```
   - Speichern

## 📁 Dateipfade nach HACS-Installation

Nach der HACS-Installation befinden sich die Dateien hier:

```
config/
├── custom_components/
│   └── hassbeam_connect/              # Integration (von HACS verwaltet)
│       ├── __init__.py
│       ├── config_flow.py
│       ├── const.py
│       ├── database.py
│       ├── manifest.json
│       └── services.yaml
└── www/
    └── community/
        └── hassbeam-connect/          # Frontend-Dateien (von HACS verwaltet)
            └── hassbeam-card.js
```

## 🔄 Updates über HACS

1. **Automatische Update-Benachrichtigungen:**
   - HACS zeigt verfügbare Updates an
   - Klicken Sie auf "Aktualisieren"

2. **Nach Updates:**
   - Starten Sie Home Assistant neu
   - Leeren Sie den Browser-Cache (Strg+F5)

## ✅ Funktionstest

Nach der Installation:

1. **Services überprüfen:**
   - Entwicklertools → Services
   - Suchen Sie nach `hassbeam_connect.start_listening`

2. **Karte testen:**
   - Öffnen Sie die Hassbeam Connect Karte
   - Geben Sie Testdaten ein
   - Klicken Sie "IR-Code aufnehmen"

## 🔧 Problembehandlung

### Karte wird nicht gefunden
- Überprüfen Sie die Resource-URL: `/hacsfiles/hassbeam-connect/hassbeam-card.js`
- Browser-Cache leeren (Strg+F5)

### Integration nicht verfügbar
- Home Assistant nach HACS-Installation neu starten
- HACS-Logs überprüfen

### Frontend-Resource-Fehler
- Stellen Sie sicher, dass HACS korrekt installiert ist
- Überprüfen Sie die Datei unter `config/www/community/hassbeam-connect/`

## 📞 Support

Bei Problemen:
1. Überprüfen Sie die Home Assistant Logs
2. Prüfen Sie die HACS-Logs  
3. Erstellen Sie ein Issue auf GitHub

**Repository:** https://github.com/BasilBerg/hassbeam-connect
