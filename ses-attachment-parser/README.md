## Sample Email Parser for Lambda

SES can receive emails and store them in S3. Configuring a trigger in S3, you can start a lambda function to extract relevant information from each message automatically. In this example, 
the function extracts all attachments that look like a CSV file and saves them in a folder in S3.

To run this example, you need to previously configure SES to receive emails.

 * https://aws.amazon.com/pt/blogs/aws/new-receive-and-process-incoming-email-with-amazon-ses/
 * https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email.html

```
SES -> S3 (input folder) -> Lambda -> S3 (csv folder)
                                      S3 (processed folder)
```

From this point on, you can use other ideas to process your file.

 * https://github.com/awslabs/aws-lambda-redshift-loader

## Deploy

Use the following command to deploy the example. Replace the parameters in the beginning of the function.

```
TEMP_BUCKET="<bucket used to package the template>"
EMAIL_BUCKET_NAME="<bucket used to store the received emails>"

aws s3 mb s3://$TEMP_BUCKET
aws cloudformation package --template-file cloudformation.yml \
    --s3-bucket $TEMP_BUCKET \
    --output-template-file output.yml \
    && aws cloudformation deploy \
    --template-file output.yml \
    --stack-name EmailParser \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides EmailBucketName=$EMAIL_BUCKET_NAME SourceFolder=subdomain CsvFolder=csv ProcessedFolder=processed
```