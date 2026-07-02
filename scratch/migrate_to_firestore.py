import sqlite3
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

DB_NAME = "withpro.db"
SERVICE_ACCOUNT_PATH = "firebase-service-account.json"

def migrate():
    if not os.path.exists(DB_NAME):
        print(f"[-] SQLite database '{DB_NAME}' not found. Cannot migrate.")
        return
        
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(f"[-] Service account file '{SERVICE_ACCOUNT_PATH}' not found. Please place it in the project root to run this script.")
        return

    # Initialize Firebase Admin
    print("[*] Initializing Firebase Admin SDK...")
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Connect to SQLite
    print(f"[*] Connecting to SQLite database '{DB_NAME}'...")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Migrate regular_users
    print("\n[*] Migrating regular_users...")
    c.execute("SELECT * FROM regular_users")
    regular_users = c.fetchall()
    count_users = 0
    for row in regular_users:
        data = dict(row)
        doc_id = str(data.pop("id"))  # use numeric id as document ID string
        db.collection("regular_users").document(doc_id).set(data)
        count_users += 1
    print(f"[+] Migrated {count_users} regular_users.")

    # 2. Migrate pro_users
    print("\n[*] Migrating pro_users...")
    c.execute("SELECT * FROM pro_users")
    pro_users = c.fetchall()
    count_pros = 0
    for row in pro_users:
        data = dict(row)
        doc_id = str(data.pop("id"))
        db.collection("pro_users").document(doc_id).set(data)
        count_pros += 1
    print(f"[+] Migrated {count_pros} pro_users.")

    # 3. Migrate lesson_requests
    print("\n[*] Migrating lesson_requests...")
    c.execute("SELECT * FROM lesson_requests")
    lesson_requests = c.fetchall()
    count_lessons = 0
    for row in lesson_requests:
        data = dict(row)
        doc_id = str(data.pop("id"))
        
        # Convert matched_pro_id to string to match document ID if it exists
        if data.get("matched_pro_id") is not None:
            data["matched_pro_id"] = str(data["matched_pro_id"])
            
        db.collection("lesson_requests").document(doc_id).set(data)
        count_lessons += 1
    print(f"[+] Migrated {count_lessons} lesson_requests.")

    conn.close()
    print("\n[+] Migration completed successfully!")

if __name__ == "__main__":
    migrate()
