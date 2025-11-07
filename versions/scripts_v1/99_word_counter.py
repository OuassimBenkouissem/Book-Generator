import os
import sys

def main():
    """
    Reads all text files from the 'chapters_2' directory,
    counts the words in each file, and then calculates the total word count.
    """
    directory = "chapters_2"
    total_word_count = 0

    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"Error: The directory '{directory}' was not found.")
        sys.exit(1)
        
    print(f"Reading chapters from '{directory}'...")
    print("---------------------------------")

    # Get a list of all chapter files and sort them numerically
    try:
        chapter_files = sorted([f for f in os.listdir(directory) if f.startswith("chapter_") and f.endswith(".txt")],
                               key=lambda x: int(''.join(filter(str.isdigit, x))))
    except Exception as e:
        print(f"Error reading directory or sorting files: {e}")
        sys.exit(1)

    if not chapter_files:
        print(f"No chapter files found in '{directory}'.")
        sys.exit(0)

    # Loop through each chapter file
    for file_name in chapter_files:
        file_path = os.path.join(directory, file_name)
        word_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # A simple way to count words is to split the content by whitespace
                words = content.split()
                word_count = len(words)
                total_word_count += word_count
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            continue
        except Exception as e:
            print(f"An error occurred while processing {file_name}: {e}")
            continue

        print(f"{file_name}: {word_count} words")
        
    print("---------------------------------")
    print(f"Total word count for all chapters: {total_word_count}")

if __name__ == "__main__":
    main()
