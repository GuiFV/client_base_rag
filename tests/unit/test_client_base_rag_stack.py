import aws_cdk as core
import aws_cdk.assertions as assertions

from client_base_rag.client_base_rag_stack import ClientBaseRagStack

# example tests. To run these tests, uncomment this file along with the example
# resource in client_base_rag/client_base_rag_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ClientBaseRagStack(app, "client-base-rag")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
