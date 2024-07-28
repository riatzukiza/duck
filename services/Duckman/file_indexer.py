"""
Itterate recusively through a directory and index the the python files with chromadb and mongodb for the Duckman service.
"""
from datetime import date
import os
from time import sleep
import chromadb
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

def index_file(file,root,extension):
    with open(os.path.join(root, file), "r") as f:
        contents=f.read()
        shasum=hash(contents)

        sleep(5)
        for i,chunk in enumerate(contents.split('\n')):
            text=format_code_chunks(os.path.join(root, file),i,shasum,chunk,extension)
            print("chunk",text)
            sleep(1)
            chroma_collection.upsert(ids=[os.path.join(root, file)+"-"+str(shasum)+"-line-"+str(i)], documents=[text])

        sleep(5)
        for i,chunk in enumerate(contents.split('\n\n')):
            text=format_code_chunks(os.path.join(root, file),i,shasum,chunk,extension)
            print("chunk",text)
            sleep(1)
            chroma_collection.upsert(ids=[os.path.join(root, file)+"-"+str(shasum)+"-line-"+str(i)], documents=[format_code_lines(os.path.join(root, file),i,shasum,chunk)])
while True:
    keys=[]
    fragments=[]

    for root, dirs, files in os.walk(directory):
        for file in files:
            print("file",file)
            extension = os.path.splitext(file)[1]
            if extension in ['.py','.html','.js','.css','.json','.txt','.md','.jsx','.ts','.tsx','.yml','.yaml','.csv']:
                print("indexing", os.path.join(root, file))
                index_file(file,root, extension)
                
    print("done!")
    sleep(10)

