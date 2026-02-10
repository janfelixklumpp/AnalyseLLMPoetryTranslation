from openai import OpenAI
from string import digits

client = OpenAI(
    api_key='INSERT_API_KEY_HERE'
)

# definitions for the individual conditions
def plain(original, model):
    prompt = f"Please translate the following poem to German: \n\n{original}"
    messages = [{"role": "user", "content": prompt}]
    chat = client.chat.completions.create(model=model, messages=messages)
    translation = chat.choices[0].message.content
    return translation

def plainform(original, model):
    prompt = f"Please translate the following poem to German. Please make sure that your translation reproduces the form of the original (rhyme and meter): \n\n{original}"
    messages = [{"role": "user", "content": prompt}]
    chat = client.chat.completions.create(model=model, messages=messages)
    translation = chat.choices[0].message.content
    return translation

def plainmeaning(original, model):
    prompt = f"Please translate the following poem to German. Please make sure that your translation reproduces the meaning of the original as closely as possible: \n\n{original}"
    messages = [{"role": "user", "content": prompt}]
    chat = client.chat.completions.create(model=model, messages=messages)
    translation = chat.choices[0].message.content
    return translation

# can also be used for the conditions "IterativeMixed" and "IterForm2Steps", depending on the input translations
def iterativeform(original, attempt, model):
    prompt = f"You are provided with an English poem and an attempt at a German translation. Please suggest a translation to German that reproduces the form of the original (rhyme and meter) better.\n\nOriginal:\n\n{original}\n\nAttempt at translation:\n\n{attempt}"
    messages = [{"role": "user", "content": prompt}]
    chat = client.chat.completions.create(model=model, messages=messages)
    translation = chat.choices[0].message.content
    return translation

def iterativemeaning(original, attempt, model):
    prompt = f"You are provided with an English poem and an attempt at a German translation. Please suggest a translation to German that reproduces the meaning of the original better.\n\nOriginal:\n\n{original}\n\nAttempt at translation:\n\n{attempt}"
    messages = [{"role": "user", "content": prompt}]
    chat = client.chat.completions.create(model=model, messages=messages)
    translation = chat.choices[0].message.content
    return translation

def analysisrewrite(original, candidate_translation, model, return_description=False):
    prompt1 = f"Please tell me the meter and rhyme of the following poem (in the format: \"Meter: [meter]; Rhyme scheme: [rhyme scheme]\").\n\nPoem:\n{original}\n\n"
    messages = [{"role": "user", "content": prompt1}]
    chat = client.chat.completions.create(model=model, messages=messages)
    description = chat.choices[0].message.content
    prompt2 = f"Please translate the following to German:\n\n{description}"
    messages = [{"role": "user", "content": prompt2}]
    chat = client.chat.completions.create(model=model, messages=messages)
    german_description = chat.choices[0].message.content
    prompt3 = f"Bitte schreiben Sie den folgenden Text in ein Gedicht mit den folgenden Eigenschaften um:\n\n{german_description}\n\nText:\n{candidate_translation}\n\n"
    messages = [{"role": "user", "content": prompt3}]
    chat = client.chat.completions.create(model=model, messages=messages)
    improved_translation = chat.choices[0].message.content
    if return_description:
        return improved_translation, description, german_description
    return improved_translation

def analysistranslate(original, model, return_description=False):
    prompt1 = f"Please tell me the meter and rhyme of the following poem (in the format: \"Meter: [meter]; Rhyme scheme: [rhyme scheme]\").\n\nPoem:\n{original}\n\n"
    messages = [{"role": "user", "content": prompt1}]
    chat = client.chat.completions.create(model=model, messages=messages)
    description = chat.choices[0].message.content
    prompt2 = f"Please translate the poem below to German. Please make sure to reproduce the meter and rhyme scheme of the original, making use of the given additional information.\n\nInformation on meter and rhyme scheme:\n{description}\n\nPoem:\n{original}\n\n"
    messages = [{"role": "user", "content": prompt2}]
    chat = client.chat.completions.create(model=model, messages=messages)
    translation = chat.choices[0].message.content
    if return_description:
        return translation, description
    return translation

if __name__ == "__main__":
    iterative = True # True for iterative conditions, where there is a candidate translation to improve upon
    model = "gpt-4o" # insert the model name

    remove_digits = str.maketrans('', '', digits)

    original_poems = "".join(open("data/shakespeare_yale", "r").readlines()).replace("END", "").translate(
        remove_digits).split("<>")[1:-1]

    if iterative:
        # for conditions that derive a translation iteratively from a previous attempt, this is the previous attempt
        seed_translations = "".join(open("PATH_TO_SEED_TRANSLATION", "r").readlines()).replace("END",
                                                                                                     "").translate(
            remove_digits).split("<>")[1:-1]

        input_poems = [(original_poems[i], seed_translations[i]) for i in range(len(original_poems))]
    else:
        input_poems = [(original_poems[i]) for i in range(len(original_poems))]
    output_translations = []

    for p in input_poems:
        # use whichever condition is intended instead
        t = plain(p[0], model=model)
        # t = iterativeform(p[0], p[1], model=model) # use p[1] for seed translations
        output_translations.append(t)

    with open("output_translations.txt", "a") as outfile:
        for c in range(len(output_translations)):
            outfile.write("<" + str(c+1) + ">\n" + str(output_translations[c]) + "\n")