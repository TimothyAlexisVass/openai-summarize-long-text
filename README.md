# Long text summarizer

This script will use ChatGPT to summarize a text of any length, such as an entire book, into several steps of summaries.
The initial text is split into sections based on the max token limit set.
Each section is summarized and concatenated into a new text which is again split into sections.

This process repeats until there is only 1 section which will then be turned into a long and a short summary.

The summary for each step is also stored.

## Usage:

Make sure you insert your OpenAI API-key into summarize.py (https://platform.openai.com/account/api-keys)

Then you can run:
`python3 summarize.py <path_to_long_text_file>`

### With the included example:

`python3 summarize.py peter_pan.txt`
