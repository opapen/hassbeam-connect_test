#!/usr/bin/env python3
"""
Test script for Hassbeam Connect database functionality
Run this script to test database operations independently
"""

import sqlite3
import json
import os
import sys

# Add the custom component path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'hassbeam_connect'))

from database import init_db, save_ir_code

def test_database_functionality():
    """Test database initialization and IR code saving"""
    test_db_path = "test_hassbeam.db"
    
    print("🧪 Testing Hassbeam Connect Database Functionality")
    print("=" * 50)
    
    try:
        # Clean up any existing test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
        # Test 1: Database initialization
        print("📁 Test 1: Database Initialization")
        init_db(test_db_path)
        
        if os.path.exists(test_db_path):
            print("✅ Database file created successfully")
        else:
            print("❌ Database file was not created")
            return False
            
        # Test 2: Verify table structure
        print("\n🏗️  Test 2: Table Structure Verification")
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if ('ir_codes',) in tables:
            print("✅ ir_codes table exists")
        else:
            print("❌ ir_codes table not found")
            conn.close()
            return False
            
        # Check table schema
        cursor.execute("PRAGMA table_info(ir_codes);")
        columns = cursor.fetchall()
        expected_columns = ['id', 'device', 'action', 'event_data']
        actual_columns = [col[1] for col in columns]
        
        if all(col in actual_columns for col in expected_columns):
            print("✅ Table schema is correct")
        else:
            print(f"❌ Table schema mismatch. Expected: {expected_columns}, Got: {actual_columns}")
            conn.close()
            return False
            
        conn.close()
        
        # Test 3: Save IR code
        print("\n💾 Test 3: IR Code Saving")
        test_event_data = {
            "protocol": "NEC",
            "data": "0x12345678",
            "command": "0x56",
            "address": "0x1234"
        }
        
        save_ir_code(test_db_path, "test_tv", "power", test_event_data)
        print("✅ IR code saved successfully")
        
        # Test 4: Verify saved data
        print("\n🔍 Test 4: Data Verification")
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ir_codes WHERE device='test_tv' AND action='power';")
        result = cursor.fetchone()
        
        if result:
            saved_event_data = json.loads(result[3])
            if saved_event_data == test_event_data:
                print("✅ Saved data matches expected data")
                print(f"   Device: {result[1]}")
                print(f"   Action: {result[2]}")
                print(f"   Event Data: {saved_event_data}")
            else:
                print("❌ Saved data does not match expected data")
                conn.close()
                return False
        else:
            print("❌ No data found in database")
            conn.close()
            return False
            
        conn.close()
        
        # Test 5: Multiple entries
        print("\n📊 Test 5: Multiple Entries")
        test_entries = [
            ("test_tv", "volume_up", {"protocol": "NEC", "data": "0x11111111"}),
            ("test_tv", "volume_down", {"protocol": "NEC", "data": "0x22222222"}),
            ("test_ac", "power", {"protocol": "RC5", "data": "0x33333333"})
        ]
        
        for device, action, event_data in test_entries:
            save_ir_code(test_db_path, device, action, event_data)
            
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ir_codes;")
        count = cursor.fetchone()[0]
        conn.close()
        
        expected_count = len(test_entries) + 1  # +1 for the first test entry
        if count == expected_count:
            print(f"✅ All {expected_count} entries saved correctly")
        else:
            print(f"❌ Expected {expected_count} entries, found {count}")
            return False
            
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
        
    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print(f"\n🧹 Cleaned up test database: {test_db_path}")

def test_event_simulation():
    """Simulate the event flow that would happen in Home Assistant"""
    print("\n🎭 Simulating Home Assistant Event Flow")
    print("=" * 50)
    
    # This simulates what happens when the service is called and an IR event is received
    print("1. 📞 Service 'start_listening' called with device='TV', action='power'")
    pending_state = {"device": "TV", "action": "power"}
    print(f"   Pending state set: {pending_state}")
    
    print("\n2. 📡 IR event received from ESPHome")
    mock_ir_event = {
        "protocol": "NEC",
        "data": "0x20DF10EF",
        "command": "0x10",
        "address": "0x04"
    }
    print(f"   Event data: {mock_ir_event}")
    
    print("\n3. 💾 Processing and saving to database")
    test_db_path = "test_flow.db"
    
    try:
        init_db(test_db_path)
        save_ir_code(test_db_path, pending_state["device"], pending_state["action"], mock_ir_event)
        
        print("✅ IR code saved successfully")
        print(f"4. 🔔 Event 'hassbeam_connect_saved' would be fired")
        print(f"   Event data: {{'device': '{pending_state['device']}', 'action': '{pending_state['action']}'}}")
        
        # Verify the save
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ir_codes ORDER BY id DESC LIMIT 1;")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"\n📋 Database entry created:")
            print(f"   ID: {result[0]}")
            print(f"   Device: {result[1]}")
            print(f"   Action: {result[2]}")
            print(f"   Event Data: {json.loads(result[3])}")
            
        return True
        
    except Exception as e:
        print(f"❌ Flow simulation failed: {str(e)}")
        return False
        
    finally:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

if __name__ == "__main__":
    print("🏠 Hassbeam Connect - Test Suite")
    print("================================\n")
    
    success = test_database_functionality()
    if success:
        test_event_simulation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("1. Install this integration in Home Assistant")
        print("2. Set up your HassBeam ESPHome device")
        print("3. Add the Lovelace card to your dashboard")
        print("4. Test with real IR remote controls")
    else:
        print("❌ Some tests failed. Please check the implementation.")
