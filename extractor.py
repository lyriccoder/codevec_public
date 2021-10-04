import subprocess
import tempfile
from time import time
import redis
import uuid
import json

class Extractor:
    def __init__(self, config, jar_path, max_path_length, max_path_width):
        self.config = config
        self.max_path_length = max_path_length
        self.max_path_width = max_path_width
        self.jar_path = jar_path
        self.publish_r = redis.Redis(host='localhost', port=6379, db=0)
        self.p = self.publish_r.pubsub()

    def extract_paths_with_redis(self, code_string, file_name_str):
        hash_to_string_dict = {}
        result = []
        req_uuid = str(uuid.uuid1())
        try:
                request = {'uuid': req_uuid, 'code': code_string}
                self.publish_r.publish('requests', json.dumps(request))
                self.p.subscribe(req_uuid)
                while True:
                    resp = self.p.get_message()
                    if resp:
                        type_msg = resp['type']
                        if type_msg.strip() == 'message':
                            message = resp['data'].decode()
                            break
                        else:
                            continue
                    else:
                        continue

                output = message.splitlines()
                if len(output) == 0:
                    err = err.decode()
                    raise ValueError(err)
                for i, line in enumerate(output):
                    parts = line.rstrip().split(' ')
                    method_name = parts[0]
                    current_result_line_parts = [method_name]
                    contexts = parts[1:]
                    for context in contexts[:self.config.MAX_CONTEXTS]:
                        context_parts = context.split(',')
                        context_word1 = context_parts[0]
                        context_path = context_parts[1]
                        context_word2 = context_parts[2]
                        hashed_path = str(self.java_string_hashcode(context_path))
                        hash_to_string_dict[hashed_path] = context_path
                        current_result_line_parts += ['%s,%s,%s' % (context_word1, hashed_path, context_word2)]
                    space_padding = ' ' * (self.config.MAX_CONTEXTS - len(contexts))
                    result_line = ' '.join(current_result_line_parts) + space_padding
                    result.append(result_line)
        finally:
            return result, hash_to_string_dict
            
    def extract_paths(self, code_string, file_name_str):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        out = None
        java_start_time = time()
        try:
            tmp.write(bytes(code_string, encoding='utf-8'))
            tmp.close()
                
            command = ['java', '-cp', self.jar_path, 'JavaExtractor.App', '--max_path_length',
                       str(self.max_path_length), '--max_path_width', str(self.max_path_width), '--file', tmp.name, '--no_hash']
            command_str = ' '.join(command)
            print(f'Running {command_str}')
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            output = out.decode().splitlines()
            if len(output) == 0:
                err = err.decode()
                raise ValueError(err)
            hash_to_string_dict = {}
            result = []
            for i, line in enumerate(output):
                parts = line.rstrip().split(' ')
                method_name = parts[0]
                current_result_line_parts = [method_name]
                contexts = parts[1:]
                for context in contexts[:self.config.MAX_CONTEXTS]:
                    context_parts = context.split(',')
                    context_word1 = context_parts[0]
                    context_path = context_parts[1]
                    context_word2 = context_parts[2]
                    hashed_path = str(self.java_string_hashcode(context_path))
                    hash_to_string_dict[hashed_path] = context_path
                    current_result_line_parts += ['%s,%s,%s' % (context_word1, hashed_path, context_word2)]
                space_padding = ' ' * (self.config.MAX_CONTEXTS - len(contexts))
                result_line = ' '.join(current_result_line_parts) + space_padding
                result.append(result_line)
        finally:
            return result, hash_to_string_dict


    @staticmethod
    def java_string_hashcode(s):
        """
        Imitating Java's String#hashCode, because the model is trained on hashed paths but we wish to
        Present the path attention on un-hashed paths.
        """
        h = 0
        for c in s:
            h = (31 * h + ord(c)) & 0xFFFFFFFF
        return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000
