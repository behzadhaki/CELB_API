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
from collections import Counter
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

    def is_valid(self):
        return os.path.exists(self.drum_path) and os.path.exists(self.get_bongo_loop_midi_path())

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
        self.__load_all_attempts(attempts_dir)

        self.attempts = sorted(self.attempts, key=lambda x: x.attempt_duration)
        self.number_of_attempts = len(self.attempts)
        self.user_id = int(attempts_dir.split('SavedSessions/session_')[-1][:8])
        self.attempts_dir = attempts_dir

    def __load_all_attempts(self, attempts_dir_):
        for attempt in os.listdir(attempts_dir_):
            if attempt.startswith('attempt_'):
                temp_attempt = Attempt(os.path.join(attempts_dir_, attempt), self.user_level_of_musical_experience, self.user_exhibion_rating)
                if temp_attempt.is_valid():
                    self.attempts.append(Attempt(os.path.join(attempts_dir_, attempt), self.user_level_of_musical_experience, self.user_exhibion_rating))

    @classmethod
    def from_selected_attempts(cls, attempts_dir, selected_attempts):
        instance = cls(attempts_dir)
        instance.attempts = selected_attempts
        instance.number_of_attempts = len(instance.attempts)
        if instance.number_of_attempts > 0:
            return instance
        else:
            return None

    def get_attempts_with_total_bongo_hits_within_range(self, min_bongo_hits, max_bongo_hits):
        selected_attempts = []
        for attempt in self.attempts:
            bongo_loop_hits = attempt.load_bongo_loop_hvo_seq().hvo[:,:2].sum()
            if min_bongo_hits <= bongo_loop_hits <= max_bongo_hits:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

    def get_attempts_in_tempo_range(self, min_tempo, max_tempo):
        selected_attempts = []
        for attempt in self.attempts:
            if min_tempo <= attempt.attempt_tempo <= max_tempo:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

    def get_attempts_with_with_style(self, style):
        selected_attempts = []
        for attempt in self.attempts:
            if attempt.genre == style:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

    def get_attempts_with_self_assessment_within_range(self, min , max):
        selected_attempts = []
        for attempt in self.attempts:
            if min <= attempt.self_assessment <= max:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

    def get_attempts_with_attempt_duration_minimum(self, min_duration):
        selected_attempts = []
        for attempt in self.attempts:
            if attempt.attempt_duration >= min_duration:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

    def get_attempts_with_assessment_duration_minimum(self, min_duration):
        selected_attempts = []
        for attempt in self.attempts:
            if attempt.assessment_time >= min_duration:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

    def filter_by_user_level_of_musical_experience(self, min_experience, max_experience):
        selected_attempts = []
        for attempt in self.attempts:
            if min_experience <= self.user_level_of_musical_experience <= max_experience:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

    def filter_by_user_exhibion_rating(self, min_rating, max_rating):
        selected_attempts = []
        for attempt in self.attempts:
            if min_rating <= self.user_exhibion_rating <= max_rating:
                selected_attempts.append(attempt)
        return UserAttempts.from_selected_attempts(self.attempts_dir, selected_attempts)

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

    def __len__(self):
        return len(self.attempts)

    def __getitem__(self, item):
        return self.attempts[item]

    def filter_by_genre(self, genre):
        return [a for a in self.attempts if a.genre == genre]


