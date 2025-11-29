import os

def clean_env():
    if os.path.exists(".env"):
        with open(".env", "rb") as f:
            content = f.read()
        
        # Remove null bytes (fix UTF-16 artifacts)
        clean_content = content.replace(b'\x00', b'')
        
        # Write back
        with open(".env", "wb") as f:
            f.write(clean_content)
            
        print("Cleaned .env file.")
    else:
        print(".env does not exist")

if __name__ == "__main__":
    clean_env()
