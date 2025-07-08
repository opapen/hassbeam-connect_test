# Testing Guide for Hassbeam Connect

## Prerequisites

To test this integration, you'll need:

1. **Home Assistant instance** (version 2024.0.0 or later)
2. **HassBeam device** - An ESP32/ESP8266 device with IR receiver configured with ESPHome
3. **IR remote control** - Any remote control to test IR code capture
4. **HACS** (Home Assistant Community Store) - Optional, for easier installation

## Setup Steps

### 1. Install the Integration

#### Option A: Manual Installation
1. Copy the `custom_components/hassbeam_connect` folder to your Home Assistant `custom_components` directory
2. Copy `www/hassbeam-card.js` to your Home Assistant `www` directory
3. Restart Home Assistant

#### Option B: HACS Installation
1. Add this repository to HACS
2. Install the integration through HACS
3. Restart Home Assistant

### 2. Configure HassBeam Device (ESPHome)

Create an ESPHome configuration for your HassBeam device:

```yaml
# hassbeam.yaml
esphome:
  name: hassbeam
  friendly_name: HassBeam IR Receiver

esp32:
  board: esp32dev

wifi:
  ssid: "your_wifi_ssid"
  password: "your_wifi_password"

api:
  encryption:
    key: "your_api_key"

ota:
  password: "your_ota_password"

logger:

remote_receiver:
  pin: GPIO14  # Adjust pin as needed
  dump: all
  on_remote_received:
    - homeassistant.event:
        event: esphome.hassbeam.ir_received
        data:
          protocol: !lambda 'return x.get_protocol();'
          data: !lambda 'return x.get_data();'
          command: !lambda 'return x.get_command();'
          address: !lambda 'return x.get_address();'
```

### 3. Add Integration to Home Assistant

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Hassbeam Connect"
4. Follow the setup wizard

### 4. Add the Lovelace Card

Add the custom card to your Lovelace dashboard:

```yaml
# In your dashboard configuration
resources:
  - url: /local/hassbeam-card.js
    type: module

# Add the card to a view
type: custom:ir-code-logger-card
```

## Testing Procedure

### 1. Basic Functionality Test

1. **Open the Hassbeam Connect card** in your Lovelace dashboard
2. **Enter device name** (e.g., "TV")
3. **Enter action name** (e.g., "power")
4. **Click "IR-Code speichern"** (Save IR Code)
5. **Point your remote at the HassBeam device** and press the corresponding button
6. **Check for success message** showing the device and action were saved

### 2. Database Verification

Check if the IR code was saved to the database:

1. Navigate to your Home Assistant config directory
2. Look for the `hassbeam.db` file
3. Open it with a SQLite browser or command line tool:

```bash
sqlite3 hassbeam.db
.tables
SELECT * FROM ir_codes;
```

### 3. Service Call Test

Test the service directly from Developer Tools:

1. Go to Developer Tools → Services
2. Select service: `hassbeam_connect.start_listening`
3. Enter service data:
```yaml
device: test_device
action: test_action
```
4. Call the service
5. Press a button on your remote
6. Check the database for the new entry

### 4. Event Monitoring

Monitor events in real-time:

1. Go to Developer Tools → Events
2. Listen for event: `hassbeam_connect_saved`
3. Use the card to capture an IR code
4. Verify the event is fired with correct data

### 5. Log Analysis

Check Home Assistant logs for any errors:

1. Go to Settings → System → Logs
2. Look for entries related to `hassbeam_connect`
3. Check for any error messages or warnings

## Expected Behavior

### Successful Test Results:
- ✅ Card displays properly in Lovelace
- ✅ Service `hassbeam_connect.start_listening` is available
- ✅ Status shows "Warte auf IR-Event..." when listening
- ✅ IR codes are captured and saved to database
- ✅ Success message displays device and action name
- ✅ Database contains correct IR code data
- ✅ Events are fired correctly

### Common Issues and Solutions:

1. **Card not loading**: Check if `hassbeam-card.js` is in the `www` directory
2. **Service not found**: Ensure the integration is properly installed and Home Assistant restarted
3. **No IR events**: Verify HassBeam device is online and ESPHome configuration is correct
4. **Database errors**: Check file permissions in Home Assistant config directory

## Troubleshooting

### Debug Mode

Enable debug logging for the integration:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.hassbeam_connect: debug
```

### Manual Event Testing

You can manually fire IR events for testing:

1. Go to Developer Tools → Events
2. Fire event: `esphome.hassbeam.ir_received`
3. Event data:
```yaml
protocol: "NEC"
data: "0x12345678"
command: "0x56"
address: "0x1234"
```

## Test Results Template

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Integration loads | No errors | | ⏳ |
| Service available | `hassbeam_connect.start_listening` exists | | ⏳ |
| Card displays | Card shows in Lovelace | | ⏳ |
| IR capture works | IR codes saved to DB | | ⏳ |
| Events fired | `hassbeam_connect_saved` event | | ⏳ |
| Database created | `hassbeam.db` file exists | | ⏳ |
| Multiple captures | Multiple IR codes stored | | ⏳ |

## Performance Testing

Test with multiple rapid captures:
1. Capture 10 IR codes in quick succession
2. Verify all codes are saved correctly
3. Check for any memory leaks or performance issues

## Security Testing

1. Verify database file permissions
2. Test with invalid service data
3. Check for SQL injection vulnerabilities (though unlikely with this simple implementation)
