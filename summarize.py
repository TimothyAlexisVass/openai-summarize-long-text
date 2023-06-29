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
openai.api_key = "YOUR_API_KEY_HERE"
gpt_model = "gpt-3.5-turbo"
max_tokens = 2000 # About half of the maximum tokens, which is 4096 for gpt-3.5-turbo
rate_limit = 3 # The amount of API calls that can be made per minute

# Function to split the text into sections based on token limit
def token_split_text(text):
    append_section = (lambda: (print(f"Section {len(sections)+1}: {tokens} tokens, {len(section)} characters"), sections.append(section.strip())))

    sections = []
    tokens = 0
    section = ""
    parts = [part + "." for part in text.split(".")]

    print("="*20 + "\nSplitting text into sections")
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
def gpt_summarize(section, length):
    retry_count = 0
    max_tries = 99
    while retry_count < max_tries:
        try:
            response = openai.ChatCompletion.create(
                model=gpt_model,
                messages=[
                    {"role": "system", "content": f"Please generate a {length} summary of the following text omitting chapter numbers/names, starting from the beginning and progressing through each paragraph to the end."},
                    {"role": "user", "content": f"Here is the text:\n\n{section}"},
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
    print(f"Failed to generate summary for section {section} after {max_tries} tries")
    exit()

# Function to generate summaries for all sections
def generate_summaries(text_parts, step, folder_path=None):
    summaries = []

    api_call_count = 0 # Handle rate_limit
    start_time = time.time()  # Track start time

    print(f"\nStep {step}")
    for i, section in enumerate(text_parts):
        print("Summarizing section", i+1)
        summary = gpt_summarize(section, "" if step > 3 else "long")
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
    sections = token_split_text(initial_text)

    step = 0

    while len(sections) > 1:
        step += 1
        step_folder = f"Step {step} - {len(sections)} sections"

        # Generate summaries for all sections
        summaries = generate_summaries(sections, step, folder_path=step_folder)
        
        step_summary = "\n".join(summaries)
        write_file(f"{step_folder}/Step {step} summary.txt", step_summary)

        sections = token_split_text(step_summary)

    print("Generating final summaries")
    for length in ["Long", "Short", "Very short"]:
        step_summary = gpt_summarize(step_summary, length)
        write_file(f"Final summaries/{length} summary.txt", step_summary)

if __name__ == "__main__":
    main()
