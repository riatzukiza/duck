"""
Itterate recusively through a directory and index the the python files with chromadb and mongodb for the Duckman service.
"""
import asyncio
from datetime import date
import os
from time import sleep
import chromadb
import ollama
from shared.embeddings import generate_embedding
from shared.mongodb import db

chroma_client = chromadb.PersistentClient(path="./chroma_db")

chroma_collection = chroma_client.get_or_create_collection(name="duckman_files")
file_collection = db["duckman_files"]

directory = "."

def format_code_chunks(path,i,sha,contents,extension):
    return f"""
Contents of {path} (SHA: {sha}, chunk {i}):
```{extension}
{contents}
```
"""

def format_code_lines(path,i,sha,contents,extension):
    return f"""
Contents of {path} (SHA: {sha}, line {i}):
```{extension}
{contents}
```
"""


async def index_file(file,root,extension):
    with open(os.path.join(root, file), "r") as f:
        contents=f.read()
        shasum=hash(contents)

        sleep(5)
        for i,chunk in enumerate(contents.split('\n\n')):
            text=format_code_chunks(os.path.join(root, file),i,shasum,chunk,extension)
            embedding = await generate_embedding(text)
            chroma_collection.upsert(ids=[os.path.join(root, file)+"-"+str(shasum)+"-chunk-"+str(i)],embeddings=[embedding])
async def main():
    while True:
        for root, dirs, files in os.walk(directory):
            for file in files:
                extension = os.path.splitext(file)[1]
                if extension in ['.py','.html','.js','.css','.json','.txt','.md','.jsx','.ts','.tsx','.yml','.yaml','.csv']:
                    print("indexing", os.path.join(root, file))
                    try:
                        await index_file(file,root, extension)
                    except Exception as e:
                        print("error",e)
                    
        print("done!")
        sleep(10)


asyncio.run(main())