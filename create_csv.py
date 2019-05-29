from src import ember
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--path', help='jsonl path', required=True)
args = parser.parse_args()

output = '/home/choi/Desktop/output'
ember.create_metadata(args.path)

print('Done')
print()