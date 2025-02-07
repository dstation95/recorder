import json
import os

def combine_files(input_file, output_file, combined_file):
    # Read the training input JSON.
    with open(input_file, "r", encoding="utf-8") as f:
        training_input = json.load(f)
    
    # Read the training output JSON.
    with open(output_file, "r", encoding="utf-8") as f:
        training_output = json.load(f)
    
    # Combine into a single record with keys "input" and "output".
    combined = {
        "input": training_input,
        "output": training_output
    }
    
    # If the combined dataset file does not exist, create it.
    if not os.path.exists(combined_file):
        with open(combined_file, "w", encoding="utf-8") as f:
            pass  # create empty file
    
    # Append the combined record as a new JSON line.
    with open(combined_file, "a", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False)
        f.write("\n")
    
    print(f"Appended combined record to {combined_file}")

if __name__ == "__main__":
    # Define the file names. Adjust these if needed.
    input_file = "training_input.json"     # Contains the UI snapshot and task instruction
    output_file = "training_output.json"   # Contains the runtime_id of the clicked element
    combined_file = "combined_dataset.jsonl"  # This file will contain one record per line
    
    combine_files(input_file, output_file, combined_file)
