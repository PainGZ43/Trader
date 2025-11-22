# Fix main_window.py corruption
import codecs

# Read the file and find where corruption starts
with open('ui/main_window.py', 'rb') as f:
    content = f.read()

# Find the last valid line before corruption
# Looking for line 1251 (last valid line before corruption)
try:
    decoded = content.decode('utf-8')
    lines = decoded.split('\n')
except:
    # If decoding fails, try to find the corruption point
    valid_bytes = b''
    for i, byte in enumerate(content):
        try:
            (valid_bytes + bytes([byte])).decode('utf-8')
            valid_bytes += bytes([byte])
        except:
            print(f"Corruption found at byte {i}")
            break
    decoded = valid_bytes.decode('utf-8')
    lines = decoded.split('\n')

# Write clean file with new methods
with open('ui/main_window.py', 'w', encoding='utf-8') as f:
    # Write all lines up to 1251
    f.write('\n'.join(lines[:1251]))
    
    # Add the missing methods
    f.write('''

    def cancel_training(self):
        """Cancel AI training"""
        self.training_cancel_flag = True
        self.train_stop_btn.setEnabled(False)
        self.train_result_text.append("\\nStop training...\\n")
        self.log("AI Training cancel requested")
    
    def _finish_training(self, success):
        """Restore UI after training completion"""
        self.train_start_btn.setEnabled(True)
        self.train_stop_btn.setEnabled(False)
        if not success:
            self.train_progress.setVisible(False)
''')

print("File repaired successfully")
