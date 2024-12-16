import sqlite3

# Connect to SQLite database (or create it)
conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()

# Create a table for storing responses
cursor.execute('''
CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT NOT NULL,
    bot_response TEXT NOT NULL
)
''')

# Add some sample responses
cursor.executemany('''
INSERT INTO responses (user_input, bot_response) VALUES (?, ?)
''', [
    ('hello', 'Hi there! How can I help you today?'),
    ('how are you', 'I am just a bot, but I am functioning as expected!'),
    ('bye', 'Goodbye! Have a great day!'),
])
conn.commit()
conn.close()
