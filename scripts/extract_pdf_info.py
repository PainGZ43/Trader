import sys
import os
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def extract_text_from_pdf(pdf_path):
    print(f"Attempting to read: {pdf_path}")
    
    try:
        import PyPDF2
        print("Using PyPDF2...")
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except ImportError:
        print("PyPDF2 import failed.")
        return ""
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def search_keywords(text, keywords):
    results = {}
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                # Capture context (10 lines before and 20 lines after to get full table/spec)
                start = max(0, i - 10)
                end = min(len(lines), i + 30)
                context = "\n".join(lines[start:end])
                if kw not in results:
                    results[kw] = []
                results[kw].append(context)
    return results

if __name__ == "__main__":
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "키움 REST API 문서.pdf"))
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)
        
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Failed to extract text.")
        sys.exit(1)
        
    print(f"Extracted {len(text)} characters.")
    
    # Search for opw00018 and related keywords
    keywords = ["opw00018", "계좌평가잔고내역요청", "balance"]
    results = search_keywords(text, keywords)
    
    for kw, contexts in results.items():
        print(f"\n--- Matches for '{kw}' ---")
        for ctx in contexts[:3]: # Show top 3 matches
            print(f"...\n{ctx}\n...")
