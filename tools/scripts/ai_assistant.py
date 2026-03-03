from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_ai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    print("\nMobility AI Assistant\n")
    user_input = input("Ask Codex a question: ")
    answer = ask_ai(user_input)
    print("\nAI Response:\n")
    print(answer)
