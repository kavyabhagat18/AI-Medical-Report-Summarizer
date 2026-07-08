from text_processing.regex_filters import apply_regex
from text_processing.clean_text import fix_ocr_errors
from text_processing.formatter import format_text

# Ask user for input file
input_file = input("Enter report filename: ")

# Read report
with open(input_file, "r", encoding="utf-8") as file:
    text = file.read()

# Process report
text = apply_regex(text)
text = fix_ocr_errors(text)
text = format_text(text)

# Save cleaned report
output_file = "cleaned_" + input_file

with open(output_file, "w", encoding="utf-8") as file:
    file.write(text)

# Display cleaned report
print("\n----- CLEANED REPORT -----\n")
print(text)

print("\nReport cleaned successfully!")
print("Saved as:", output_file)