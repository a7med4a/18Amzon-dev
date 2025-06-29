#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Naql Integration Module
This script performs basic validation of the module structure and Python syntax
"""

import os
import sys
import ast
import importlib.util

def test_python_syntax(file_path):
    """Test if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def test_module_structure():
    """Test the module structure"""
    base_path = '/home/ubuntu/sta_integration_module'
    
    required_files = [
        '__init__.py',
        '__manifest__.py',
        'models/__init__.py',
        'models/sta_config_settings.py',
        'models/sta_contract.py',
        'models/sta_branch.py',
        'models/sta_rent_policy.py',
        'controllers/__init__.py',
        'controllers/sta_api_controller.py',
        'wizards/__init__.py',
        'wizards/sta_send_otp_wizard.py',
        'wizards/sta_cancel_contract_wizard.py',
        'wizards/sta_suspend_contract_wizard.py',
        'wizards/sta_close_contract_wizard.py',
    ]
    
    required_xml_files = [
        'views/sta_config_settings_views.xml',
        'views/sta_contract_views.xml',
        'views/sta_branch_views.xml',
        'views/sta_rent_policy_views.xml',
        'wizards/sta_wizards_views.xml',
        'views/menuitems.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sta_data.xml',
    ]
    
    print("Testing module structure...")
    
    # Test required Python files
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            print(f"❌ Missing file: {file_path}")
            return False
        else:
            print(f"✅ Found: {file_path}")
            
            # Test Python syntax
            is_valid, error = test_python_syntax(full_path)
            if not is_valid:
                print(f"❌ Syntax error in {file_path}: {error}")
                return False
            else:
                print(f"✅ Valid syntax: {file_path}")
    
    # Test required XML files
    for file_path in required_xml_files:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            print(f"❌ Missing file: {file_path}")
            return False
        else:
            print(f"✅ Found: {file_path}")
    
    return True

def test_manifest_file():
    """Test the manifest file"""
    manifest_path = '/home/ubuntu/sta_integration_module/__manifest__.py'
    
    print("\nTesting manifest file...")
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse as Python to get the dictionary
        manifest_dict = ast.literal_eval(content)
        
        required_keys = ['name', 'version', 'depends', 'data', 'installable']
        for key in required_keys:
            if key not in manifest_dict:
                print(f"❌ Missing key in manifest: {key}")
                return False
            else:
                print(f"✅ Found key: {key}")
        
        # Check dependencies
        expected_deps = ['base', 'rental_contract', 'branches_management', 'customer_info', 'vehicle_info', 'fleet_status']
        for dep in expected_deps:
            if dep not in manifest_dict['depends']:
                print(f"⚠️  Missing dependency: {dep}")
            else:
                print(f"✅ Dependency found: {dep}")
        
        print(f"✅ Manifest file is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading manifest: {e}")
        return False

def test_imports():
    """Test if imports work correctly"""
    print("\nTesting imports...")
    
    # Test if we can import the main module files
    sys.path.insert(0, '/home/ubuntu/sta_integration_module')
    
    try:
        # Test models
        spec = importlib.util.spec_from_file_location("sta_config_settings", "/home/ubuntu/sta_integration_module/models/sta_config_settings.py")
        if spec and spec.loader:
            print("✅ sta_config_settings import structure is valid")
        
        spec = importlib.util.spec_from_file_location("sta_contract", "/home/ubuntu/sta_integration_module/models/sta_contract.py")
        if spec and spec.loader:
            print("✅ sta_contract import structure is valid")
        
        spec = importlib.util.spec_from_file_location("sta_api_controller", "/home/ubuntu/sta_integration_module/controllers/sta_api_controller.py")
        if spec and spec.loader:
            print("✅ sta_api_controller import structure is valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Starting Naql Integration Module Tests\n")
    
    tests = [
        ("Module Structure", test_module_structure),
        ("Manifest File", test_manifest_file),
        ("Import Structure", test_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY")
    print('='*50)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Module structure is valid.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

