import argparse
import os
import openai
import time
import token_helper

'''
This will split a long text into parts long enough for ChatGPT to handle.
It will then summarize each section to create a new text.
This will repeat until there is only one section left to produce a long and a short summary.
Each step is saved in it's own folder.
'''

# Set up OpenAI API credentials, model to use and maximum token amount for each section
openai.api_key = "YOUR_API_KEY_HERE"
gpt_model = "gpt-3.5-turbo"
max_tokens = 2000

# Function to split the text into sections based on token limit
def token_split_text(text):
    append_section = (lambda: (print(f"Tokens for section {len(sections)+1}:", tokens), sections.append(section.strip())))
    print("="*20)

    sections = []
    tokens = 0
    section = ""
    paragraphs = text.split("\n")

    # Loop through each paragraph and divide the text into sections that are within the max_tokens limit
    for paragraph in paragraphs:
        paragraph_tokens = token_helper.token_counter(paragraph, gpt_model)
        if tokens + paragraph_tokens <= max_tokens:
            section += paragraph + "\n"
            tokens += paragraph_tokens
        else:
            append_section()
            section = paragraph + "\n"
            tokens = paragraph_tokens
    if section:
        append_section()
    return sections

# Function to summarize a section using ChatGPT
def summarize_section(section, length):
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": f"Please provide a {length} summary of the following text omitting chapter numbers/names, starting from the beginning and progressing through each paragraph to the end"},
            {"role": "user", "content": f"The text to be summarized:\n\n{section}"}
        ],
        temperature=0.3
    )
    summary = response.choices[0].message.get("content", "").strip()
    print("Section length:", len(section), "Summary length:", len(summary))
    return summary

# Function to generate summaries for all sections
def generate_summaries(text_parts, step_number, length="long"):
    summaries = []
    # Introduce a pause between API calls
    api_call_count = 0
    start_time = time.time()  # Track start time
    rate_limit = 3 # The amount of API calls that can be made per minute
    print("Step", step_number)
    for i, section in enumerate(text_parts):
        print("Generating a", length, "summary for section", i+1)
        summary = summarize_section(section, length)
        summaries.append(summary)
        api_call_count += 1
        if api_call_count == rate_limit:
            elapsed_time = time.time() - start_time
            if elapsed_time < 60:
                print(f"{'='*20}\nRate limit reached. Pausing for {61 - int(elapsed_time)} seconds.")
                time.sleep(61 - int(elapsed_time))
            api_call_count = 0
            start_time = time.time()  # Reset start time
    return summaries

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Summarizer of long texts")
    parser.add_argument("file_path", type=str, help="Path to the text file")
    args = parser.parse_args()

    # Read the long text from file
    with open(args.file_path, "r") as file:
        initial_text = file.read()

    # Split the long text into sections
    text_parts = token_split_text(initial_text)

    # Generate summaries for all sections
    step_number = 1
    current_summaries = generate_summaries(text_parts, step_number)

    # Save summaries as individual text files
    while len(current_summaries) > 1:
        step_folder = f"Step {step_number} - {len(current_summaries)} sections"
        os.makedirs(step_folder, exist_ok=True)

        for i, summary in enumerate(current_summaries):
            write_file(f"{step_folder}/Section {i+1} summary.txt", summary)

        new_text = "\n".join(current_summaries)
        write_file(f"{step_folder}/Step {step_number} summary.txt", new_text)

        new_text_parts = token_split_text(new_text)

        step_number += 1
        current_summaries = generate_summaries(new_text_parts, step_number)

    # Save the final summaries
    step_folder = f"Step {step_number} - final summaries"
    os.makedirs(step_folder, exist_ok=True)

    long_summary = current_summaries
    write_file(f"{step_folder}/Long summary.txt", long_summary[0])

    short_summary = generate_summaries(long_summary, step_number, "short")
    write_file(f"{step_folder}/Short summary.txt", short_summary[0])

def write_file(file_name, text):
    with open(file_name, "w") as file:
        file.write(text)

if __name__ == "__main__":
    main()
