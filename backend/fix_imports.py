#!/usr/bin/env python3
"""
Fix import issues and ensure all dependencies are properly installed
"""
import sys
import subprocess
import os

def check_uagents_import():
    """Check if uagents can be imported correctly"""
    print("🔍 Checking uagents import...")

    try:
        import uagents
        print(f"✅ uagents version: {uagents.__version__}")

        # Try importing specific modules
        try:
            from uagents.crypto import Identity
            print("✅ uagents.crypto.Identity imported successfully")
        except ImportError as e:
            print(f"❌ uagents.crypto.Identity import failed: {e}")

        try:
            from uagents.communication import query
            print("✅ uagents.communication.query imported successfully")
        except ImportError as e:
            print(f"❌ uagents.communication.query import failed: {e}")

    except ImportError as e:
        print(f"❌ uagents import failed: {e}")
        return False

    return True

def check_uagents_core_import():
    """Check if uagents_core can be imported"""
    print("\n🔍 Checking uagents_core import...")

    try:
        import uagents_core
        print(f"✅ uagents_core version: {uagents_core.__version__}")

        try:
            from uagents_core.crypto import Identity
            print("✅ uagents_core.crypto.Identity imported successfully")
        except ImportError as e:
            print(f"❌ uagents_core.crypto.Identity import failed: {e}")

        try:
            from uagents_core.communication import query
            print("✅ uagents_core.communication.query imported successfully")
        except ImportError as e:
            print(f"❌ uagents_core.communication.query import failed: {e}")

    except ImportError as e:
        print(f"❌ uagents_core import failed: {e}")
        return False

    return True

def test_multiagent_service():
    """Test if multiagent service can be imported and initialized"""
    print("\n🔍 Testing multiagent service import...")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        from app.services.multiagent_service import get_multiagent_service
        print("✅ Multiagent service imported successfully")

        # Try to get the service (this will test the dynamic imports)
        service = get_multiagent_service()
        if service:
            print("✅ Multiagent service instance created")
        else:
            print("⚠️ Multiagent service instance is None (fallback mode)")

        return True

    except Exception as e:
        print(f"❌ Multiagent service test failed: {e}")
        return False

def fix_requirements():
    """Ensure requirements.txt has the correct versions"""
    print("\n🔧 Checking requirements.txt...")

    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')

    try:
        with open(requirements_path, 'r') as f:
            content = f.read()

        # Check if uagents versions are specified
        if 'uagents==' not in content:
            print("⚠️ uagents version not specified in requirements.txt")
            print("📝 Adding specific versions...")

            # Update with specific versions
            updated_content = content.replace(
                'uagents\n',
                'uagents==0.22.10\n'
            ).replace(
                'uagents-core\n',
                'uagents-core==0.3.11\n'
            )

            with open(requirements_path, 'w') as f:
                f.write(updated_content)

            print("✅ Updated requirements.txt with specific versions")

        else:
            print("✅ requirements.txt already has version specifications")

    except Exception as e:
        print(f"❌ Error updating requirements.txt: {e}")

def install_dependencies():
    """Install/update dependencies"""
    print("\n📦 Installing dependencies...")

    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])

        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

        print("✅ Dependencies installed successfully")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

    return True

def main():
    """Main fix function"""
    print("🔧 ChatRealm Multi-Agent System Import Fixer")
    print("=" * 50)

    # Fix requirements first
    fix_requirements()

    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return

    # Check imports
    uagents_ok = check_uagents_import()
    uagents_core_ok = check_uagents_core_import()

    # Test multiagent service
    service_ok = test_multiagent_service()

    print("\n" + "=" * 50)
    print("📊 FIX SUMMARY")
    print("=" * 50)

    if uagents_ok and uagents_core_ok and service_ok:
        print("✅ ALL IMPORTS WORKING!")
        print("🎉 Multi-agent system is ready")
    elif uagents_ok or uagents_core_ok:
        print("⚠️ PARTIAL SUCCESS")
        print("📝 Basic uagents import works, but multiagent service may need fixes")
    else:
        print("❌ IMPORT ISSUES DETECTED")
        print("🔧 Check uagents installation and versions")

    print("\n💡 If issues persist:")
    print("1. Try: pip install --upgrade uagents uagents-core")
    print("2. Check: python -c 'import uagents; print(uagents.__version__)'")
    print("3. Verify: python -c 'from uagents.crypto import Identity'")

if __name__ == "__main__":
    main()
