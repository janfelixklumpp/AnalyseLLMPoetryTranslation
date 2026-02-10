import phonemizer
from numpy import ndarray
from comet import download_model, load_from_checkpoint

# method to extract the sequence of stress values (primary stress = 1.0, secondary stress = 0.9, unstressed = 0.8)
# from a line of English or German text
def get_stresses(line, lang="de"):
    # define the monophthongs, diphthongs, and triphthongs occurring
    if lang == "de":
        diphthongs = ["aɪ", "ɔø", "aʊ", "??"]
        triphthongs = []
        vowels = ["a", "e", "i", "o", "u", "y", "ø", "ɪ", "ɔ", "ʊ", "ɑ", "ɜ", "ɛ", "ə", "œ"]
        text = phonemizer.phonemize(line, language="de", with_stress=True)
    else: # for English
        diphthongs = ["aɪ", "oʊ", "aʊ", "eɪ", "iɪ", "ɔɪ", "iə", "n̩", "l̩"]
        triphthongs = ["aɪɚ", "aʊɚ"]
        vowels = ["ʌ", "ɛ", "ə", "i", "ɚ", "ɪ", "æ", "u", "ʊ", "ᵻ", "ɐ", "ɑ", "ɜ", "ɔ", "o"]
        text = phonemizer.phonemize(line, with_stress=True)
    t = text
    sequence = []
    stress = 0.8
    # go through the whole line
    # for each character:
    # - if it is a stress mark, change the stress value
    # - if the beginning of the string is a vowel, append the stress value to the sequence and reset the stress value
    while len(t) > 0:
        if t[0] == "ˈ":
            stress = 1
        elif t[0] == "ˌ":
            stress = 0.9
        elif len(t) > 2 and t[:3] in triphthongs:
            sequence.append(stress)
            stress = 0.8
            t = t[2:]
        elif len(t) > 1 and t[:2] in diphthongs:
            sequence.append(stress)
            stress = 0.8
            t = t[1:]
        elif t[0] in vowels:
            sequence.append(stress)
            stress = 0.8
        t = t[1:]
    return sequence

# edit distance algorithm, where line and metre are represented as sequences of stress values
# returns the alignment and the score for this line
# set adjusted=True to adjust the distance based on the length of the metre (may be useful when lines of different
# length cooccur in a poem)
def edit_distance_alignment(line, metre, adjusted=False):
    l = [0] + line
    m = [0] + metre
    value_table = ndarray((len(l), len(m)))
    pointer_table = ndarray((len(l), len(m)))
    for i in range(len(l)):
        value_table[i][0] = sum(l[0:i + 1])
        pointer_table[i][0] = 2  # 2 signifies insertion
    for j in range(len(m)):
        value_table[0][j] = sum(m[0:j + 1])
        pointer_table[0][j] = 1  # 1 signifies deletion
    for i in range(len(l)):
        if i == 0:
            pass
        else:
            for j in range(len(m)):
                if j == 0:
                    pass
                else:
                    insert = value_table[i - 1][j] + l[i]
                    delete = value_table[i][j - 1] + m[j]
                    substitute = value_table[i - 1][j - 1] + abs(
                        l[i] - m[j])
                    value_table[i][j] = min(insert, delete, substitute)
                    if delete < insert and delete < substitute:
                        pointer_table[i][j] = 1
                    elif insert < substitute:
                        pointer_table[i][j] = 2
                    else:
                        pointer_table[i][j] = 0  # 0 signifies substitution
    score = value_table[-1][-1]

    # backtrack, recording for each metrical position in the reference how it is realized in the actual line
    i = len(l) - 1
    j = len(m) - 1
    alignment = []
    while j >= 0 and i >= 0:
        internal = []
        while pointer_table[i][j] == 2:
            internal = [l[i]] + internal
            i -= 1
        if pointer_table[i][j] == 0:
            internal = [l[i]] + internal
            i -= 1
            j -= 1
        elif pointer_table[i][j] == 1:
            internal = [0] + internal
            j -= 1
        alignment = [internal] + alignment
    if adjusted:
        return alignment, (score*10)/len(metre) # adjust for reference metre length
    else:
        return alignment, score

# get a list of metrical distances for each of several lines
def line_distance(stresses, metre):
    return [edit_distance_alignment(stresses[i], metre[i])[1] for i in range(len(stresses))]

# get the metrical distance for a whole poem
def get_metrical_distance(candidate, metrical_pattern, lang="de"):
    # if the candidate is a text, get stress values first
    if type(candidate) is str:
        stresses = [get_stresses(line=line, lang=lang) for line in candidate.split("\n")]
        stresses = [x for x in stresses if x != []]
    else:
        stresses = candidate.copy()

    metre = metrical_pattern.copy()
    total = 0

    # undefined if there is no poem (e.g. because none has been produced)
    if len(stresses) == 0 or len(metre) == 0:
        return None
    # if the two parts are of different length, remove lines iteratively
    elif len(stresses) > len(metre):
        diff = len(stresses) - len(metre)
        while diff > 0:
            min_value = 1000
            min_index = 0
            for x in range(len(stresses)):
                value = sum(stresses[x])
                if value < min_value:
                    min_value = value
                    min_index = x
            total += sum(stresses.pop(min_index))
            diff -= 1
    elif len(metre) > len(stresses):
        diff = len(metre) - len(stresses)
        while diff > 0:
            min_value = 1000
            min_index = 0
            for x in range(len(metre)):
                value = sum(metre[x])
                if value < min_value:
                    min_value = value
                    min_index = x
            total += sum(metre.pop(min_index))
            diff -= 1

    # return average line distance
    return (total + sum(line_distance(stresses, metre))) / len(metre)

