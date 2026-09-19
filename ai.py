from app import generate_reply


def LLM(prompt):
    return generate_reply(prompt)

if __name__ == "__main__":
    initial_prompt = "User has not added any prompt."
    print(LLM(initial_prompt))