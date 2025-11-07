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
    Main function to read story info and generate a blurb.
    """
    story_info_file = "story_info.txt"
    output_blurb_file = "blurb.txt"
    api_key = "AIzaSyDK7qwSMgdPlyIpWlZtsbahoyqICniKLqY" 

    try:
        if not os.path.exists(story_info_file):
            print(f"Error: The file '{story_info_file}' was not found.")
            sys.exit(1)

        print(f"Reading story information from '{story_info_file}'...")
        with open(story_info_file, 'r', encoding='utf-8') as file:
            story_info = file.read()
        
        prompt = (
            f"Read the following information about a novel and generate a concise and compelling book blurb for the back cover. "
            f"The blurb should introduce the main characters, the central conflict, and the stakes of the story, "
            f"while leaving the reader wanting to know more. After the main blurb, include a section titled 'What you'll find' that lists 3-5 key elements or themes of the story in a clear, concise manner. "
            f"Keep the tone engaging and mysterious. Here is the story information:\n\n{story_info}"
        )
        
        blurb = get_gemini_completion(prompt, api_key)

        if blurb.startswith("API response did not contain text") or blurb.startswith("Error"):
            print(f"Failed to generate blurb. Error: {blurb}")
            sys.exit(1)

        print("\n--- Generated Book Blurb ---")
        print(blurb)
        print("----------------------------")

        with open(output_blurb_file, 'w', encoding='utf-8') as file:
            file.write(blurb)
        
        print(f"Successfully generated blurb. Saved to '{output_blurb_file}'.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
