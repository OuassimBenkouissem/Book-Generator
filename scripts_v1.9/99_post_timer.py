import os
import sys
from datetime import datetime, timedelta

def main():
    """
    Reads a chapter titles file and adds a posting date to each title.
    """
    titles_file = "chapter_titles.txt"
    
    try:
        if not os.path.exists(titles_file):
            print(f"Error: The file '{titles_file}' was not found.")
            sys.exit(1)

        print(f"Reading chapter titles from '{titles_file}'...")
        with open(titles_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Remove header lines
        if lines and "Generated Chapter Titles" in lines[0]:
            lines = lines[2:]

        # Get current time and set the hour to 3 a.m. for the first post
        current_time = datetime.now().replace(hour=3, minute=0, second=0, microsecond=0)
        
        updated_lines = []
        for i, line in enumerate(lines):
            if not line.strip():
                continue

            # Remove any existing posting date from the line to prevent duplicates
            if "(Posted:" in line:
                line = line.split("(Posted:")[0].strip()

            # Assuming the format is "chapter_xx.txt: Title"
            try:
                file_name, title = line.split(":", 1)
                file_name = file_name.strip()
                title = title.strip()
            except ValueError:
                # Handle lines that don't match the expected format
                updated_lines.append(line.strip() + " - [Could not parse line]\n")
                continue

            # Determine the posting date based on the chapter index
            if i == 0:
                # First chapter: post at 3 a.m.
                post_date = current_time
            elif i < 10:
                # Chapters 2-10: 1 hour after the previous chapter
                post_date = current_time + timedelta(hours=i)
            else:
                # Rest of chapters: 1 day apart, starting from the day after chapter 10
                # First day is for the first 10 chapters. Day 2 starts with chapter 11
                # The index for these chapters starts at 10, so subtract 9 to get the day offset
                day_offset = (i - 9)
                
                # Set the base date to be the start of the next day (midnight)
                base_date = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Add the correct number of days and set the time to 3 AM
                post_date = base_date + timedelta(days=day_offset - 1, hours=3)

            # Format the line with the posting date for better readability
            formatted_line = f"{file_name}: {title}\n  (Posted: {post_date.strftime('%Y-%m-%d %I:%M %p')})\n"
            updated_lines.append(formatted_line)
        
        # Write the updated content back to the file
        with open(titles_file, 'w', encoding='utf-8') as outfile:
            outfile.write("Generated Chapter Titles\n")
            outfile.write("------------------------\n\n")
            for line in updated_lines:
                outfile.write(line)
            
        print(f"\nSuccessfully updated '{titles_file}' with posting dates.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
