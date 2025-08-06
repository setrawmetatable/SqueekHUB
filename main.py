# at the top
import requests
import time
import os
from flask import Flask
from threading import Thread

# fake web server to keep Render happy
app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# now your original code follows
print("Starting bio monitor...")

ROBLOSECURITY = os.getenv("ROBLOSECURITY")
if not ROBLOSECURITY:
    print("ROBLOSECURITY is missing!")
    exit()
    
desired_bio = "set owns my soft kiffy"

session = requests.Session()
session.cookies.set(".ROBLOSECURITY", ROBLOSECURITY, domain=".roblox.com")
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
})

def get_user_id():
    res = session.get("https://users.roblox.com/v1/users/authenticated")
    if res.status_code == 200:
        return res.json()["id"]
    else:
        print("Failed to authenticate.")
        print(res.text)
        exit()

user_id = get_user_id()

def get_bio():
    res = session.get(f"https://users.roblox.com/v1/users/{user_id}")
    if res.status_code == 200:
        return res.json().get("description", "")
    else:
        print("Failed to get bio:", res.text)
        return ""

def try_set_bio(new_bio):
    # Attempt to update bio (initial attempt without CSRF token)
    res = session.post("https://users.roblox.com/v1/description", json={"description": new_bio})

    if res.status_code == 200:
        print("Bio updated successfully.")
        return True

    if res.status_code == 403:
        csrf_token = res.headers.get("x-csrf-token")
        if not csrf_token:
            print("Failed to get CSRF token. Likely logged out.")
            return False

        # Retry with new CSRF token
        session.headers["X-CSRF-Token"] = csrf_token
        print("Retrying with new CSRF token...")
        retry = session.post("https://users.roblox.com/v1/description", json={"description": new_bio})
        if retry.status_code == 200:
            print("Bio updated successfully after retry.")
            return True
        else:
            print("Failed to update bio on retry.")
            print(retry.status_code, retry.text)
            return False
    else:
        print("Unexpected error updating bio:", res.status_code)
        print(res.text)
        return False

# Main loop
print("Starting bio monitor...")
laststatus = False
while True:
    try:
        current_bio = get_bio()
        print("Current bio:", current_bio)
        
        if current_bio.strip() != desired_bio:
            laststatus = False
            print("Bio doesn't match. Fixing...")
            success = try_set_bio(desired_bio)
            if not success:
                print("Bio update failed. Retrying in 2 minutes...")
                time.sleep(120)
                continue
        elif laststatus == False:
            laststatus = True
            print("Bio is correct.")

        time.sleep(3)
    except Exception as e:
        print("Error in loop:", e)
        time.sleep(10)

