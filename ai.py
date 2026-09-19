import requests

def LLM(prompt):
    response = requests.post("https://localhost:11434/ai/generate", json={"model": "llama3.2", "prompt": prompt, "stream": False})
    result = response.json()
    message = result.get("response", "")
    return message

if __name__ == "__main__":
    initial_prompt = "User has not added any prompt."
    print(LLM(initial_prompt))