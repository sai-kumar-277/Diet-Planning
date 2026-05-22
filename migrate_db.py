import sqlite3

def upgrade():
    print("Connecting to database...")
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE health ADD COLUMN avoid_foods TEXT DEFAULT ''")
        print("Successfully added avoid_foods column to health table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column already exists.")
        else:
            print("Error altering table:", e)
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    upgrade()
