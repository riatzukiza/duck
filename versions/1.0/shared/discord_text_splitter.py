
import re

import nltk
nltk.download('punkt')
nltk.download('punkt_tab')

# Extract sentences from a text
def extract_sentences(text):
    sentences = nltk.sent_tokenize(text)
    return sentences

def split_into_sentences(text):
    # Define the regex pattern for sentence boundaries
    return text.split(".\n\n")


def split_markdown(markdown,finished=False):

    lines=markdown.split("\n\n")
    code_blocks=markdown.split("```")
    results=[]
    code_block=""
    pre_formatted_block=""

    for line in lines:
        if "`" in line:
            if "```" in line:
                if code_block and not (code_block.count("```") % 2):
                    code_block+=line+ "\n\n"
                    # results.append(code_block)
                else:
                    code_block+=line + "\n\n"
                    # results.append(code_block)
            else:
                pre_formatted_block+=line + "\n\n"

        elif pre_formatted_block:
            pre_formatted_block+=line + "\n\n"
        elif code_block:
            code_block+=line + "\n\n"
            # results.append(code_block)
        elif re.match(r"^\d+\.",line):
            results.append(line)
        else:
            sentances=extract_sentences(line)
            for sentance in sentances:
                results.append(sentance)
    if code_block:
        results.append(code_block)
    return results
            

class DiscordTextSplitter:
    """
    Handles a stream of tokens from an LLM and splits them into manageable chunks for Discord messages.
    This class is designed to handle the specific constraints of Discord messages, ensuring that
    each chunk does not exceed the maximum length allowed by Discord (2000 characters) by detecting sentances, paragraphs, code blocks, and other meaningful breaks in the text.
    If a chunk exceeds the maximum length, it will return the  chunk regardless of whether it is a complete sentence or not, to ensure that the message can be sent without truncation.
    Otherwise, it will yield the current chunk when it reaches the maximum length or when a meaningful break is detected (like a sentence end or paragraph break).
    It also makes sure that code chunks are not split across messages, preserving the integrity of code formatting.
    """
    def __init__(self, max_length=2000):
        self.max_length = max_length
        self.current_chunk = ""
        self.is_code_block = False
    def add_token(self, token):
        """
        Adds a token to the current chunk. If the current chunk exceeds the maximum length,
        it returns the current chunk and starts a new one.
        """
        ## It seems like the model handles "``",  "```", and "`" as distinct tokens.
        ## It seems to treat "``" followed by "`" as the end of a code block
        ## and "```" as the start of a code block.
        ## We'll have to see how this works in practice. As the model could choose to output any combination of these to signify code blocks.
        ## If it breaks in the future we will have to do this differently.
        if token == "`\n\n" and self.is_code_block:
            self.is_code_block = False
            return None

        if token.startswith("```") and self.is_code_block:
            self.is_code_block = False
            self.current_chunk += "```"
            result = self.current_chunk
            self.current_chunk = ""

        if token.startswith("```") and not self.is_code_block:
            self.is_code_block = True
            result= self.current_chunk
            self.current_chunk = "```"
            return result

        if token.startswith("``") and self.is_code_block:
            self.current_chunk += "```"
            result = self.current_chunk
            self.current_chunk = ""
            return result
        # if len(self.current_chunk) + len(token) > self.max_length-5:
        #     if self.is_code_block:
        #         result=self.current_chunk+"\n````"
        #     else:
        #         result=self.current_chunk
        #     self.current_chunk = token
        #     return result

        elif self.is_code_block:
            self.current_chunk += token
            return None
        else:
            self.current_chunk += token
            # sentances=extract_sentences(self.current_chunk)
            if self.current_chunk.endswith("\n") :
                result = self.current_chunk
                self.current_chunk = ""
                return result
            else:
                return None
