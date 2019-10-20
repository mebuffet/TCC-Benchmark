from argparse import ArgumentParser
from json import load

def parser():
    parser = ArgumentParser()
    parser.add_argument('--config-file', dest = 'config', type = str, required = True, help = 'json file containing the benchmark parameters')
    parser.add_argument('--enable-output', dest = 'output', action = 'store_true', required = False, help = 'if used, response output file, of AWS Lambda function, will be created')
    return parser.parse_args()

def readJson(file):
    result = None
    if isinstance(file, str):
        with open(file) as file:
            try:
                result = load(file)
            except:
                print('Error loading ' + file)
    return result
