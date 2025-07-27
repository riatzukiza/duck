from discord_text_splitter import split_markdown

# read the markdown
with open("shared/test.md", "r") as file:
    markdown_content = file.read()




# Split the markdown content
split_content = split_markdown(markdown_content, finished=True)
# Print the split content
for i, chunk in enumerate(split_content):
    print(f"Chunk {i + 1}:\n{chunk}\n")
    print("-" * 40)  # Separator for readability
