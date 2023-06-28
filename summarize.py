import argparse
import os
import openai
import time
import token_helper

'''
This will split a long text into parts long enough for ChatGPT to handle.
It will then summarize each section to create a new text.
This will repeat until there is only one section left to produce a long and a short summary.
Each step is saved in its own folder.
'''

# Set up OpenAI API credentials, model to use, and maximum token amount for each section
openai.api_key = "YOU_API_KEY"
gpt_model = "gpt-3.5-turbo"
max_tokens = 2000 # About half of the maximum tokens, which is 4096 for gpt-3.5-turbo
rate_limit = 3 # The amount of API calls that can be made per minute

# Function to split the text into sections based on token limit
def token_split_text(text):
    append_section = (lambda: (print(f"Tokens for section {len(sections)+1}:", tokens), sections.append(section.strip())))
    print("="*20)

    sections = []
    tokens = 0
    section = ""
    parts = [part + "." for part in text.split(".")]

    # Add parts to the section until it reaches the max_token limit
    while parts:
        while tokens < max_tokens and parts:
            section += parts.pop(0)
            tokens = token_helper.token_counter(section, gpt_model)
        append_section()
        tokens = 0
        section = ""
    return sections

# Function to summarize a section using ChatGPT
def summarize_section(section, length):
    retry_count = 0
    while retry_count < 99:
        try:
            response = openai.ChatCompletion.create(
                model=gpt_model,
                messages=[
                    {"role": "system", "content": f"Please provide a {length} summary of the following text omitting chapter numbers/names, starting from the beginning and progressing through each paragraph to the end."},
                    {"role": "user", "content": f"The text to be summarized:\n\n{section}"},
                ],
                temperature=0.3
            )
            summary = response.choices[0].message.get("content", "").strip()
            print("Section length:", len(section), "Summary length:", len(summary))
            return summary
        except Exception as e:
            print("An error occurred during summary generation:", str(e))
            print("Retrying in 60 seconds...")
            time.sleep(60)
            retry_count += 1
    print("Failed to generate summary for section:", section)
    exit()

# Function to generate summaries for all sections
def generate_summaries(text_parts, step_number, length="long", folder_path=None):
    summaries = []

    api_call_count = 0 # Handle rate_limit
    start_time = time.time()  # Track start time

    print("Step", step_number)
    for i, section in enumerate(text_parts):
        print("Generating a", length, "summary for section", i+1)
        summary = summarize_section(section, length)
        summaries.append(summary)
        api_call_count += 1

        # Save the summary to a file in the specified folder path
        if folder_path:
            write_file(f"{folder_path}/Section {i+1} summary.txt", summary)

        if api_call_count == rate_limit:
            elapsed_time = time.time() - start_time
            if elapsed_time < 60:
                print(f"{'='*20}\nRate limit reached. Pausing for {61 - int(elapsed_time)} seconds.")
                time.sleep(61 - int(elapsed_time))
            api_call_count = 0
            start_time = time.time()  # Reset start time
    return summaries

# Function to write text to a file
def write_file(file_name, text):
    os.makedirs(file_name.split("/")[0], exist_ok=True)
    with open(file_name, "w") as file:
        file.write(text)

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
    current_summaries = generate_summaries(text_parts, step_number, folder_path=f"Step {step_number} - {len(text_parts)} sections")

    # Save summaries as individual text files
    while len(current_summaries) > 1:
        step_folder = f"Step {step_number} - {len(current_summaries)} sections"

        new_text = "\n".join(current_summaries)
        write_file(f"{step_folder}/Step {step_number} summary.txt", new_text)

        new_text_parts = token_split_text(new_text)

        step_number += 1
        current_summaries = generate_summaries(new_text_parts, step_number, folder_path=step_folder)

    # Save the final summaries
    step_folder = f"Step {step_number} - final summaries"
    # Long summary
    write_file(f"{step_folder}/Long summary.txt", current_summaries[0])
    # Short summary
    short_summary = generate_summaries(current_summaries, step_number, "short", folder_path=step_folder)
    write_file(f"{step_folder}/Short summary.txt", short_summary[0])

if __name__ == "__main__":
    main()
