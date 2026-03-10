"""
Check messages, chats, chat_participants, and other tables in the DB.
Run from Backend folder: python check_messages_and_tables.py
"""
import database

def row_factory(cursor, row):
    return dict(zip([col[0] for col in cursor.description], row))

def run():
    conn = database.get_connection()
    conn.row_factory = row_factory

    # --- Users ---
    rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    print(f"\n=== Users ({len(rows)}) ===")
    for r in rows:
        print(f"  id={r['id']} | {r['name']} | {r['email']} | {r['role']}")

    # --- Chats ---
    rows = conn.execute("SELECT * FROM chats ORDER BY id").fetchall()
    print(f"\n=== Chats ({len(rows)}) ===")
    for r in rows:
        print(f"  id={r['id']} | type={r['type']} | name={r['name']} | created_at={r.get('created_at')}")

    # --- Chat participants ---
    rows = conn.execute("SELECT * FROM chat_participants ORDER BY chat_id, user_id").fetchall()
    print(f"\n=== Chat participants ({len(rows)}) ===")
    for r in rows:
        print(f"  chat_id={r['chat_id']} | user_id={r['user_id']}")

    # --- Messages ---
    rows = conn.execute("SELECT * FROM messages ORDER BY chat_id, id").fetchall()
    print(f"\n=== Messages ({len(rows)}) ===")
    for r in rows:
        body = r['body'] or ''
        body_short = (body[:50] + '...') if len(body) > 50 else body
        print(f"  id={r['id']} | chat_id={r['chat_id']} | sender_id={r['sender_id']} | body={body_short!r} | created_at={r.get('created_at')}")


    conn.close()
    print()

if __name__ == "__main__":
    run()
