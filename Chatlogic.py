import sqlite3

def get_response(user_input):
    # Connect to the database
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    # Search for an exact match in the database
    cursor.execute("SELECT bot_response FROM responses WHERE user_input = ?", (user_input.lower(),))
    result = cursor.fetchone()

    conn.close()

    # Return the response or a default message
    if result:
        return result[0]
    else:
        return "Sorry, I don't understand that. Can you rephrase?"

# Chatbot loop
def chat():
    print("Chatbot: Hello! Type 'bye' to exit.")
    while True:
        user_input = input("You: ").strip().lower()
        if user_input == 'bye':
            print("Chatbot: Goodbye!")
            break
        response = get_response(user_input)
        print(f"Chatbot: {response}")

# Start the chatbot
if __name__ == "__main__":
    chat()
