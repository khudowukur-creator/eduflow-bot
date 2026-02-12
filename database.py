import sqlite3

def create_db():
    conn = sqlite3.connect('eduflow.db')
    cursor = conn.cursor()
    
    # Kurslar jadvalini yaratish
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            description TEXT
        )
    ''')
    
    # Namuna uchun kurs qo'shish
    cursor.execute("INSERT OR IGNORE INTO courses (id, name, price, description) VALUES (1, 'Gitara darslari', 100000, 'Noldan mohir chalishgacha')")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_db()