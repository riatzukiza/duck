import nltk
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer


def extract_keywords(text):
    # Tokenize the text into individual words
    tokens = word_tokenize(text)

    # Remove stopwords and punctuation
    stop_words = set(nltk.corpus.stopwords.words('english'))
    tokens = [token for token in tokens if token.lower() not in stop_words]

    # Lemmatize the remaining words
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Join the keywords back into a single string
    keywords = ' '.join(tokens)

    return keywords

# Example usage
text = "This is an example of how you can use NLTK to extract keywords from text."
print(extract_keywords(text))