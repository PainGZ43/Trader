import pypdf
import os
import sys

# Set encoding for output
sys.stdout.reconfigure(encoding='utf-8')

DOC_PATH = r"e:\GitHub\Trader\PainTrader\docs\키움 REST API 문서.pdf"

def search_pdf():
    print(f"Reading PDF: {DOC_PATH}")
    try:
        reader = pypdf.PdfReader(DOC_PATH)
        print(f"Total Pages: {len(reader.pages)}")
        
        found_count = 0
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            
            if "kt10000" in text:
                print(f"\n--- Page {i+1} (Stock Buy Order) ---")
                print(text)
                found_count += 1
                continue
                    
        if found_count == 0:
            print("No relevant info found in PDF.")
            
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    search_pdf()
