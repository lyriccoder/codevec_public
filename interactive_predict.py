import traceback

from common import common
from extractor import Extractor
from pathlib import Path
import inspect
import time
from numpy import mean, median, quantile
import json
import pandas as pd
from collections import defaultdict


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
        self.path_extractor = Extractor(config,
                                        jar_path=JAR_PATH,
                                        max_path_length=MAX_PATH_LENGTH,
                                        max_path_width=MAX_PATH_WIDTH)

    def predict(self, input_filename: Path):
        predictions_with_ranks = defaultdict(list)
        file_name_str = str(input_filename)
        with open(file_name_str) as f:
            code = f.read()
            predict_lines, hash_to_string_dict = self.path_extractor.extract_paths_with_redis(code, file_name_str)
            method_prediction_results = common.parse_prediction_results(
                raw_prediction_results, hash_to_string_dict,
                self.model.vocabs.target_vocab.special_words, topk=SHOW_TOP_CONTEXTS)
            for raw_prediction, method_prediction in zip(raw_prediction_results, method_prediction_results):
                print('Original name:\t' + method_prediction.original_name)
                for name_prob_pair in method_prediction.predictions:
                    print('\t(%f) predicted: %s' % (name_prob_pair['probability'], name_prob_pair['name']))
                    predictions_with_ranks[file_name_str].append((name_prob_pair['probability'], name_prob_pair['name']))
