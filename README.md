# Hassbeam Connect

Home Assistant integration to capture and save IR codes from remote controls using HassBeam.

## What it does

This integration allows you to:
- Capture IR codes from any remote control using a HassBeam device
- Save captured codes to a database with custom labels (device + action)
- Use a simple web interface to manage the capture process
- Integrate captured codes into Home Assistant automations

## Quick Test

To test if the core functionality works, run:

```bash
python test_hassbeam.py
```

## Installation

### Option 1: HACS Installation (empfohlen)
1. Fügen Sie dieses Repository als benutzerdefiniertes Repository in HACS hinzu
2. Installieren Sie "Hassbeam Connect" über HACS
3. Starten Sie Home Assistant neu
4. Folgen Sie der `HACS_INSTALLATION.md` für die UI-Einrichtung

### Option 2: Manuelle Installation
1. Kopieren Sie `custom_components/hassbeam_connect` in Ihr `custom_components` Verzeichnis
2. Kopieren Sie `hassbeam-card.js` in Ihr `www` Verzeichnis  
3. Starten Sie Home Assistant neu
4. Folgen Sie der `UI_INSTALLATION.md` für die UI-Einrichtung

### Option 3: Automatische Installation
```bash
python install.py
```

## Setup

1. **Set up HassBeam device**: Use the provided `hassbeam-esphome.yaml` configuration
2. **Add integration**: Go to Settings → Devices & Services → Add Integration → "Hassbeam Connect"
3. **Add Lovelace card**: Add the custom card to your dashboard (see `TESTING.md` for details)

## Usage

1. Open the Hassbeam Connect card in your Lovelace dashboard
2. Enter a device name (e.g., "TV") and action (e.g., "power")
3. Click "IR-Code speichern" (Save IR Code)
4. Point your remote at the HassBeam device and press the button
5. The IR code will be saved to the database with your labels

## Testing

See `TESTING.md` for comprehensive testing instructions and troubleshooting.

## Files

- `custom_components/hassbeam_connect/` - Home Assistant integration
- `www/hassbeam-card.js` - Lovelace frontend card
- `hassbeam-esphome.yaml` - ESPHome configuration example
- `test_hassbeam.py` - Test script for database functionality
- `install.py` - Automated installation script
- `TESTING.md` - Detailed testing guide
