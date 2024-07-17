







# Install ollama models
```bash
docker exec -it ollama ollama pull <model-name>
docker exec -it ollama ollama pull llama2
```


To remove the `_id` field and any other unwanted fields from the documents retrieved from a MongoDB collection, you can use the `projection` feature of the `find()` method. This allows you to specify which fields to include or exclude in the resulting documents.

Here’s how you can modify the previous script to exclude the `_id` field and any other fields you don't want:

1. **Install pymongo** if you haven’t already:
   ```bash
   pip install pymongo
   ```

2. **Connect to your MongoDB database and retrieve the documents with the desired fields excluded**:

Here's the complete code:

```python
import pymongo
import pandas as pd

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string
db = client["your_database_name"]  # Replace with your database name
collection = db["your_collection_name"]  # Replace with your collection name

# Define the fields to exclude
fields_to_exclude = {"_id": 0, "unwanted_field_1": 0, "unwanted_field_2": 0}  # Add any other fields to exclude

# Retrieve the last 20 documents, excluding specified fields
last_documents = list(collection.find({}, fields_to_exclude).sort("created_at", pymongo.DESCENDING).limit(20))

# Convert documents to a DataFrame
df = pd.DataFrame(last_documents)

# Display the DataFrame
print(df)
```

### Explanation:

1. **Connection**:
   ```python
   client = pymongo.MongoClient("mongodb://localhost:27017/")
   db = client["your_database_name"]
   collection = db["your_collection_name"]
   ```

   Replace `localhost:27017` with your MongoDB connection string and `your_database_name` and `your_collection_name` with the appropriate names.

2. **Define the fields to exclude**:
   ```python
   fields_to_exclude = {"_id": 0, "unwanted_field_1": 0, "unwanted_field_2": 0}
   ```

   Specify the fields you want to exclude by setting their values to `0` in the dictionary. The `_id` field is included here by default.

3. **Retrieve documents with fields excluded**:
   ```python
   last_documents = list(collection.find({}, fields_to_exclude).sort("created_at", pymongo.DESCENDING).limit(20))
   ```

   This retrieves the last 20 documents, sorted by the `created_at` field in descending order, excluding the specified fields.

4. **Convert to DataFrame**:
   ```python
   df = pd.DataFrame(last_documents)
   ```

   Convert the list of documents into a Pandas DataFrame.

5. **Display the DataFrame**:
   ```python
   print(df)
   ```

   This prints the DataFrame containing the last 20 documents with the unwanted fields excluded.

By following these steps, you can retrieve the last 20 documents from a MongoDB collection, excluding the `_id` field and any other specified fields.
