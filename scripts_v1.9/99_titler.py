import requests
import sys
import os
import json
import time

def get_gemini_completion(prompt, api_key, max_retries=5, backoff_factor=1):
    """
    Sends a text prompt to the Gemini API and returns the generated completion.
    Includes exponential backoff for rate limit handling.

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
        except requests.exceptions.RequestException as err:
            return f"An unexpected error occurred: {err}"
        except (KeyError, IndexError) as e:
            return f"Error parsing API response: {e}. Response was: {json.dumps(data)}"
    
    return f"Failed after {max_retries} retries due to rate limiting."

def main():
    """
    Main function to read chapters and generate titles for them.
    """
    input_dir = "chapters_2"
    output_file = "chapter_titles.txt"

    # Define your API key. Replace the placeholder with your actual key.
    api_key = "AIzaSyDK7qwSMgdPlyIpWlZtsbahoyqICniKLqY" 

    try:
        if not os.path.exists(input_dir):
            print(f"Error: The input directory '{input_dir}' was not found.")
            sys.exit(1)

        chapter_files = sorted([f for f in os.listdir(input_dir) if f.startswith("chapter_") and f.endswith(".txt")],
                               key=lambda x: int(''.join(filter(str.isdigit, x))))
        
        if not chapter_files:
            print(f"No chapter files found in '{input_dir}'.")
            sys.exit(0)

        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write("Generated Chapter Titles\n")
            outfile.write("------------------------\n\n")

            for file_name in chapter_files:
                input_file_path = os.path.join(input_dir, file_name)

                print(f"Generating title for '{file_name}'...")
                with open(input_file_path, 'r', encoding='utf-8') as file:
                    chapter_text = file.read()
                
                # Truncate the chapter to the first 1000 characters to save tokens and speed up API calls.
                truncated_text = chapter_text[:1000]

                prompt = (
                    f"Read the following excerpt from a novel chapter. Based on the content, generate a concise, compelling, "
                    f"and memorable title for this chapter. The title should capture the essence or a key event "
                    f"of the chapter. Respond with only the title text, and nothing else. "
                    f"Here is the chapter excerpt:\n\n{truncated_text}"
                )
                
                title = get_gemini_completion(prompt, api_key)

                if title.startswith("API response did not contain text") or title.startswith("Error"):
                    print(f"Failed to generate title for '{file_name}'. Error: {title}")
                    outfile.write(f"{file_name}: [Title Generation Failed]\n")
                    continue

                outfile.write(f"{file_name}: {title.strip()}\n")
                print(f"Successfully generated title for '{file_name}': {title.strip()}")
            
        print(f"\nAll titles generated successfully! Saved to '{output_file}'.")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
