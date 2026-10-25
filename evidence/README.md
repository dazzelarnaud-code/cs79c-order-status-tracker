# Live evidence

I deployed `cs79c-final-project` in us-west-2 on October 25, 2026. The public API accepted a sample order and returned the same saved item through GET. The order ID was `ab377bfc-122e-464a-aef5-4d090dbaa95a`.

`stack-create-complete.jpg` shows CREATE_COMPLETE. `stack-outputs.jpg` shows the API and queue URLs. `stack-resources.jpg` shows created resources. `dynamodb-sample-order.jpg` shows the saved item. `sqs-event-delivered.jpg` and `sqs-event-body.jpg` show the matching event in the queue. `lambda-successful-lookup.jpg` shows HTTP 200, the project name, and execution metrics. The Lambda test also displayed the CloudWatch log output. The public API POST returned HTTP 201. Its GET returned HTTP 200 with the saved record.

No credentials, payment data, or real customer details appear in these screenshots.
