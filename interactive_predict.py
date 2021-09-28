import traceback

from common import common
from extractor import Extractor
from pathlib import Path
import inspect
import time
from numpy import mean, median, quantile
import json
import pandas as pd

SHOW_TOP_CONTEXTS = 10
MAX_PATH_LENGTH = 8
MAX_PATH_WIDTH = 2
JAR_PATH = 'JavaExtractor/JPredict/target/JavaExtractor-0.0.1-SNAPSHOT.jar'


class InteractivePredictor:
    exit_keywords = ['exit', 'quit', 'q']

    def __init__(self, config, model):
        model.predict([])
        self.model = model
        self.config = config
        self.model.prepare()
        self.results = {}
        self.java = {}
        self.path_extractor = Extractor(config,
                                        jar_path=JAR_PATH,
                                        max_path_length=MAX_PATH_LENGTH,
                                        max_path_width=MAX_PATH_WIDTH)

    def read_file(self, input_filename):
        with open(input_filename, 'r') as file:
            return file.readlines()

    def predict(self, path_folder):
        files_list = list(Path(path_folder).glob('*.java'))
        for input_filename in files_list:
            file_name_str = str(input_filename)
            # input_filename = Path('temp.java')
            with open(file_name_str) as f:
                code = f.read()
                start = time.time()
                predict_lines, hash_to_string_dict = self.path_extractor.extract_paths(code, file_name_str)
                java_end = time.time()
                end = time.time()
                p_java = java_end - start
                #with open('inspect.txt', 'w') as w:
                    #w.write(inspect.getsource(self.model))
                raw_prediction_results = self.model.predict(predict_lines)
                end = time.time()
                self.java[file_name_str] = p_java
                p = end - start
                self.results[file_name_str] = p
                print(f'Time passed: {p} for {file_name_str}')

                method_prediction_results = common.parse_prediction_results(
                    raw_prediction_results, hash_to_string_dict,
                    self.model.vocabs.target_vocab.special_words, topk=SHOW_TOP_CONTEXTS)
                for raw_prediction, method_prediction in zip(raw_prediction_results, method_prediction_results):
                    print('Original name:\t' + method_prediction.original_name)
                    for name_prob_pair in method_prediction.predictions:
                        print('\t(%f) predicted: %s' % (name_prob_pair['probability'], name_prob_pair['name']))
        total_time_for_one_iteration = sum(self.results.values())
        times_arr = list(self.results.values())
        print(f'Total time of running {len(files_list)} java methods is '
              f'{total_time_for_one_iteration} secs for 1 iteration. \n'
              f'Average time for 1 method: {mean(times_arr):0.3f} secs. \n'
              f'Min time of 1 method: {min(times_arr):0.3f} secs, \n'
              f'max time of 1 method: {max(times_arr):0.3f} secs, \n'
              f'median: {median(times_arr):0.3f} secs, \n'
              f'quantile 75%: {quantile(times_arr, 0.75):0.3f} secs, \n'
              f'quantile 95%: {quantile(times_arr, 0.95):0.3f} secs')
        all_res = json.dumps(self.results)
        df = pd.DataFrame(columns=['filename', 'total_time', 'preprocess', 'predict_time'])
        print(f'All results: {all_res}')
        for filename, total_time in self.results.items():
            preprocess_time = self.java[filename]
            df = df.append({'filename': filename, 'total_time': total_time, 'preprocess': preprocess_time, 'predict_time': total_time - preprocess_time}, ignore_index=True)
        df.to_csv('res.csv')
