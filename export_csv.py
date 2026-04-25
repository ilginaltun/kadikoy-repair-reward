import sqlite3, csv, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'repair_hub.db')

if not os.path.exists(DB_PATH):
    print("repair_hub.db bulunamadi! Once Flask sunucusunu calistirip giris yapilmasi gerekiyor.")
    exit()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

users = conn.execute("SELECT id, email, role, created_at FROM users ORDER BY created_at").fetchall()
with open('kullanicilar.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['ID', 'Email', 'Rol', 'Kayit Tarihi'])
    for u in users:
        w.writerow([u['id'], u['email'], u['role'], u['created_at']])

convs = conn.execute(
    "SELECT id, user_email, user_role, sender, message, created_at FROM conversations ORDER BY created_at"
).fetchall()
with open('konusmalar.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['ID', 'Email', 'Rol', 'Gonderen', 'Mesaj', 'Tarih'])
    for c in convs:
        w.writerow([c['id'], c['user_email'], c['user_role'], c['sender'], c['message'], c['created_at']])

conn.close()
print(f"Tamamlandi: {len(users)} kullanici, {len(convs)} konusma mesaji")
print("Dosyalar: kullanicilar.csv, konusmalar.csv")