class ElBongoseroCollection:
    def __init__(self, dataset_dir=None):
        self.number_of_users = 0
        self.users = []
        if dataset_dir is not None:
            self._initialize(dataset_dir)
        
    def _initialize(self, dataset_dir):
        folders_ = [f for f in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, f)) and f.startswith('session_')]

        valid_folders = []

        for folder in folders_:
            try:
                if os.path.exists(os.path.join(dataset_dir, folder, 'session_meta.json')):
                    session_metadata = os.path.join(dataset_dir, folder, 'session_meta.json')
                    with open(session_metadata, 'r') as f:
                        session_metadata = json.load(f)

                    if session_metadata['explicitely_granted_consent'].lower() == 'yes':
                        attempts_dir = os.path.join(dataset_dir, folder, 'Part2_BongosAlonWithDrums')
                        if os.path.exists(attempts_dir) and len(os.listdir(attempts_dir)) > 0:
                            valid_folders.append(folder)
            except:
                pass

        self.number_of_users = len(valid_folders)
        self.users = [UserAttempts(os.path.join(dataset_dir, folder, 'Part2_BongosAlonWithDrums')) for folder in valid_folders]

    @classmethod
    def from_attempts_list(cls, select_users):
        instance = cls()
        instance.users = select_users
        instance.number_of_users = len(select_users)
        return instance

    '''
     attempts.get_attempts_with_self_assessment_within_range(0, 3)
    attempts.get_attempts_with_attempt_duration_minimum(22)
    attempts.get_attempts_with_assessment_duration_minimum(24)
    attempts.get_attempts_in_tempo_range(100, 115)
    attempts.get_attempts_with_total_bongo_hits_within_range(0, 13)
    attempts.get_attempts_with_with_style('Punk')'''
    def filter_by_self_assessment_within_range(self, min_attempts, max_attempts):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.get_attempts_with_self_assessment_within_range(min_attempts, max_attempts)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def filter_by_attempt_duration_minimum(self, min_duration):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.get_attempts_with_attempt_duration_minimum(min_duration)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def filter_by_assessment_duration_minimumm(self, min_duration):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.get_attempts_with_attempt_duration_minimum(min_duration)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def filter_by_tempo_range(self, min_tempo, max_tempo):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.get_attempts_in_tempo_range(min_tempo, max_tempo)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def filter_by_total_bongo_hits_within_range(self, min_bongo_hits, max_bongo_hits):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.get_attempts_with_total_bongo_hits_within_range(min_bongo_hits, max_bongo_hits)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def filter_by_style(self, style):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.get_attempts_with_with_style(style)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def filter_by_user_level_of_musical_experience(self, min_experience, max_experience):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.filter_by_user_level_of_musical_experience(min_experience, max_experience)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def filter_by_user_exhibion_rating(self, min_rating, max_rating):
        selected_users = []
        for user_attempts in self.users:
            filtered_attempts = user_attempts.filter_by_user_exhibion_rating(min_rating, max_rating)
            if filtered_attempts is not None:
                if len(filtered_attempts) > 0:
                    selected_users.append(filtered_attempts)
        return ElBongoseroCollection.from_attempts_list(selected_users)

    def get_all_attempts(self):
        attempts = []
        for user in self.users:
            attempts.extend(user.attempts)
        return attempts

    def get_bongo_hits_statistics(self):
        hit_counts = []
        for user in self.users:
            for attempt in user.attempts:
                hit_counts.append(attempt.load_bongo_loop_hvo_seq().hvo[:,:2].sum())
        return {'mean': np.mean(hit_counts), 'std': np.std(hit_counts), 'min': np.min(hit_counts), 'max': np.max(hit_counts)}

    def get_all_styles(self):
        styles = []
        for user in self.users:
            styles.extend([a.genre for a in user.attempts])
        return sorted(list(set(styles)))

    def get_all_attempts_with_style(self, style):
        attempts = []
        for user in self.users:
            attempts.extend([a for a in user.attempts if a.genre == style])
        return attempts

    def get_self_assessment_rating_statistics(self):
        ratings = []
        for user in self.users:
            for attempt in user.attempts:
                ratings.append(attempt.self_assessment)
        return {'mean': np.mean(ratings), 'std': np.std(ratings), 'min': np.min(ratings), 'max': np.max(ratings)}

    def get_exhibition_rating_statistics(self):
        ratings = []
        for user in self.users:
            ratings.append(user.user_exhibion_rating)
        return {'mean': np.mean(ratings), 'std': np.std(ratings), 'min': np.min(ratings), 'max': np.max(ratings)}

    def get_bongo_groove_density_to_drum_density_ratio_statistics(self):
        ratios = []
        for user in self.users:
            for attempt in user.attempts:
                bongo_loop = attempt.load_bongo_loop_hvo_seq().flatten_voices(reduce_dim=True)[:, 0]
                drums = attempt.load_source_drum_hvo_seq().flatten_voices(reduce_dim=True)[:, 0]
                ratios.append(bongo_loop.sum() / drums.sum())
        return {'mean': np.mean(ratios), 'std': np.std(ratios), 'min': np.min(ratios), 'max': np.max(ratios)}

    def count_number_of_attempts_per_style(self):
        styles = []
        for user in self.users:
            styles.extend([a.genre for a in user.attempts])

        res = dict(Counter(styles))

        return {x: res[x] for x in self.get_all_styles()}

    def count_unique_drums_tested_per_style(self):
        files_per_style = {x: [] for x in self.get_all_styles()}
        
        for user in self.users:
            for attempt in user.attempts:
                files_per_style[attempt.genre].append(attempt.drum_path)

        for k, v in files_per_style.items():
            files_per_style[k] = len(set(v))

        # sort alphabetically

        return files_per_style

    def __len__(self):
        return len(self.users)

    def __getitem__(self, item):
        return self.users[item]

    def __repr__(self):
        return f"ElBongoseroCollection with {self.number_of_users} users, total of {len(self.get_all_attempts())} attempts"


if __name__ == "__main__":

    attempts = UserAttempts('SavedSessionToMar12_2024_Noon/SavedSessions/session_00000089/Part2_BongosAlonWithDrums')

    # attempts.get_attempts_with_self_assessment_within_range(0, 3)
    # attempts.get_attempts_with_attempt_duration_minimum(22)
    # attempts.get_attempts_with_assessment_duration_minimum(24)
    # attempts.get_attempts_in_tempo_range(100, 115)
    # attempts.get_attempts_with_total_bongo_hits_within_range(0, 13)
    # attempts.get_attempts_with_with_style('Punk')



    collection = ElBongoseroCollection('SavedSessions/SavedSessions/')
    collection.filter_by_assessment_duration_minimumm(24)
    collection.filter_by_attempt_duration_minimum(22)
    collection.filter_by_self_assessment_within_range(2, 2)
    collection.filter_by_tempo_range(100, 115)
    collection.filter_by_total_bongo_hits_within_range(0, 13)
    collection.filter_by_style('Punk')
    len(collection.get_all_attempts())

    # collection.get_all_styles()
    # collection[0].attempts[0].load_bongo_loop_hvo_seq()
    # collection[0].attempts[0].load_source_drum_hvo_seq()
    # collection[0].attempts[0].load_drums_with_bongos_hvo_sequence()