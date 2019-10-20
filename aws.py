from boto3 import Session
from json import dump
from time import sleep

def session(region_name, aws_access_key_id, aws_secret_access_key):
    s = Session(region_name = region_name, aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key)
    return s

def checkBucket(bucket_list, bucket_name):
    bucket_already_created = False
    print('Checking if an AWS S3 bucket ' + bucket_name + ' already exists in your account')
    for bucket in bucket_list:
        if bucket['Name'] == bucket_name:
            bucket_already_created = True
            break
    return bucket_already_created

def createBucket(bucket_list, bucket_name, s3_client, region):
    if not checkBucket(bucket_list, bucket_name):
        print('Creating AWS S3 bucket ' + bucket_name)
        return s3_client.create_bucket(Bucket = bucket_name, ACL = 'private', CreateBucketConfiguration = { 'LocationConstraint': region })
    else:
        exit('ERROR: The AWS S3 bucket ' +  bucket_name + ' already exists (maybe in another AWS account). Please, change the bucket name.')

def uploadFiles(upload_list, bucket_name, session):
    for upload_file in upload_list:
        print('Uploading ' + upload_file + ' to AWS S3 bucket ' + bucket_name)
        session.resource('s3').meta.client.upload_file(upload_file, bucket_name, upload_file)

def createChangeSet(function_name, cloudformation_client, location, template_file, s3_client, bucket_name):
    for stack in cloudformation_client.describe_stacks()['Stacks']:
        if stack['StackName'] == function_name:
            if stack['StackStatus'] == 'REVIEW_IN_PROGRESS':
                break
            else:
                print('Rollbacking')
                cleanUp(s3_client, bucket_name, None, None)
                exit('ERROR: The AWS CloudFormation stack ' +  function_name + ' already exists. Please, change the stack name.')
    return cloudformation_client.create_change_set(StackName = function_name, TemplateURL = location + template_file, Capabilities=['CAPABILITY_IAM'], ChangeSetName = function_name + '-cs', ChangeSetType = 'CREATE')

def executeChangeSet(function_name, cloudformation_client, location, template_file, s3_client, bucket_name):
    while True:
        sleep(1)
        if cloudformation_client.describe_change_set(ChangeSetName = createChangeSet(function_name, cloudformation_client, location, template_file, s3_client, bucket_name)['Id'])['Status'] == 'CREATE_COMPLETE':
            print('Creating and executing AWS CloudFormation change set ' + function_name + '-cs')
            cloudformation_client.execute_change_set(StackName = function_name, ChangeSetName = function_name + '-cs')
            break

def updateFunctionConfiguration(function_name, lambda_client, function_memory, function_timeout):
    print('Updating AWS Lambda function ' + function_name + ' configuration with ' + function_memory + 'MB of memory and ' + function_timeout + 's of timeout')
    lambda_client.update_function_configuration(FunctionName = function_name, Timeout = int(function_timeout), MemorySize = int(function_memory))

def getEndpoint(cloudformation_client, function_name):
    url = None
    while True:
        sleep(1)
        if cloudformation_client.describe_stacks(StackName = function_name)['Stacks'][0]['StackStatus'] == 'CREATE_COMPLETE':
            url = cloudformation_client.describe_stacks(StackName = function_name)['Stacks'][0]['Outputs'][0]['OutputValue']
            print('Getting AWS API Gateway endpoint ' + url + '...')
            break
    return url

def cleanUp(s3_client, bucket_name, function_name, cloudformation_client):
    print('Starting cleanup')
    for object in s3_client.list_objects_v2(Bucket = bucket_name)['Contents']:
        print('Deleting ' + object['Key'] + ' at AWS S3 bucket ' + bucket_name)
        s3_client.delete_object(Bucket = bucket_name, Key = object['Key'])
    print('Deleting AWS S3 bucket ' + bucket_name)
    s3_client.delete_bucket(Bucket = bucket_name)
    if cloudformation_client is not None and function_name is not None:
        print('Deleting AWS CloudFormation stack ' + function_name)
        cloudformation_client.delete_stack(StackName = function_name)
    print('Finishing cleanup')

def collectMetrics(metric_name, cloudwatch_client, start_time, end_time, period, statistics, file, s3_client, bucket_name, function_name, cloudformation_client):
    response = None
    empty = False
    for metric in metric_name:
        with open(file + '-' + metric + '.json', 'w') as metric_file:
            response = cloudwatch_client.get_metric_statistics(Namespace = 'AWS/Lambda', MetricName = metric, StartTime = start_time, EndTime = end_time, Period = period, Statistics = statistics)
            if response is not None:
                for key in response:
                    if 'HTTPHeaders' in response[key]:
                        continue
                    elif type(response[key]) is str:
                        continue
                    elif response[key]:
                        dump(response[key], metric_file, indent = '\t', default = str, sort_keys = True)
                        empty = False
                    else:
                        empty = True
                        break
    if empty:
        print('Rollbacking')
        cleanUp(s3_client, bucket_name, function_name, cloudformation_client)
        exit('ERROR: Timestamp without data. Please, change another timestamp to collects metrics.')
