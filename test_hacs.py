#!/usr/bin/env python3
"""
HACS Compatibility Test für Hassbeam Connect
Überprüft, ob die Integration HACS-kompatibel strukturiert ist
"""

import json
import os
from pathlib import Path

def test_hacs_structure():
    """Überprüft die HACS-Kompatibilität der Integration."""
    
    root_path = Path(__file__).parent
    print(f"📁 Überprüfe HACS-Struktur in: {root_path}")
    print("=" * 60)
    
    # 1. hacs.json prüfen
    hacs_json_path = root_path / "hacs.json"
    if hacs_json_path.exists():
        print("✅ hacs.json gefunden")
        with open(hacs_json_path, 'r', encoding='utf-8') as f:
            hacs_config = json.load(f)
            print(f"   - Name: {hacs_config.get('name')}")
            print(f"   - Frontend: {hacs_config.get('frontend', False)}")
            print(f"   - Filename: {hacs_config.get('filename', 'N/A')}")
            print(f"   - Domains: {hacs_config.get('domains', [])}")
    else:
        print("❌ hacs.json nicht gefunden")
        return False
    
    # 2. Frontend-Datei prüfen
    frontend_files = []
    if hacs_config.get('frontend'):
        filename = hacs_config.get('filename', 'hassbeam-card.js')
        
        # Im Root-Verzeichnis (für HACS)
        root_file = root_path / filename
        if root_file.exists():
            frontend_files.append(f"Root: {filename}")
            print(f"✅ Frontend-Datei im Root gefunden: {filename}")
        
        # In dist/ (alternative Struktur)
        dist_file = root_path / "dist" / filename
        if dist_file.exists():
            frontend_files.append(f"dist/: {filename}")
            print(f"✅ Frontend-Datei in dist/ gefunden: {filename}")
        
        # In www/ (für manuelle Installation)
        www_file = root_path / "www" / filename
        if www_file.exists():
            frontend_files.append(f"www/: {filename}")
            print(f"✅ Frontend-Datei in www/ gefunden: {filename}")
    
    if not frontend_files:
        print("❌ Frontend-Datei nicht gefunden")
        return False
    
    # 3. Integration-Struktur prüfen
    integration_path = root_path / "custom_components" / "hassbeam_connect"
    if integration_path.exists():
        print("✅ Integration-Verzeichnis gefunden")
        
        # Manifest prüfen
        manifest_path = integration_path / "manifest.json"
        if manifest_path.exists():
            print("✅ manifest.json gefunden")
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                print(f"   - Domain: {manifest.get('domain')}")
                print(f"   - Version: {manifest.get('version')}")
                print(f"   - Config Flow: {manifest.get('config_flow', False)}")
                # Prüfen, dass KEIN frontend: true in manifest.json steht
                if 'frontend' not in manifest:
                    print("✅ Kein 'frontend' Flag in manifest.json (korrekt für HACS)")
                else:
                    print("⚠️  'frontend' Flag in manifest.json gefunden (könnte Konflikte verursachen)")
        else:
            print("❌ manifest.json nicht gefunden")
            return False
        
        # Wichtige Dateien prüfen
        required_files = ['__init__.py', 'const.py', 'config_flow.py']
        for file in required_files:
            if (integration_path / file).exists():
                print(f"✅ {file} gefunden")
            else:
                print(f"❌ {file} nicht gefunden")
    else:
        print("❌ Integration-Verzeichnis nicht gefunden")
        return False
    
    # 4. README und Dokumentation
    readme_files = ['README.md', 'info.md']
    for readme in readme_files:
        if (root_path / readme).exists():
            print(f"✅ {readme} gefunden")
    
    print("\n" + "=" * 60)
    print("🎉 HACS-Kompatibilitätstest abgeschlossen!")
    print("\n📋 Zusammenfassung:")
    print(f"   - Frontend-Dateien: {len(frontend_files)} gefunden")
    for file in frontend_files:
        print(f"     * {file}")
    
    print("\n🚀 Installation mit HACS:")
    print("   1. Repository zu HACS hinzufügen")
    print("   2. 'Hassbeam Connect' installieren")
    print("   3. Home Assistant neustarten")
    print("   4. Integration über UI hinzufügen")
    print("   5. Karte verwenden: type: custom:hassbeam-connect-card")
    
    print("\n💡 Nach HACS-Installation sollte die Ressource automatisch unter verfügbar sein:")
    print("   /hacsfiles/hassbeam-connect/hassbeam-card.js")
    
    return True

if __name__ == "__main__":
    test_hacs_structure()
