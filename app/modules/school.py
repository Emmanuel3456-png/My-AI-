def answer(question):

    question = question.lower()

    if "who can use" in question or "who is quantum mind for" in question:
        return "Quantum Mind is a general assistant. Anyone can use it."

    elif "courses" in question or "what can i learn" in question:
        return "You can ask about science, math, language, history, coding, or everyday questions."

    elif "computer studies" in question:
        return "Computer Studies teaches the fundamentals of computers, software, and programming."

    return None
