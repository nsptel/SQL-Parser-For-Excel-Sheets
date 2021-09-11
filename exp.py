import sqlite3

conn = sqlite3.connect(r'C:\Users\Neel Patel\PycharmProjects\SQLParser\databases\b3d37a4d5953d523c43892c439d048bf_a454a0f773a1027b0913e96686e72870b773f450.db')
cursor = sqlite3.Cursor(conn)

cursor.execute('SELECT * FROM sheets')
result = cursor.fetchall()
print(result)

cursor.execute('SELECT * FROM columns')
results = cursor.fetchall()
print(results)
