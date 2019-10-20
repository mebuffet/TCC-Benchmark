args = read_arguments()
config = read_json_configuration(args.config)
session = aws.session(config.aws)
bucket = create_bucket(session, config.s3)
upload_files(session, config.files, bucket)
stack = create_stack(session, config.template, bucket)
url = get_url(stack.output)
invoke_function(session, config.function, 'warm')
for payload in config.payload:
  for concurrents in config.concurrents:
    for memory in config.memory:
      for timeout in config.timeout:
        update_function_configuration(session, config.function, timeout, memory)
        while(second is not 0):
          pass
        time.start = now()
        tests.append(run_test(url, concurrents, payload, args.output))
        time.finish = now()
        test_time.update(tests, time)
for test in tests:
  collect_metrics(session, test)
cleanup(session, bucket, stack)
