import argparse
import os
import openai
import time
import token_helper

'''
This will split a long text into parts long enough for ChatGPT to handle.
It will then summarize each section to create a new text.
This will repeat until there is only one section left to produce a long, a short and a very short summary.
Each step is saved in its own folder.
'''

# Set up OpenAI API credentials, model to use, and maximum token amount for each section
openai.api_key = "YOUR_API_KEY_HERE"
gpt_model = "gpt-3.5-turbo"
max_tokens = 2000 # Set this to half of the maximum tokens for your chosen model. It is 4096 for gpt-3.5-turbo.
rate_limit = 3 # The amount of API calls that can be made per minute. It is 3 for the most basic, free account.

# Function to split the text into sections based on token limit
def token_split_text(text):
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
        print(f"Section {len(sections)+1}: {tokens} tokens, {len(section)} characters")
        sections.append([section.strip(), tokens]) # [section_text, token_count]
        tokens = 0
        section = ""
    return sections

# Function to summarize a section using ChatGPT
def gpt_summarize(section_text, token_count, length="long", important_part=None):
    retry_count = 0
    max_tries = 99
    messages = [
        {"role": "user", "content": f"Your task is to generate a {length} summary of the following text ignoring chapter numbers/names. Start from the beginning and progress through to the end.\nHere is the text:\n{section_text}"}
    ]
    if important_part:
        messages.append({"role": "system", "content": f"The {important_part} of the text is important and has priority."})

    while retry_count < max_tries:
        try:
            response = openai.ChatCompletion.create(
                model=gpt_model,
                messages=messages,
                temperature=0.3
            )
            summary = response.choices[0].message.get("content", "").strip()
            print("Section length:", len(section_text), "Summary length:", len(summary))
            return summary
        except Exception as e:
            print("An error occurred during summary generation:", str(e))
            print("Retrying in 60 seconds...")
            time.sleep(60)
            retry_count += 1
    print(f"Failed to generate summary for section after {max_tries} tries")
    exit()

# Function to generate summaries for all sections
def generate_summaries(text_parts, step, folder_path=None):
    summaries = []

    api_call_count = 0 # Handle rate_limit
    start_time = time.time()  # Track start time

    amount_of_parts = len(text_parts)

    print(f"\nStep {step}")
    for i, section in enumerate(text_parts):
        print("Summarizing section", i+1)
        if amount_of_parts > 1:
            if i == 0:
                important_part = "beginning"
            elif i == amount_of_parts:
                important_part = "ending"
        elif amount_of_parts == 1:
            important_part = "beginning and ending"
        summary = gpt_summarize(*section, "long", important_part)
        summaries.append(summary)
        api_call_count += 1

        # Save the summary to a file in the specified folder path
        if folder_path:
            write_file(folder_path, f"Section {i+1} summary", summary)

        if api_call_count == rate_limit:
            elapsed_time = time.time() - start_time
            if elapsed_time < 60:
                print(f"{'='*20}\nRate limit reached. Pausing for {61 - int(elapsed_time)} seconds.")
                time.sleep(61 - int(elapsed_time))
            api_call_count = 0
            start_time = time.time()  # Reset start time
    return summaries

# Function to write text to a file
def write_file(folder_path, file_name, text):
    os.makedirs(folder_path, exist_ok=True)
    with open(f"{folder_path}/{file_name}.txt", "w") as file:
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
        write_file(step_folder, f"/Step {step} summary", step_summary)

        sections = token_split_text(step_summary)

    print("Generating final summaries")
    for i, length in enumerate(["Long", "Short", "Very short"]):
        summary_tokens = int(token_helper.token_counter(step_summary, gpt_model))
        step_summary = gpt_summarize(step_summary, summary_tokens, length)
        write_file("Final summaries", f"{length} summary", step_summary)

if __name__ == "__main__":
    main()