# get the rhyme scheme similarity between a candidate (as a text) and a reference (as a list of rhyme pairs)
def get_rhyme_scheme_similarity(candidate, rhyme_scheme, lang="de"):
    # get the phonetic sequence from the last stressed vowel onwards and the preceding consonantal onset
    def get_rhyme(line, lang=lang):
        if lang == "de":
            transcription = phonemizer.phonemize(line, language="de", with_stress=True)
            # replace vowels according to the equivalence rules
            equivalences = [("y", "i"), ("ɪ", "i"), ("ɔø", "aɪ"), ("ai", "aɪ"), ("aʊ", "aw"), ("ø", "e"), ("œ", "e"),
                            ("ɛ", "e"), ("ɑ", "a"), ("ɔ", "o"), ("ʊ", "u"),
                            ("ː", "")]
            for e in equivalences:
                transcription = transcription.replace(e[0], e[1])  # remove umlaut and length distinctions
            transcription = transcription.replace("ˌ", "ˈ")
            index = transcription.rfind("ˈ")
            rhyme = transcription[index+1:]
            # define all possible onsets
            onset = transcription[index-3:index] if transcription[index-3:index] in ["ʃtɾ", "ʃpɾ", "tsv"] else \
                transcription[index-2:index] if transcription[index-2:index] in ["ʃl", "ʃm", "ʃn", "ʃɾ", "ʃv", "bɾ",
                                                                                 "bl", "dɾ", "fɾ", "fl", "ɡɾ", "ɡl",
                                                                                 "ɡn", "kl", "kɾ", "kn", "pl", "pɾ",
                                                                                 "pn", "kv", "ʃt", "ʃp", "tɾ", "vɾ",
                                                                                 "ts", "pf", "ps", "ks"] else \
                transcription[index-1:index]
        else: # English
            transcription = phonemizer.phonemize(line, with_stress=True)
            transcription = transcription.replace("ˌ", "ˈ")
            index = transcription.rfind("ˈ")
            rhyme = transcription[index+1:]
            # define all possible onsets
            onset = transcription[index-3:index] if transcription[index-3:index] in ["stɹ", "spɹ"] else \
                transcription[index-2:index] if transcription[index-2:index] in ["pl", "pɹ", "bl", "bɹ", "fl", "fɹ",
                                                                                 "tɹ", "dɹ", "ʃɾ", "sl", "tʃ", "dʒ",
                                                                                 "sw", "kw", "kɹ", "kl", "gl", "gɹ",
                                                                                 "ks"] else \
                transcription[index-1:index]

        return rhyme, onset

    # get a list of rhyme pairs
    def get_rhyme_scheme(candidate, lang=lang):
        rhymes = [get_rhyme(line, lang=lang) for line in candidate.split("\n") if line.strip() != ""]
        pairs = []
        for i in range(len(rhymes)):
            for j in range(len(rhymes)-i-1):
                if rhymes[i][0]==rhymes[j+i+1][0] and rhymes[i][1]!=rhymes[j+i+1][1]:
                    pairs.append([i,j+i+1])
                elif (rhymes[i][0].endswith(rhymes[j+i+1][0]) or rhymes[j+i+1][0].endswith(rhymes[i][0])) and \
                        rhymes[i][1]!=rhymes[j+i+1][1] and not \
                        rhymes[i][0].endswith(rhymes[j+i+1][1]+rhymes[j+i+1][0]) and not \
                        rhymes[j+i+1][1].endswith(rhymes[i][1]+rhymes[i][0]):
                    pairs.append([i,j+i+1])
        return pairs

    # calculate rhyme scheme similarity from the overlap between the rhyme pairs of candidate and reference
    candidate_rhyme_scheme = get_rhyme_scheme(candidate=candidate, lang=lang)
    f1_score = 0
    if len(candidate_rhyme_scheme) > 0:
        precision = len([e for e in candidate_rhyme_scheme if e in rhyme_scheme]) / len(candidate_rhyme_scheme)
    else:
        precision = 1.0
    if len(rhyme_scheme) > 0:
        recall = len([e for e in rhyme_scheme if e in candidate_rhyme_scheme]) / len(rhyme_scheme)
    else:
        recall = 1.0
    if precision + recall > 0:
        f1_score = 2 * precision * recall / (precision + recall)
    return precision, recall, f1_score

# get cometkiwi scores
def get_cometkiwi(originals, translations):
    model_path = download_model("Unbabel/wmt22-cometkiwi-da")
    model = load_from_checkpoint(model_path)
    data = [{"src": originals[i], "mt": translations[i]} for i in range(len(originals))]
    model_output = model.predict(data)
    return model_output.scores
