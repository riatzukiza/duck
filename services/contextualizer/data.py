"""This service creates messages from the model and saves them in mongodb
"""

import os
import datetime

import pandas as pd

def dir_is_not_empty(path): return os.path.exists(path) and len(os.listdir(path)) > 0
def get_collection_df(collection): return pd.DataFrame(list(collection.find()))
def get_chunk_file_path(chunk_size,i,num_chunks): return f"output_chunk_{chunk_size}_{i+1}_{num_chunks}.csv"

def get_all_chunks_as_strings(chunk_file_paths):
    # List to hold CSV strings
    csv_strings = []

    # Read each chunk file and convert to CSV string
    for path in chunk_file_paths:
        df_chunk = pd.read_csv(path)
        csv_string = df_chunk.to_csv(index=False)
        csv_strings.append(csv_string)
    print("CSV strings are ready for training the model.")
    return csv_strings

def get_chunk_by_index(i,chunk_size,num_chunks,df):
    if(i>num_chunks):
        raise Exception("out of bounds: Overflow")
    if(i<0):
        raise Exception("out of bounds: Negative number")
    return df[i*chunk_size:(i+1)*chunk_size]


def get_chunk_file_paths(df, chunk_size, num_chunks):
    # Save DataFrame to multiple CSV files in chunks
    chunk_paths = []
    for i in range(num_chunks):
        chunk_file_path = get_chunk_file_path(chunk_size,i, num_chunks)

        chunk_paths.append(chunk_file_path)

        get_chunk_by_index(i,chunk_size,num_chunks,df ).to_csv(
            chunk_file_path, index=False
        )
    return chunk_paths


class ChunkedCollection():
    def __init__(self, collection,chunk_size):
        self.collection=collection
        self.chunk_size=chunk_size

    @property
    def chunk_file_paths(self):
        return get_chunk_file_paths(self.df,self.chunk_size, self.num_chunks)

    @property
    def df(self):
        return get_collection_df(self.collection)

    @property
    def num_chunks(self):
        return len(self.df) // self.chunk_size + (1 if len(self.df) % self.chunk_size != 0 else 0)

    @property
    def chunks(self): return get_all_chunks_as_strings(self.chunk_file_paths)

    @property
    def last(self): return self.chunks[-1]

    def get_chunk_by_index(self,i):
        return get_chunk_by_index(i,self.chunk_size,self.num_chunks,self.df)



