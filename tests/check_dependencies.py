"""
Script to verify all required dependencies are installed and accessible.
"""
import sys
import pkg_resources

def check_package(package_name: str) -> tuple[bool, str]:
    """Check if a package is installed and return its version."""
    try:
        package = pkg_resources.working_set.by_key[package_name]
        return True, f"✅ {package_name} ({package.version})"
    except KeyError:
        return False, f"❌ {package_name} is not installed"

def main():
    """Main function to check all dependencies."""
    packages = [
        'fastapi',
        'uvicorn',
        'python-dotenv',
        'pydantic',
        'woocommerce',
        'requests',
        'openai',
        'langchain',
        'sqlalchemy',
        'alembic',
        'python-telegram-bot',
        'pytest',
        'black',
        'flake8',
        'mypy'
    ]

    print("Checking installed packages...")
    print("-" * 50)
    
    all_good = True
    for package in packages:
        success, message = check_package(package)
        print(message)
        if not success:
            all_good = False
    
    print("-" * 50)
    if all_good:
        print("✅ All packages are installed successfully!")
        sys.exit(0)
    else:
        print("❌ Some packages are missing or have issues.")
        sys.exit(1)

if __name__ == "__main__":
    main() 