
import re

import nltk
nltk.download('punkt')

# Extract sentences from a text
def extract_sentences(text):
    sentences = nltk.sent_tokenize(text)
    return sentences

def split_into_sentences(text):
    # Define the regex pattern for sentence boundaries
    
    return text.split(".\n\n")

def split_markdown(markdown,finished=False):

    lines=markdown.split("\n\n")
    results=[]
    code_block=""

    for line in lines:
        if "```" in line :
            split_line=line.split("```")
            if code_block:
                code_block+=line+ "\n\n"
                results.append(code_block)
                code_block=""
            else:
                code_block+=line 
        elif code_block:
            code_block+=line + "\n\n"
        elif re.match(r"^\d+\.",line):
            results.append(line)
        else:
            sentances=extract_sentences(line)
            for sentance in sentances:
                results.append(sentance)
    if code_block:
        end_code_block_chunk='\n```\n\n'
        results.append(f"{code_block}{end_code_block_chunk if finished else ''}")
    return results
            
