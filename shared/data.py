"""
This service creates messages from the model and saves them in MongoDB.
"""

from io import StringIO
import os
import pandas as pd


FIELDS_TO_EXCLUDE = {
    "_id": 0,
    "id": 0,
    # "author":0,
    # "guild":0,
    # "author_name":0,
    "recipient": 0,
    "recipient_name": 0,
    # "raw_mentions": 0,
}  # Add any other fields to exclude

def get_df(document_list):
    """
    Retrieve all documents from the cursor,
    excluding specified fields,
    and return them as a pandas DataFrame.
    """
    # Convert the list of documents to a DataFrame
    df = pd.DataFrame(document_list)
    # List of columns to exclude
    columns_to_exclude = [key for key, value in FIELDS_TO_EXCLUDE.items() if value == 0]
    # Drop the specified columns from the DataFrame
    df = df.drop(columns=columns_to_exclude, errors='ignore')  # errors='ignore' to skip non-existing columns
    return df

def gaurd_index(v,bounds):
    if v >= bounds:
        raise IndexError("Index out of bounds: Overflow")
    if v < 0:
        raise IndexError("Index out of bounds: Negative number")

def get_chunk_by_index(i, chunk_size, num_chunks, df):
    """
    Retrieve a specific chunk of data by index.
    """
    gaurd_index(i,num_chunks)
    return df[i * chunk_size:(i + 1) * chunk_size]

class CSVChunk:
    """
    Class to represent a csv chunk.
    """
    def __init__(self, chunker, chunk_id) -> None:
        self.chunker = chunker
        self.chunk_id = chunk_id

    @property
    def csv(self):
        csv_buffer=StringIO()
        self.value.to_csv(csv_buffer,index=False)
        return csv_buffer.getvalue()
    @property
    def value(self):
        return get_chunk_by_index(
            self.chunk_id,
            self.chunker.chunk_size,
            self.chunker.num_chunks,
            self.chunker.df
        )

class CSVChunker:
    """
    Class to handle chunking of a MongoDB cursor into csv strings.
    """
    def __init__(self, name,cursor, chunk_size):
        self.name= name
        self.data = list(cursor)
        self.chunk_size = chunk_size

    @property
    def df(self):
        """Return the DataFrame representation of the cursor."""
        return get_df(self.data)

    @property
    def num_chunks(self):
        """Calculate and return the number of chunks."""
        return len(self.df) // self.chunk_size + (
            1 if len(self.df)
                 % self.chunk_size != 0
            else 0
        )

    @property
    def csvs(self):
        """Return all chunks as CSV strings."""
        return [chunk.csv for chunk in self.chunks]
    @property
    def chunks(self):
        """Return all chunks """
        return self.get_chunks()

    def get_chunks(self):
        """Return all chunks """
        chunks=[]
        for i in range(self.num_chunks):
            chunks.append(CSVChunk(self,i)) 
        return chunks

    @property
    def last(self):
        """Return the last chunk as a CSV string."""
        return list(self.chunks)[-1]

    def get_chunk(self, i):
        """Retrieve a specific chunk by index."""
        return get_chunk_by_index(
            i,
            self.chunk_size,
            self.num_chunks,
            self.df
        )
