import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.key_manager import key_manager

def main():
    print("Cleaning up duplicate keys...")
    count = key_manager.cleanup_duplicates()
    print(f"Removed {count} duplicate keys.")
    
    print("Remaining keys:")
    for k in key_manager.get_keys():
        print(f"- {k['owner']} ({k['type']})")

if __name__ == "__main__":
    main()
