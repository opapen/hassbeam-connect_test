#!/usr/bin/env python3
"""
Installation and setup script for Hassbeam Connect
This script helps set up the integration for testing
"""

import os
import shutil
import sys
from pathlib import Path

def find_home_assistant_config():
    """Try to find Home Assistant configuration directory"""
    common_paths = [
        os.path.expanduser("~/.homeassistant"),
        "/config",  # Home Assistant OS/Container
        os.path.expanduser("~/homeassistant"),
        os.path.expanduser("~/.config/homeassistant")
    ]
    
    for path in common_paths:
        if os.path.exists(path) and os.path.isdir(path):
            # Check if it looks like a Home Assistant config dir
            if os.path.exists(os.path.join(path, "configuration.yaml")):
                return path
    
    return None

def install_integration(ha_config_path):
    """Install the integration files"""
    print(f"📁 Installing integration to: {ha_config_path}")
    
    # Create directories if they don't exist
    custom_components_dir = os.path.join(ha_config_path, "custom_components")
    www_dir = os.path.join(ha_config_path, "www")
    
    os.makedirs(custom_components_dir, exist_ok=True)
    os.makedirs(www_dir, exist_ok=True)
    
    # Copy integration files
    source_integration = os.path.join(os.path.dirname(__file__), "custom_components", "hassbeam_connect")
    target_integration = os.path.join(custom_components_dir, "hassbeam_connect")
    
    if os.path.exists(target_integration):
        print("⚠️  Integration directory already exists. Removing old version...")
        shutil.rmtree(target_integration)
    
    shutil.copytree(source_integration, target_integration)
    print("✅ Integration files copied")
    
    # Copy www file
    source_www = os.path.join(os.path.dirname(__file__), "www", "hassbeam-card.js")
    target_www = os.path.join(www_dir, "hassbeam-card.js")
    
    shutil.copy2(source_www, target_www)
    print("✅ Frontend card copied")
    
    return True

def create_configuration_snippet():
    """Create a configuration snippet for the user"""
    config_snippet = """
# Add this to your configuration.yaml to enable debug logging
logger:
  default: warning
  logs:
    custom_components.hassbeam_connect: debug

# Add this to your Lovelace dashboard resources
# (Go to Settings -> Dashboards -> Three dots -> Resources)
# URL: /local/hassbeam-card.js
# Type: JavaScript Module

# Then add this card to your dashboard:
# type: custom:ir-code-logger-card
"""
    
    with open("configuration_snippet.yaml", "w") as f:
        f.write(config_snippet)
    
    print("📝 Configuration snippet created: configuration_snippet.yaml")

def main():
    print("🏠 Hassbeam Connect - Installation Script")
    print("=" * 50)
    
    # Try to find Home Assistant config directory
    ha_config_path = find_home_assistant_config()
    
    if not ha_config_path:
        print("❌ Could not find Home Assistant configuration directory")
        print("\nPlease manually specify the path to your Home Assistant config directory:")
        ha_config_path = input("Enter path (or press Enter to skip installation): ").strip()
        
        if not ha_config_path:
            print("⏭️  Skipping installation. You can manually copy the files later.")
            create_configuration_snippet()
            return
        
        if not os.path.exists(ha_config_path):
            print(f"❌ Directory {ha_config_path} does not exist")
            return
    
    print(f"✅ Found Home Assistant config directory: {ha_config_path}")
    
    # Install the integration
    try:
        install_integration(ha_config_path)
        create_configuration_snippet()
        
        print("\n🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. Restart Home Assistant")
        print("2. Go to Settings -> Devices & Services")
        print("3. Click 'Add Integration' and search for 'Hassbeam Connect'")
        print("4. Set up your HassBeam ESPHome device (see hassbeam-esphome.yaml)")
        print("5. Add the Lovelace card to your dashboard")
        print("6. Test with your IR remote controls")
        print("\nFor detailed testing instructions, see TESTING.md")
        
    except Exception as e:
        print(f"❌ Installation failed: {str(e)}")
        print("\nYou can manually copy the files:")
        print("- Copy custom_components/hassbeam_connect to your Home Assistant custom_components directory")
        print("- Copy www/hassbeam-card.js to your Home Assistant www directory")

if __name__ == "__main__":
    main()
