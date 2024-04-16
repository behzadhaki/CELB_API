import os
import note_seq

def duplicate_folder_structure(source_folder, duplicate_folder):
    # Create the duplicate folder if it doesn't exist
    if not os.path.exists(duplicate_folder):
        os.makedirs(duplicate_folder)

    # Iterate over each item in the source folder
    for item in os.listdir(source_folder):
        item_path = os.path.join(source_folder, item)
        duplicate_item_path = os.path.join(duplicate_folder, item)
        # If it's a directory, recursively duplicate its structure
        if os.path.isdir(item_path):
            duplicate_folder_structure(item_path, duplicate_item_path)
        # If it's a file, ignore it
        else:
            continue

def process_midi_files_in_directory(directory):
    # Loop through files and folders in the current directory
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        # Check if it's a directory
        if os.path.isdir(item_path):
            # Recursively call the function for subdirectories
            process_midi_files_in_directory(item_path)
        else:
            # Check if it's a MIDI file
            if item.endswith('.mid'):
              # print(item_path)
              note_sequence = note_seq.midi_file_to_note_sequence(item_path)
              midi_text_file_path = convert_midi_file_path_to_text_file_path(item_path)
              with open(midi_text_file_path, 'w') as file:
                for tempo in note_sequence.tempos:
                  file.write(str(tempo.qpm))
                for note in note_sequence.notes:
                    # Write content to the file
                    quarter_notes = (tempo.qpm * note.start_time) / 60
                    file.write('\n' + str(note.pitch) + ', ' + str(note.velocity) + ', ' + str(note.start_time) + ', ' + str(quarter_notes))

def convert_midi_file_path_to_text_file_path(midi_path):
  # Original file name
  original_filename = midi_path

  # Replace "DrumMidis" with "DrumMidisText"
  new_filename = original_filename.replace("DrumMidis", "DrumMidisText").replace(".mid", ".txt")
  return new_filename


def main():
    source_folder = "DrumMidis"
    duplicate_folder = "DrumMidisText"
    duplicate_folder_structure(source_folder, duplicate_folder)

    process_midi_files_in_directory('DrumMidis')

if __name__ == "__main__":
    main()