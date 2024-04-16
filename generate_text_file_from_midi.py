import os
import note_seq
import zipfile
import shutil


def duplicate_folder_structure(source_folder, duplicate_folder):
    """
    Duplicate the structure of a folder.
    @param source_folder: folder to duplicate structure from
    @param duplicate_folder: name of the new folder
    """
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
    """
    Converts MIDI files to text files in a directory and its subdirectories.
    @param directory: path to the directory holding the MIDI files
    """
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
    """"
    Converts a MIDI file path to the text file path.
    @param midi_path: string path to the MIDI file
    @return: string path to the text file
    """
    original_filename = midi_path
    new_filename = original_filename.replace("DrumMidis", "DrumMidisText").replace(".mid", ".txt")
    return new_filename


def zip_folder(folder_path, zip_path):
    """
    Zip a folder.

    Args:
        folder_path (str): Path to the folder to be zipped.
        zip_path (str): Path to the output zip file.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Iterate over each file in the folder
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Calculate the relative path of the file
                relative_path = os.path.relpath(os.path.join(root, file), folder_path)
                # Add the file to the zip file with its relative path
                zipf.write(os.path.join(root, file), relative_path)

    # Delete the original folder after zipping
    shutil.rmtree(folder_path)


def extract_zip(zip_file, extract_dir):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)


def main():
    if not os.path.exists('DrumMidis'):
        extract_zip('DrumMidis.zip', 'DrumMidis')

    # Duplicate the folder structure of the MIDI files
    source_folder = "DrumMidis"
    duplicate_folder = "DrumMidisText"
    duplicate_folder_structure(source_folder, duplicate_folder)

    # Process the MIDI files in the directory
    process_midi_files_in_directory('DrumMidis')

    # Zip the folder
    zip_folder("DrumMidisText", "DrumMidisText.zip")

    # Delete the original unzipped midi folder
    shutil.rmtree("DrumMidis")


if __name__ == "__main__":
    main()