from json import dumps
from collections import Counter
from string import punctuation

#Handles formatting the http response
def respond(err, res = None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

#Looks for text inside of the body and returns frequency information about the words
def handler(event, context):
    try:
        text = event['body']
    except KeyError as e:
        print(e)
        return respond(KeyError('Unsupported key "{}"'.format(e)))
    if not text:
        return respond(ValueError('Body text can not be empty'))
    if text == 'LOW':
        text = open('tests/50K.txt').read()
    elif text == 'MEDIUM':
        text = open('tests/100K.txt').read()
    elif text == 'HIGH':
        text = open('tests/200K.txt').read()
    wordCounts = Counter()
    for word in text.split():
        word = word.rstrip(punctuation)
        if len(word) > 0:
            wordCounts.update([word.lower()])
    result = {
        'payload': event['body'],
        'uniqueWords': len(wordCounts),
        'wordCounts': wordCounts,
        'mostCommon': wordCounts.most_common()
    }
    return respond(None, result)
