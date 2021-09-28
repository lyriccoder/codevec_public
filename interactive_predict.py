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
        self.java = {}
        self.predict_d = {}
        self.redis = {}
        self.path_extractor = Extractor(config,
                                        jar_path=JAR_PATH,
                                        max_path_length=MAX_PATH_LENGTH,
                                        max_path_width=MAX_PATH_WIDTH)

    def read_file(self, input_filename):
        with open(input_filename, 'r') as file:
            return file.readlines()

    def predict(self, path_folder):
        print(0)
        files_list = list(Path(path_folder).glob('*.java'))
        for input_filename in files_list:
            file_name_str = str(input_filename)
            # input_filename = Path('temp.java')
            with open(file_name_str) as f:
                code = f.read()
                #################
                # Extract paths with redis, without loading Java VM
                start_redis = time.time()
                predict_lines, hash_to_string_dict = self.path_extractor.extract_paths_with_redis(code, file_name_str)
                end_redis = time.time()
                p_redis = end_redis - start_redis
                self.redis[file_name_str] = p_redis
                ##################
                # Extract paths with redis, with running Java VM
                start_java = time.time()
                predict_lines, hash_to_string_dict = self.path_extractor.extract_paths(code, file_name_str)
                java_end = time.time()
                p_java = java_end - start_java
                self.java[file_name_str] = p_java
                #################
                #with open('inspect.txt', 'w') as w:
                    #w.write(inspect.getsource(self.model))
                start_predict = time.time()
                raw_prediction_results = self.model.predict(predict_lines)
                end = time.time()
                p_predict = end - start_predict
                self.predict_d[file_name_str] = p_predict
                #print(f'Time passed: {p} for {file_name_str}')

                method_prediction_results = common.parse_prediction_results(
                    raw_prediction_results, hash_to_string_dict,
                    self.model.vocabs.target_vocab.special_words, topk=SHOW_TOP_CONTEXTS)
                for raw_prediction, method_prediction in zip(raw_prediction_results, method_prediction_results):
                    print('Original name:\t' + method_prediction.original_name)
                    for name_prob_pair in method_prediction.predictions:
                        print('\t(%f) predicted: %s' % (name_prob_pair['probability'], name_prob_pair['name']))
        total_time_for_redis = sum(self.redis.values()) + sum(self.predict_d.values())
        total_time_for_java = sum(self.java.values()) + sum(self.predict_d.values())
        #all_res = json.dumps(self.results)
        df = pd.DataFrame(columns=['filename', 'total_time_redis', 'total_time_java', 'java_time', 'predict_time'])
        #print(f'All results: {all_res}')
        for filename, predict_time in self.predict_d.items():
            java_time = self.java[filename]
            redis_time = self.redis[filename]
            df = df.append(
            {'filename': filename, 
            'java_time': java_time,
            'predict_time': predict_time,
            'redis_time': redis_time,
            'total_time_java': predict_time + java_time, 
            'total_time_redis': predict_time + redis_time, 
            'predict_time': predict_time, 
            }, ignore_index=True)
        df.to_csv('res.csv')
