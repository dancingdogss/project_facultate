import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create a table to store deposit addresses
cursor.execute('''
    CREATE TABLE IF NOT EXISTS deposit_addresses
    (user_id TEXT, deposit_address TEXT)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()