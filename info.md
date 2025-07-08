# Hassbeam Connect

Capture and save IR codes from remote controls via ESPHome HassBeam devices.

## Features

- 🎯 **Easy IR Capture**: Simple card interface for capturing remote control codes
- 💾 **Automatic Storage**: Saves captured codes to local database  
- 🔧 **ESPHome Integration**: Works seamlessly with HassBeam ESPHome devices
- 🎨 **Modern UI**: Clean and intuitive Lovelace card

## Installation

This integration includes both backend services and a custom Lovelace card.

### HACS Installation (Recommended)

1. Add this repository to HACS
2. Install "Hassbeam Connect"
3. Restart Home Assistant
4. Add the integration via UI (Settings > Integrations > Add Integration)
5. Add the card to your dashboard

### Manual Installation

See [README.md](./README.md) for detailed manual installation instructions.

## Usage

### Adding the Card

After installation, add the card to your Lovelace dashboard:

```yaml
type: custom:hassbeam-connect-card
```

### Capturing IR Codes

1. Point your remote control at the HassBeam device
2. Enter device name and action in the card
3. Click "Start Listening"
4. Press the button on your remote control
5. The code will be automatically captured and saved

## Support

For issues and questions, please check the [GitHub repository](https://github.com/yourusername/hassbeam-connect).
