# LLM bot with Client Side RAG
## Upload a file and use ChatGPT to talk about it

Application: [https://link.gfv.bio/RAG-GPT](https://link.gfv.bio/RAG-GPT)

### What is RAG GPT?
- It's ChatGPT on steroids! You upload a document and instantly augment it with your data!
- This is a small prototype to showcase AWS services (CDK, Lambda and S3) and Large Language Models capabilities when extended with files using RAG technique (Retrieval-Augmented Generation).

### How to Use
1. Upload a .txt or .csv document using the Upload Document button. (1MB MAX)
2. Type your message in the input box below and hit Send or press Enter.
3. The system will process your message and respond using data from your file.

### Characteristics
- Uploaded files are associated with your session only.
- All Files are deleted automatically from S3 bucket every 24h.
- Limited number of calls - per day: 10 files max, 30 messages max

### This is an AWS CDK deployable project

- Flask based
- Runs on Lambda
- S3 bucket for files
- App is exposed with Lambda function URL
- CI/CD pipeline with Github actions

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

For more information on setting up AWS CDK, visit [https://aws.amazon.com/cdk/](https://aws.amazon.com/cdk/)

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies locally.

```
$ pip install -r requirements-dev.txt
$ pip install -r lambda/requirements.txt
```

And update any lambda dependencies for deployment (required before pushing for CI/CD pipeline)

```
$ pip install \
    --platform manylinux2014_x86_64 \
    --target=lambda/ \
    --implementation cp \
    --python-version 3.9 \
    --only-binary=:all: --upgrade \
    -r lambda/requirements.txt
```

Set up a OpenAI API secret key

```
$ aws secretsmanager create-secret --name openai-api-key --secret-string "your_openai_api_key_here"
```

Generate and set up a session secret key

```
$ aws secretsmanager create-secret --name app-session-secret-key --secret-string "a_strong_string_for_session_security"
```

Run tests locally with
```
$ pytest tests lambda/tests
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

Run locally with
```
$ python lambda/app.py
```

And manual deploy with
```
$ cdk deploy
```

For CI-CD deployment, insert in 'secrets and variables/actions/repository secrets' the following variables:

- OPENAI_API_KEY
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- BUCKET_NAME
- OPENAI_SECRET_ARN
- SESSION_SECRET_KEY_ARN
- LAMBDA_FUNCTION_URL

Commands to expose them:

Stack name: 
```sh
aws cloudformation list-stacks --query "StackSummaries[*].StackName"
```

Lambda function name: 
```sh
aws lambda list-functions --query 'Functions[*].FunctionName' --output text
```

Retrieve Logical Resource IDs: 
To list all logical resource IDs in your stack:
```sh
aws cloudformation describe-stack-resources --stack-name <your_identified_stack_name> --query 'StackResources[*].LogicalResourceId' --output text
```

Replace `<your_identified_stack_name>`, `<your_lambda_function_name>`, and `<your_logical_resource_id>` with actual values:

Commands to retrieve and expose secrets:

Retrieve the `BUCKET_NAME` (Physical Resource ID for your bucket):
```sh
BUCKET_NAME=$(aws cloudformation describe-stack-resource --stack-name <your_identified_stack_name> --logical-resource-id <your_logical_resource_id> --query 'StackResourceDetail.PhysicalResourceId' --output text)
echo "BUCKET_NAME: $BUCKET_NAME"
```

Retrieve the `OPENAI_SECRET_ARN`:
```sh
OPENAI_SECRET_ARN=$(aws secretsmanager describe-secret --secret-id openai-api-key --query 'ARN' --output text)
echo "OPENAI_SECRET_ARN: $OPENAI_SECRET_ARN"
```

Retrieve the `SESSION_SECRET_KEY_ARN`:
```sh
SESSION_SECRET_KEY_ARN=$(aws secretsmanager describe-secret --secret-id app-session-secret-key --query 'ARN' --output text)
echo "SESSION_SECRET_KEY_ARN: $SESSION_SECRET_KEY_ARN"
```

Retrieve the `LAMBDA_FUNCTION_URL` (Function ARN for your Lambda function):
```sh
LAMBDA_FUNCTION_URL=$(aws lambda list-functions --query "Functions[?FunctionName=='<your_lambda_function_name>'].FunctionArn" --output text)
echo "LAMBDA_FUNCTION_URL: $LAMBDA_FUNCTION_URL"
```


To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk bootstrap`   setup the AWS account environment (required only once)
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
