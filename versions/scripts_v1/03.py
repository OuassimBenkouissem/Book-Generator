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
    Main function to read chapters, enhance them with sensory details, and save them.
    """
    input_dir = "chapters"
    output_dir = "chapters_2"

    # Define your API key. Replace the placeholder with your actual key.
    api_key = "AIzaSyDK7qwSMgdPlyIpWlZtsbahoyqICniKLqY" 

    try:
        if not os.path.exists(input_dir):
            print(f"Error: The input directory '{input_dir}' was not found.")
            sys.exit(1)

        os.makedirs(output_dir, exist_ok=True)
        
        chapter_files = sorted([f for f in os.listdir(input_dir) if f.startswith("chapter_") and f.endswith(".txt")])
        if not chapter_files:
            print(f"No chapter files found in '{input_dir}'.")
            sys.exit(0)

        for file_name in chapter_files:
            input_file_path = os.path.join(input_dir, file_name)
            output_file_path = os.path.join(output_dir, file_name)

            if os.path.exists(output_file_path):
                print(f"Enhanced chapter '{file_name}' already exists. Skipping.")
                continue

            print(f"Processing '{file_name}'...")
            with open(input_file_path, 'r', encoding='utf-8') as file:
                chapter_text = file.read()
            
            prompt = (
                f"Read the following chapter of a novel. Your task is to rewrite the chapter, "
                f"adding a significant amount of descriptive and sensory detail to make the world feel more immersive and "
                f"the characters' experiences more vivid. Focus on enriching descriptions related to "
                f"sight, sound, smell, taste, and touch. Do not change the core plot or dialogue, but "
                f"expand upon the existing narrative to make it more descriptive and detailed. "
                f"The rewritten chapter should be significantly longer than the original. "
                f"Here is the chapter text:\n\n{chapter_text}"
            )
            
            enhanced_chapter = get_gemini_completion(prompt, api_key)

            if enhanced_chapter.startswith("API response did not contain text") or enhanced_chapter.startswith("Error"):
                print(f"Failed to enhance '{file_name}'. Error: {enhanced_chapter}")
                continue

            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(enhanced_chapter)
            
            print(f"Successfully enhanced '{file_name}'. Saved to '{output_file_path}'.")
            
        print("\nAll chapters enhanced successfully!")

        print("\nChecking word counts and re-generating chapters under 2000 words...")
        
        regenerate_dir = "chapters_2"
        regenerate_files = sorted([f for f in os.listdir(regenerate_dir) if f.startswith("chapter_") and f.endswith(".txt")])

        for file_name in regenerate_files:
            file_path = os.path.join(regenerate_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                word_count = len(content.split())
            
            print(f"'{file_name}': {word_count} words.")
            
            if word_count < 2000:
                print(f"Word count is under 2000. Re-generating '{file_name}' to be between 2000-3000 words.")
                
                # Use a slightly different prompt to aim for the new length
                prompt = (
                    f"Read the following chapter of a novel. Your task is to rewrite the chapter, "
                    f"adding a significant amount of descriptive and sensory detail to make the world feel more immersive and "
                    f"the characters' experiences more vivid. The final output should be between 2000 and 3000 words long. "
                    f"Do not change the core plot or dialogue, but expand upon the existing narrative to make it more "
                    f"descriptive and detailed. Here is the chapter text:\n\n{content}"
                )
                
                regenerated_chapter = get_gemini_completion(prompt, api_key)
                
                if regenerated_chapter.startswith("API response did not contain text") or regenerated_chapter.startswith("Error"):
                    print(f"Failed to re-generate '{file_name}'. Error: {regenerated_chapter}")
                    continue

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(regenerated_chapter)
                
                new_word_count = len(regenerated_chapter.split())
                print(f"Successfully re-generated '{file_name}'. New word count: {new_word_count} words.")
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
