# Script to merge methods into main_window.py properly
with open('ui/main_window.py', 'r', encoding='utf-8', errors='ignore') as f:
    main_content = f.read()

with open('ui/missing_methods.py', 'r', encoding='utf-8') as f:
    missing_methods = f.read()

# Ensure no null bytes
main_content = main_content.replace('\x00', '')
missing_methods = missing_methods.replace('\x00', '')

# Merge
full_content = main_content + '\n' + missing_methods

# Write
with open('ui/main_window.py', 'w', encoding='utf-8') as f:
    f.write(full_content)

print("Successfully merged methods into main_window.py")
