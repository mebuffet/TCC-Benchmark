import aws
import utils

from reqasync import run_async
from sys import exit
from time import sleep
from datetime import datetime
from datetime import timedelta

if __name__ == '__main__':
    args = utils.parser()

    print('Reading configuration file')
    benchmark_params = utils.readJson(args.config)

    print('Starting AWS session')
    session = aws.session(benchmark_params['region'], benchmark_params['access_key_id'], benchmark_params['secret_access_key'])

    print('All the AWS services will be created at ' + benchmark_params['region'])

    print('Starting AWS S3 client')
    s3_client = session.client('s3')

    bucket_list = s3_client.list_buckets()
    bucket = None

    bucket = aws.createBucket(bucket_list['Buckets'], benchmark_params['bucket_name'], s3_client, benchmark_params['region'])

    upload_list = [benchmark_params['template_file'], benchmark_params['function_zip']]

    aws.uploadFiles(upload_list, benchmark_params['bucket_name'], session)

    print('Starting AWS CloudFormation client')
    cloudformation_client = session.client('cloudformation')

    aws.executeChangeSet(benchmark_params['function_name'], cloudformation_client, bucket['Location'], benchmark_params['template_file'], s3_client, benchmark_params['bucket_name'])

    print('Starting AWS CloudWatch client')
    cloudwatch_client = session.client('cloudwatch')

    url = aws.getEndpoint(cloudformation_client, benchmark_params['function_name'])

    if not url:
        print('Rollbacking')
        aws.cleanUp(s3_client, benchmark_params['bucket_name'], benchmark_params['function_name'], cloudformation_client)
        exit('The AWS API Gateway endpoint is with problem. Please, check the template file ' + benchmark_params['template_file'])

    semaphores = 1024

    print('Starting AWS Lambda client')
    lambda_client = session.client('lambda')

    print('Warming AWS Lambda function ' + benchmark_params['function_name'])
    lambda_client.invoke(FunctionName = benchmark_params['function_name'], Payload = b'{"body":"warm"}')

    print('Starting benchmark')
    test = 0
    total_tests = len(benchmark_params['payload']) * len(benchmark_params['concurrents']) * len(benchmark_params['function_memory']) * len(benchmark_params['function_timeout'])
    output = None
    benchmark_cloudwatch_metrics = {}
    for payload in benchmark_params['payload']:
        for concurrents in benchmark_params['concurrents']:
            for memory in benchmark_params['function_memory']:
                for timeout in benchmark_params['function_timeout']:
                    test += 1
                    print('Test ' + str(test) + ' of ' + str(total_tests))
                    if args.output:
                        output = open('results/' + payload + '-' + concurrents + '-' + memory + '-' + timeout + '.output', 'w')
                    aws.updateFunctionConfiguration(benchmark_params['function_name'], lambda_client, memory, timeout)
                    while(datetime.utcnow().second > 0):
                        pass
                    start = datetime.utcnow()
                    run_async(int(concurrents), semaphores, url, payload, output) #TODO: tratar exceptions... se memoria nao suportar tamanho do payload, nao crashar o codigo, mas sim seguir para restante da execucao
                    finish = datetime.utcnow()
                    if args.output:
                        output.close()
                        print('The result of AWS Lambda function ' + benchmark_params['function_name'] + ' test ' + str(test) + ' is available at results/' + payload + '-' + concurrents + '-' + memory + '-' + timeout + '.output')
                    print('Benchmarking timestamp: started at ' + str(start) + ' and finished at ' + str(finish) + ' with, ' + str((finish - start).total_seconds()) + 's of duration')
                    benchmark_cloudwatch_metrics.update({payload + '-' + concurrents + '-' + memory + '-' + timeout : {'start' : start, 'finish' : finish + timedelta(seconds = 60 - (finish - start).total_seconds())}})
    print('Finishing benchmark')

    print('Waiting 1 minute for AWS CloudWatch collect metrics for the benchmarking')
    sleep(60)
    for key, values in benchmark_cloudwatch_metrics.items():
        aws.collectMetrics(['IteratorAge', 'Dead Letter Error', 'Throttles', 'UnreservedConcurrentExecutions', 'ConcurrentExecutions', 'Errors', 'Duration', 'Invocations'], cloudwatch_client, values['start'], values['finish'], int(benchmark_params['period']), ['SampleCount', 'Sum', 'Average', 'Minimum', 'Maximum'], 'results/' + key, s3_client, benchmark_params['bucket_name'], benchmark_params['function_name'], cloudformation_client)
    print('The results of AWS CloudWatch metrics are stored at results/')

    aws.cleanUp(s3_client, benchmark_params['bucket_name'], benchmark_params['function_name'], cloudformation_client)

    print('Ending program')
