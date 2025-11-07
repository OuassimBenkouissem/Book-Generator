import requests
import sys
import os
import json

def get_gemini_completion(prompt, api_key):
    """
    Sends a text prompt to the Gemini API and returns the generated completion.

    Args:
        prompt (str): The text content to send to the model.
        api_key (str): Your API key for the Google Generative Language API.

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

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        
        # Extract the generated text from the nested JSON structure
        completion = data['candidates'][0]['content']['parts'][0]['text']
        return completion

    except requests.exceptions.HTTPError as errh:
        return f"HTTP Error: {errh}"
    except requests.exceptions.ConnectionError as errc:
        return f"Error Connecting: {errc}"
    except requests.exceptions.Timeout as errt:
        return f"Timeout Error: {errt}"
    except requests.exceptions.RequestException as err:
        return f"An unexpected error occurred: {err}"
    except (KeyError, IndexError) as e:
        return f"Error parsing API response: {e}. Response was: {data}"

def main():
    """
    Main function to handle file processing and API call.
    """
    # Check for the correct number of command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python gemini_file_completer.py <input_file_path>")
        sys.exit(1)

    input_file_path = sys.argv[1]
    
    # Define your API key. Replace the placeholder with your actual key.
    api_key = "AIzaSyDK7qwSMgdPlyIpWlZtsbahoyqICniKLqY" 

    try:
        # Read the content of the input file
        with open(input_file_path, 'r', encoding='utf-8') as file:
            prompt_text = file.read()
        
        if not prompt_text.strip():
            print("The input file is empty. No completion will be generated.")
            sys.exit(1)

        print(f"Sending content from '{input_file_path}' to the Gemini API...")

        # Get the completion from the API
        completed_text = get_gemini_completion(prompt_text, api_key)

        # Create the output file path
        file_name, file_extension = os.path.splitext(input_file_path)
        output_file_path = f"{file_name}_completed{file_extension}"
        
        # Write the completed text to a new file
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(completed_text)
            
        print(f"Successfully generated completion. The result has been saved to '{output_file_path}'.")

    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
