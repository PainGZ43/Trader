import os

def debug_env():
    if os.path.exists(".env"):
        with open(".env", "rb") as f:
            content = f.read()
            print(f"Content (bytes): {content}")
            try:
                print(f"Content (utf-8): {content.decode('utf-8')}")
            except:
                print("Content is NOT valid utf-8")
                try:
                    print(f"Content (utf-16): {content.decode('utf-16')}")
                except:
                    print("Content is NOT valid utf-16")
    else:
        print(".env does not exist")

if __name__ == "__main__":
    debug_env()
