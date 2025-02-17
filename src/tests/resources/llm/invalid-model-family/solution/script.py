def reverse_words(sentence):
    # Split the sentence into words, reverse the list, and join it back into a string
    return ' '.join(sentence.split()[::-1])
