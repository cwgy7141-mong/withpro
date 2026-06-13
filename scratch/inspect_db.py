import sqlite3

def inspect():
    conn = sqlite3.connect('withpro.db')
    c = conn.cursor()
    
    # List all tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in c.fetchall()]
    print("Tables:", tables)
    
    for table in tables:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        print(f"Table '{table}': {count} rows")
        
        # Print first few rows of each table
        c.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = c.fetchall()
        print(f"  Sample rows in '{table}':")
        for r in rows:
            print("   ", r)
            
    conn.close()

if __name__ == '__main__':
    inspect()
