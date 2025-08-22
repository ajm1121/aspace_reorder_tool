#!/usr/bin/env python3
"""
Setup script for ArchivesSpace Reorder Tool
Helps configure the environment and check dependencies.
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required Python packages are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        'requests',
        'pandas', 
        'openpyxl',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them using:")
        print("pip install -r requirements.txt")
        return False
    
    print("✓ All dependencies are installed!")
    return True

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    if os.path.exists('.env'):
        print("✓ .env file already exists")
        return True
    
    if not os.path.exists('env.example'):
        print("✗ env.example file not found")
        return False
    
    print("Creating .env file from template...")
    
    try:
        with open('env.example', 'r') as f:
            template = f.read()
        
        with open('.env', 'w') as f:
            f.write(template)
        
        print("✓ .env file created successfully")
        print("⚠️  IMPORTANT: Please edit the .env file with your ArchivesSpace credentials")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create .env file: {e}")
        return False

def check_excel_file():
    """Check if the sample Excel file exists."""
    excel_path = Path("01_reorder_tool/in/input_sample.xlsx")
    
    if excel_path.exists():
        print(f"✓ Excel file found: {excel_path}")
        return True
    else:
        print(f"✗ Excel file not found: {excel_path}")
        print("Please ensure input_sample.xlsx exists in the 01_reorder_tool/in/ directory")
        return False

def main():
    """Main setup function."""
    print("=" * 50)
    print("ArchivesSpace Reorder Tool Setup")
    print("=" * 50)
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Create .env file
    env_ok = create_env_file()
    
    # Check Excel file
    excel_ok = check_excel_file()
    
    print("\n" + "=" * 50)
    print("Setup Summary")
    print("=" * 50)
    
    if deps_ok and env_ok and excel_ok:
        print("✅ Setup complete! You can now run the tool.")
        print("\nNext steps:")
        print("1. Edit the .env file with your ArchivesSpace credentials")
        print("2. Run: python reorder_tool.py")
    else:
        print("❌ Setup incomplete. Please address the issues above.")
        
        if not deps_ok:
            print("\nTo install dependencies:")
            print("pip install -r requirements.txt")
        
        if not env_ok:
            print("\nTo create .env file manually:")
            print("cp env.example .env")
            print("Then edit .env with your credentials")
        
        if not excel_ok:
            print("\nTo prepare Excel file:")
            print("1. Export your ArchivesSpace container list to Excel")
            print("2. Save as 'input_sample.xlsx' in '01_reorder_tool/in/' directory")

if __name__ == "__main__":
    main()
