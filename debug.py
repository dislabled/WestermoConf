#!/usr/bin/env python3
"""Comprehensive debugging for Westermo scrapli_community setup"""

import os
import sys
import subprocess
import importlib.util

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_virtual_env():
    """Check if we're in a virtual environment"""
    print("🔍 Virtual Environment Check:")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"✅ In virtual environment: {sys.prefix}")
        return True
    else:
        print("⚠️  Not in virtual environment (or system Python)")
        return False

def check_pip_installation():
    """Check if our package is installed"""
    print("\n📦 Package Installation Check:")
    
    # Check pip list
    code, stdout, stderr = run_command("pip list | grep westermo")
    if code == 0 and stdout.strip():
        print(f"✅ Package found in pip list:\n{stdout}")
    else:
        print("❌ Package not found in pip list")
        
        # Show all packages for debugging
        code, stdout, stderr = run_command("pip list")
        print("📋 All installed packages:")
        print(stdout[:500] + "..." if len(stdout) > 500 else stdout)
    
    # Check pip show
    code, stdout, stderr = run_command("pip show westermo-configurator")
    if code == 0:
        print(f"✅ Package details:\n{stdout}")
    else:
        print("❌ Package details not found")

def check_python_path():
    """Check Python path and module locations"""
    print(f"\n🐍 Python Path Check:")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    print("\nPython sys.path (first 5 entries):")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}: {path}")

def check_file_structure():
    """Check if files exist in the right places"""
    print(f"\n📁 File Structure Check:")
    
    files_to_check = [
        "pyproject.toml",
        "scrapli_community/__init__.py",
        "scrapli_community/westermo/__init__.py", 
        "scrapli_community/westermo/weos/__init__.py",
        "scrapli_community/westermo/weos/westermo_weos.py",
        "scrapli_community/westermo/weos/sync_driver.py",
        "scrapli_community/westermo/weos/async_driver.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} - MISSING")

def check_imports_step_by_step():
    """Test imports step by step"""
    print(f"\n🧪 Import Testing:")
    
    # Test basic scrapli first
    try:
        import scrapli
        print(f"✅ scrapli imported successfully (version: {getattr(scrapli, '__version__', 'unknown')})")
    except ImportError as e:
        print(f"❌ Failed to import scrapli: {e}")
        return False
    
    try:
        import scrapli_community
        print(f"✅ scrapli_community imported successfully")
        print(f"   scrapli_community location: {scrapli_community.__file__ if hasattr(scrapli_community, '__file__') else 'unknown'}")
    except ImportError as e:
        print(f"❌ Failed to import scrapli_community: {e}")
        return False
    
    # Test if our custom module is found
    try:
        import scrapli_community.westermo
        print(f"✅ scrapli_community.westermo imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import scrapli_community.westermo: {e}")
        return False
    
    try:
        import scrapli_community.westermo.weos
        print(f"✅ scrapli_community.westermo.weos imported successfully")
        
        if hasattr(scrapli_community.westermo.weos, 'SCRAPLI_PLATFORM'):
            print(f"✅ SCRAPLI_PLATFORM found in module")
            platform = scrapli_community.westermo.weos.SCRAPLI_PLATFORM
            print(f"   Platform type: {platform.get('driver_type', 'unknown')}")
        else:
            print(f"❌ SCRAPLI_PLATFORM not found in module")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import scrapli_community.westermo.weos: {e}")
        return False
    
    return True

def test_scrapli_factory():
    """Test if Scrapli can find our platform"""
    print(f"\n🏭 Scrapli Factory Test:")
    
    try:
        from scrapli import Scrapli
        
        # Test configuration (without actually connecting)
        test_config = {
            "host": "127.0.0.1",
            "port": 2323,
            "auth_username": "admin",
            "auth_password": "test",
            "platform": "westermo_weos",
            "transport": "telnet"
        }
        
        print("Testing if Scrapli factory can find westermo_weos platform...")
        
        # This will test if the platform can be found without actually connecting
        try:
            conn = Scrapli(**test_config)
            print("✅ Scrapli factory successfully found westermo_weos platform!")
            return True
        except Exception as e:
            if "Module not found" in str(e) or "not found" in str(e):
                print(f"❌ Scrapli factory can't find westermo_weos platform: {e}")
                return False
            else:
                print(f"✅ Platform found (connection error expected): {e}")
                return True
                
    except Exception as e:
        print(f"❌ Error testing Scrapli factory: {e}")
        return False

def main():
    print("🔍 COMPREHENSIVE WESTERMO SCRAPLI DEBUG")
    print("=" * 50)
    
    # Run all checks
    venv_ok = check_virtual_env()
    check_pip_installation()
    check_python_path()
    check_file_structure()
    imports_ok = check_imports_step_by_step()
    factory_ok = test_scrapli_factory()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"Virtual Environment: {'✅' if venv_ok else '⚠️'}")
    print(f"Imports Working: {'✅' if imports_ok else '❌'}")
    print(f"Scrapli Factory: {'✅' if factory_ok else '❌'}")
    
    if not imports_ok:
        print("\n💡 RECOMMENDED ACTIONS:")
        print("1. Make sure you're in your virtual environment")
        print("2. Try: pip uninstall westermo-configurator")
        print("3. Try: pip install -e . --force-reinstall")
        print("4. Check that pyproject.toml is in the project root")
        
    elif not factory_ok:
        print("\n💡 Platform imports work but Scrapli can't find it.")
        print("This might be a registration issue with scrapli_community.")

if __name__ == "__main__":
    main()
