
he was a duckling, then he was a duck.

Now he is duckman.

That's right, he's all grown up now!
# Open

- tests
- better docker files
- evaluate effectiveness of state object
- give duck access to a file system
- give duck direct access to the database?
- allow duck to generate mongodb query objects
- create a dataset of mongodb query objects.
- create a program validator
- set up restream
- edit videos
- Duck DMs
- Duck video chat?
- Context Manager
- Better twitch chat integration
# Refinement

- webserver
	- WebView of message content
	- Control parameters of the model through an interface
	- allow certain features to be togglable
	- separate chat context that is not discord
- data processing pipeline 
	- Make data processing it's own service(s)
	- Currently doing several things in Duckman's main brain and it keeps him from being his full self.
- crawler
	- move logic for searching to a separate instance with a queue kept... somewhere...
	- mongodb
- keyword generator
	- Using an LLM, generate a bunch of keywords to search for.
- search manager
	- takes generates search queries and executes searches on them. 
	- save the results for later processings.
- downloader
	- From the saved search results, download them for local processings.
- text extractor
	- From the downloaded files, extract text from them and save them in the database.
# Todo

- feature extractor
	- Extract features from existing discord messages itteratively.
		- places
		- times/dates
		- emails
		- links
		- images
		- videos
		- attachments
		- emojis
		- mentions
		- replies
		- threads
		- sentement
	- Populate the meta data of the document object that contains the text.
	- Add feature occurances to their own collection that keeps track of fequency etc.
- cleanup existing code
	- tests?
- document existing code
	- add doc strings
	- add setup instructions to readme
	- document environment variables

# Doing
- document existing code
	- Document possible useful abstractions
- cleanup existing code
	- identify anti patterns
	- reduce code duplication
# Done

- cleanup existing code
	- disable search feature
- state object exists
- basic response model
- document similarity model for messages
- document similarity model for searches.
- basic RAG using prior sources added to chroma 
- searches are done concurrently with responses
- current response won't have access to search data but future ones will.