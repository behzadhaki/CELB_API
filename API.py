import pandas
import pandas as pd
from collections import defaultdict
import note_seq
import os
import shutil
import numpy as np
import tqdm
from copy import deepcopy
import random
import json
import time
from hvo_sequence.io_helpers import midi_to_hvo_sequence
from hvo_sequence.drum_mappings import ROLAND_REDUCED_MAPPING, ROLAND_REDUCED_MAPPING_With_Bongos, BONGOSERRO_MAPPING
def time_string(time_string):
    return time.mktime(time.strptime(time_string, "%Y-%m-%d %H:%M:%S.%f"))


class Attempt:
    def __init__(self, attempt_dir, user_level_of_musical_experience, user_exhibion_rating):

        # load json
        path_ = os.path.join(attempt_dir, 'groove_metadata.json')
        with open(path_, 'r') as f:
            meta = json.load(f)

        start_time = time_string(meta['cleared_to_retry_times'][-1])
        submit_time = time_string(meta['groove_submission_time'])

        self.attempt_duration = submit_time - start_time

        self.self_assessment = meta['self_assessment_rating'][-1][0]

        assessment_time = time_string(meta['self_assessment_rating'][-1][1])
        self.assessment_time = assessment_time - start_time

        self.attempt_tempo = meta['tempos'][-1][0]

        self.drum_path = meta['midi_drum_path'][0][0].split('My Drive/')[-1]

        self.metadata_json = os.path.join(attempt_dir, 'groove_metadata.json')

        self.genre = self.drum_path.split('/')[1]

        self.user_level_of_musical_experience = user_level_of_musical_experience
        self.user_exhibion_rating = user_exhibion_rating

    def get_bongo_loop_midi_path(self):
        return self.metadata_json.replace('groove_metadata.json', 'SavedAsUserSubmitted/bongosLoop.mid')

    def __repr__(self):
        return self.__dict__.__repr__()

    def load_source_drum_hvo_seq(self, drum_mapping=ROLAND_REDUCED_MAPPING):
        hs = midi_to_hvo_sequence(self.drum_path, drum_mapping=drum_mapping, beat_division_factors=[4])
        hs.adjust_length(32)
        return hs

    def load_bongo_loop_hvo_seq(self, bongo_mapping=BONGOSERRO_MAPPING):
        hs = midi_to_hvo_sequence(self.get_bongo_loop_midi_path(), drum_mapping=bongo_mapping, beat_division_factors=[4])
        hs.adjust_length(32)
        return hs

    def load_drums_with_bongos_hvo_sequence(self, drum_mapping=ROLAND_REDUCED_MAPPING, bongo_mapping=BONGOSERRO_MAPPING):
        collective_map = bongo_mapping.copy()
        collective_map.update(drum_mapping)
        hvo_seq_drums = self.load_source_drum_hvo_seq(drum_mapping=collective_map)
        bongo_mapping = self.load_bongo_loop_hvo_seq(bongo_mapping=collective_map)
        hvo_seq_total = hvo_seq_drums.copy()
        hvo_seq_total.hvo = hvo_seq_total.hvo + bongo_mapping.hvo
        return hvo_seq_total


    def load_source_drum_note_seq(self):
        return note_seq.midi_file_to_note_sequence(self.drum_path)

    def load_bongo_loop_note_seq(self):
        return note_seq.midi_file_to_note_sequence(self.get_bongo_loop_midi_path())


class UserAttempts:
    def __init__(self, attempts_dir):

        # load ../session_metadata.json
        session_metadata = attempts_dir.replace('Part2_BongosAlonWithDrums', 'session_meta.json')

        with open(session_metadata, 'r') as f:
            meta = json.load(f)
            try:
                self.user_level_of_musical_experience = meta['level_of_musical_experience'][-1]["rating"]
                self.user_exhibion_rating = meta['exhibition_rating'][-1]["rating"]
            except:
                self.user_level_of_musical_experience = -1
                self.user_exhibion_rating = -1

        # check how many attempt_** folders are in the attempts_dir
        self.attempts = []
        for attempt in os.listdir(attempts_dir):
            if attempt.startswith('attempt_'):
                self.attempts.append(Attempt(os.path.join(attempts_dir, attempt), self.user_level_of_musical_experience, self.user_exhibion_rating))

        self.attempts = sorted(self.attempts, key=lambda x: x.attempt_duration)
        self.number_of_attempts = len(self.attempts)
        self.user_id = int(attempts_dir.split('SavedSessions/session_')[-1][:8])

    def __repr__(self):
        text = '----------------------------------------\n'
        text += 'User ID: ' + str(self.user_id) + '\n'
        text += 'Number of attempts: ' + str(self.number_of_attempts) + '\n'
        text += 'User Level of Musical Experience: ' + str(self.user_level_of_musical_experience) + '\n'
        text += 'User Exhibition Rating: ' + str(self.user_exhibion_rating) + '\n'
        for i, attempt in enumerate(self.attempts):
            text += f'Attempt {i+1}:\n'
            text += attempt.__repr__() + '\n'
        text += '----------------------------------------\n'
        return text

class ElBongoseroCollection:
    def __init__(self, dataset_dir):

        folders_ = [f for f in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, f)) and f.startswith('session_')]

        valid_folders = []

        for folder in folders_:
            try:
                # open session_meta.json
                if os.path.exists(os.path.join(dataset_dir, folder, 'session_meta.json')):
                    session_metadata = os.path.join(dataset_dir, folder, 'session_meta.json')
                    with open(session_metadata, 'r') as f:
                        session_metadata = json.load(f)

                    if session_metadata['explicitely_granted_consent'].lower() == 'yes':
                        # check if there is at least one attempt
                        attempts_dir = os.path.join(dataset_dir, folder, 'Part2_BongosAlonWithDrums')
                        if os.path.exists(attempts_dir):
                            valid_folders.append(folder)
            except:
                pass

        self.number_of_users = len(valid_folders)

        self.user_attempts = []

        for folder in valid_folders:
            self.user_attempts.append(UserAttempts(os.path.join(dataset_dir, folder, 'Part2_BongosAlonWithDrums')))

    def get_all_attempts(self):
        attempts = []
        for user in self.user_attempts:
            attempts.extend(user.attempts)
        return attempts

    def __len__(self):
        return len(self.user_attempts)

    def __getitem__(self, item):
        return self.user_attempts[item]

if __name__ == "__main__":

    attempts = UserAttempts('SavedSessionToMar12_2024_Noon/SavedSessions/session_00000089/Part2_BongosAlonWithDrums')
    print(attempts)

    collection = ElBongoseroCollection('SavedSessionToMar12_2024_Noon/SavedSessions/')

    collection[0].attempts[0].load_bongo_loop_hvo_seq(bongo_mapping=BONGOSERRO_MAPPING)
    collection[0].attempts[0].load_source_drum_hvo_seq(drum_mapping=ROLAND_REDUCED_MAPPING_With_Bongos)
    collection[0].attempts[0].load_drums_with_bongos_hvo_sequence(drum_mapping=ROLAND_REDUCED_MAPPING, bongo_mapping=BONGOSERRO_MAPPING)