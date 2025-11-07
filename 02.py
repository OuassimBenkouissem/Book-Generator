import requests
import sys
import os
import json
import time

def get_gemini_completion(prompt, api_key, max_retries=5, backoff_factor=1):
    """
    Sends a text prompt to the Gemini API and returns the generated completion with exponential backoff.

    Args:
        prompt (str): The text content to send to the model.
        api_key (str): Your API key for the Google Generative Language API.
        max_retries (int): Maximum number of retries for the API call.
        backoff_factor (int): Factor by which the delay increases.

    Returns:
        str: The completed text from the model, or an error message.
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()

            data = response.json()
            
            candidate = data.get('candidates', [{}])[0]
            content = candidate.get('content', {})
            parts = content.get('parts', [{}])
            completion_part = parts[0]
            completion = completion_part.get('text')

            if completion:
                return completion
            else:
                finish_reason = candidate.get('finishReason', 'unknown')
                return f"API response did not contain text. Finish reason: {finish_reason}. Full response: {json.dumps(data)}"

        except requests.exceptions.HTTPError as errh:
            if response.status_code == 429 and attempt < max_retries - 1:
                wait_time = backoff_factor * (2 ** attempt)
                print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            return f"HTTP Error: {errh}"
        except requests.exceptions.ConnectionError as errc:
            return f"Error Connecting: {errc}"
        except requests.exceptions.Timeout as errt:
            return f"Timeout Error: {errt}"
        except requests.exceptions.RequestException as err:
            return f"An unexpected error occurred: {err}"
        except (KeyError, IndexError) as e:
            return f"Error parsing API response: {e}. Response was: {data}"
    
    return f"Failed after {max_retries} retries due to rate limiting."


def main():
    """
    Main function to process chapter summaries and generate a full novel.
    """
    input_file_path = "story_info_completed.txt"
    chapters_dir = "chapters"
    notes_dir = "continuity_notes"
    
    # Define your API key. Replace the placeholder with your actual key.
    api_key = "AIzaSyCafsaYsQ773XVmGNt9CoY4myrsUQtrM3k" 

    try:
        if not os.path.exists(input_file_path):
            print(f"Error: The file '{input_file_path}' was not found.")
            sys.exit(1)

        with open(input_file_path, 'r', encoding='utf-8') as file:
            input_text = file.read()
        
        chapter_summaries = [s.strip() for s in input_text.split('\n\n') if s.strip()]
        if not chapter_summaries:
            print("The input file is empty or improperly formatted. No chapters will be generated.")
            sys.exit(1)

        os.makedirs(chapters_dir, exist_ok=True)
        os.makedirs(notes_dir, exist_ok=True)
        
        continuity_note = ""
        for i, summary in enumerate(chapter_summaries):
            chapter_number = i + 1
            
            chapter_file_path = os.path.join(chapters_dir, f"chapter_{chapter_number}.txt")
            note_file_path = os.path.join(notes_dir, f"note_chapter_{chapter_number}.txt")
            
            # Check if chapter and its note already exist to resume generation
            if os.path.exists(chapter_file_path) and os.path.exists(note_file_path):
                print(f"Chapter {chapter_number} and its continuity note already exist. Skipping.")
                with open(note_file_path, 'r', encoding='utf-8') as f:
                    continuity_note = f.read()
                continue
            
            # Load the continuity note from the previous chapter if it exists
            if chapter_number > 1:
                prev_note_path = os.path.join(notes_dir, f"note_chapter_{chapter_number - 1}.txt")
                if os.path.exists(prev_note_path):
                    with open(prev_note_path, 'r', encoding='utf-8') as f:
                        continuity_note = f.read()
                else:
                    print(f"Error: Previous continuity note for chapter {chapter_number - 1} was not found.")
                    print("Please ensure all previous chapters were generated successfully or delete incomplete files to restart.")
                    break

            print(f"Generating chapter {chapter_number}...")

            if chapter_number == 1:
                prompt_text = (
                    f"Write the full first chapter of a novel based on the following summary. Aim for a chapter of approximately 1000-1500 words. "
                    f"Use advanced narrative techniques, rich setting detail, point-of-view interiority, recurring motifs, "
                    f"and realistic dialogue. The chapter should end with a strong cliffhanger or closing beat.\n\nSummary:\n{summary}"
                )
            else:
                prompt_text = (
                    f"Continue the novel. Write the full chapter {chapter_number} based on the following summary and the preceding continuity note. "
                    f"Aim for a chapter of approximately 1000-1500 words. Use advanced narrative techniques, rich setting detail, "
                    f"point-of-view interiority, recurring motifs, and realistic dialogue. The chapter should end with a strong "
                    f"cliffhanger or closing beat.\n\nContinuity Note:\n{continuity_note}\n\nSummary for this chapter:\n{summary}"
                )
            
            # Get the full chapter from the API
            chapter_text = get_gemini_completion(prompt_text, api_key)

            if chapter_text.startswith("API response did not contain text") or chapter_text.startswith("Error"):
                print(f"Failed to generate chapter {chapter_number}. Error: {chapter_text}")
                break

            # Save the chapter to a new file
            with open(chapter_file_path, 'w', encoding='utf-8') as file:
                file.write(chapter_text)
            
            print(f"Successfully generated chapter {chapter_number}. Saved to '{chapter_file_path}'.")

            # Generate and save a summary for the next chapter's continuity note
            summary_prompt = f"Write a concise summary of the following chapter to maintain continuity for the next chapter's writing. The summary should capture the key events and character developments.\n\nChapter Text:\n{chapter_text}"
            continuity_note = get_gemini_completion(summary_prompt, api_key)
            
            if continuity_note.startswith("API response did not contain text") or continuity_note.startswith("Error"):
                print(f"Failed to generate continuity note for chapter {chapter_number}. Error: {continuity_note}")
                break
            
            with open(note_file_path, 'w', encoding='utf-8') as file:
                file.write(continuity_note)

            print(f"Continuity note for chapter {chapter_number + 1} generated successfully and saved to '{note_file_path}'.")
            
        print("\nNovel generation complete!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
