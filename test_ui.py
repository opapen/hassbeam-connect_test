#!/usr/bin/env python3
"""
Test script for Hassbeam Connect UI functionality.
This script helps verify that the database and service functionality works correctly.
"""

import sys
import os
import json
import sqlite3
from datetime import datetime

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'hassbeam_connect'))

try:
    from database import init_db, save_ir_code, get_ir_codes
    from const import DB_NAME
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def test_database_functionality():
    """Test the database functionality"""
    print("🧪 Testing Hassbeam Connect Database Functionality")
    print("=" * 50)
    
    # Test database path
    db_path = "test_" + DB_NAME
    
    try:
        # Test 1: Database initialization
        print("1. Testing database initialization...")
        init_db(db_path)
        print("   ✅ Database initialized successfully")
        
        # Test 2: Save IR codes
        print("2. Testing IR code saving...")
        test_codes = [
            {
                "device": "tv",
                "action": "power",
                "event_data": {
                    "raw_data": [1000, 500, 1000, 500, 500, 1000],
                    "protocol": "NEC"
                }
            },
            {
                "device": "tv", 
                "action": "volume_up",
                "event_data": {
                    "raw_data": [1000, 500, 500, 1000, 1000, 500],
                    "protocol": "NEC"
                }
            },
            {
                "device": "soundbar",
                "action": "power", 
                "event_data": {
                    "raw_data": [2000, 1000, 2000, 1000, 1000, 2000],
                    "protocol": "Samsung"
                }
            }
        ]
        
        for code in test_codes:
            save_ir_code(db_path, code["device"], code["action"], code["event_data"])
            print(f"   ✅ Saved: {code['device']}.{code['action']}")
        
        # Test 3: Retrieve all codes
        print("3. Testing code retrieval...")
        all_codes = get_ir_codes(db_path)
        print(f"   ✅ Retrieved {len(all_codes)} codes total")
        
        # Test 4: Retrieve codes by device
        print("4. Testing device-specific retrieval...")
        tv_codes = get_ir_codes(db_path, "tv")
        print(f"   ✅ Retrieved {len(tv_codes)} codes for TV")
        
        # Test 5: Retrieve with limit
        print("5. Testing limited retrieval...")
        limited_codes = get_ir_codes(db_path, limit=2)
        print(f"   ✅ Retrieved {len(limited_codes)} codes with limit=2")
        
        # Display results
        print("\n📋 Database Contents:")
        print("-" * 50)
        for code in all_codes:
            created_at = code[4] if len(code) > 4 else "Unknown"
            event_data = json.loads(code[3])
            protocol = event_data.get("protocol", "Unknown")
            print(f"   {code[1]}.{code[2]} ({protocol}) - {created_at}")
        
        print(f"\n✅ All tests passed! Database: {db_path}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup test database
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🧹 Cleaned up test database: {db_path}")
    
    return True


def test_ui_files():
    """Test if UI files exist and are valid"""
    print("\n🖥️  Testing UI Files")
    print("=" * 50)
    
    files_to_check = [
        ("www/hassbeam-card.js", "Frontend card"),
        ("UI_INSTALLATION.md", "Installation guide"),
        ("ui-demo.html", "Demo page")
    ]
    
    all_good = True
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {description}: {file_path} ({size} bytes)")
        else:
            print(f"   ❌ Missing: {file_path}")
            all_good = False
    
    # Check if the JavaScript file contains expected functions
    js_file = "www/hassbeam-card.js"
    if os.path.exists(js_file):
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_elements = [
            "class HassbeamConnectCard",
            "startListening",
            "onCodeSaved",
            "loadRecentCodes",
            "customElements.define"
        ]
        
        for element in required_elements:
            if element in content:
                print(f"   ✅ Found: {element}")
            else:
                print(f"   ❌ Missing: {element}")
                all_good = False
    
    return all_good


def simulate_ui_workflow():
    """Simulate the UI workflow"""
    print("\n🎭 Simulating UI Workflow")
    print("=" * 50)
    
    print("1. User opens Hassbeam Connect card")
    print("2. User enters device: 'tv' and action: 'power'")
    print("3. User clicks 'IR-Code aufnehmen'")
    print("4. System calls: hassbeam_connect.start_listening")
    print("5. User points remote and presses button")
    print("6. HassBeam device sends event: esphome.hassbeam.ir_received")
    print("7. System saves IR code to database")
    print("8. System fires event: hassbeam_connect_saved")
    print("9. UI shows success message and updates recent codes")
    print("10. User can see the new code in 'Zuletzt aufgenommene Codes'")
    
    print("\n✅ UI workflow simulation completed")


def main():
    """Main test function"""
    print("🎯 Hassbeam Connect - UI Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = True
    
    # Test database functionality
    if not test_database_functionality():
        success = False
    
    # Test UI files
    if not test_ui_files():
        success = False
    
    # Simulate workflow
    simulate_ui_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Your Hassbeam Connect UI is ready!")
        print("\n📝 Next steps:")
        print("1. Copy files to your Home Assistant installation")
        print("2. Follow the UI_INSTALLATION.md guide")
        print("3. Add the integration in Home Assistant")
        print("4. Register the frontend resource")
        print("5. Add the card to your dashboard")
        print("6. Start capturing IR codes!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
