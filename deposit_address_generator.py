import sqlite3
import hashlib

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create the deposit_addresses table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS deposit_addresses
    (user_id TEXT, deposit_address TEXT)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

def generate_deposit_address(user_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Generate a new deposit address
    deposit_address = hashlib.sha256(str(user_id).encode()).hexdigest()

    # Insert the deposit address into the database
    cursor.execute('INSERT INTO deposit_addresses VALUES (?, ?)', (user_id, deposit_address))
    conn.commit()
    conn.close()

    return deposit_address

def get_deposit_address(user_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Retrieve the deposit address from the database
    cursor.execute('SELECT deposit_address FROM deposit_addresses WHERE user_id = ?', (user_id,))
    deposit_address = cursor.fetchone()

    if deposit_address:
        return deposit_address[0]
    else:
        return None

def update_deposit_address(user_id, new_deposit_address):
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Update the deposit address in the database
    cursor.execute('UPDATE deposit_addresses SET deposit_address = ? WHERE user_id = ?', (new_deposit_address, user_id))
    conn.commit()
    conn.close()

def delete_deposit_address(user_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Delete the deposit address from the database
    cursor.execute('DELETE FROM deposit_addresses WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()