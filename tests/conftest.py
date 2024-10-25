# tests/conftest.py
import pytest


@pytest.fixture(scope="module")
def cdk_app():
    from aws_cdk import App
    return App()


@pytest.fixture
def client_base_stack(cdk_app):
    from client_base_rag.client_base_rag_stack import ClientBaseRagStack
    return ClientBaseRagStack(cdk_app, "ClientBaseRagStack")


@pytest.fixture
def template(client_base_stack):
    from aws_cdk.assertions import Template
    return Template.from_stack(client_base_stack)
