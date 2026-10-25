"""Local tests use fake AWS clients and do not create cloud resources."""

import importlib.util
import json
import os
import sys
import types
import textwrap
import unittest
from pathlib import Path


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item, ConditionExpression):
        assert ConditionExpression == "attribute_not_exists(orderId)"
        self.items[Item["orderId"]] = Item

    def get_item(self, Key):
        item = self.items.get(Key["orderId"])
        return {"Item": item} if item else {}


class FakeSNS:
    def __init__(self):
        self.messages = []

    def publish(self, **kwargs):
        self.messages.append(kwargs)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = FakeTable()
        cls.sns = FakeSNS()
        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.resource = lambda name: types.SimpleNamespace(Table=lambda table: cls.table)
        fake_boto3.client = lambda name: cls.sns
        sys.modules["boto3"] = fake_boto3
        fake_botocore = types.ModuleType("botocore")
        fake_exceptions = types.ModuleType("botocore.exceptions")
        fake_exceptions.ClientError = type("ClientError", (Exception,), {})
        sys.modules["botocore"] = fake_botocore
        sys.modules["botocore.exceptions"] = fake_exceptions
        os.environ["TABLE_NAME"] = "test-orders"
        os.environ["TOPIC_ARN"] = "arn:aws:sns:us-west-2:123456789012:test"
        spec = importlib.util.spec_from_file_location("order_app", Path(__file__).with_name("app.py"))
        cls.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.app)

    def setUp(self):
        self.table.items.clear()
        self.sns.messages.clear()

    def test_create_get_and_notification(self):
        created = self.app.handler({
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"itemName": "Sample notebook"}),
        }, None)
        self.assertEqual(created["statusCode"], 201)
        body = json.loads(created["body"])
        self.assertEqual(body["project"], "Daz Arnaud, CS 79C Final Project")
        self.assertEqual(body["status"], "received")
        self.assertEqual(len(self.sns.messages), 1)
        received = self.app.handler({
            "requestContext": {"http": {"method": "GET"}},
            "pathParameters": {"orderId": body["orderId"]},
        }, None)
        self.assertEqual(received["statusCode"], 200)
        self.assertEqual(json.loads(received["body"])["itemName"], "Sample notebook")

    def test_invalid_json(self):
        result = self.app.handler({"requestContext": {"http": {"method": "POST"}}, "body": "{"}, None)
        self.assertEqual(result["statusCode"], 400)

    def test_json_array(self):
        event = {"requestContext": {"http": {"method": "POST"}}, "body": "[]"}
        self.assertEqual(self.app.handler(event, None)["statusCode"], 400)

    def test_blank_item(self):
        result = self.app.handler({
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"itemName": "  "}),
        }, None)
        self.assertEqual(result["statusCode"], 400)

    def test_missing_order(self):
        result = self.app.handler({
            "requestContext": {"http": {"method": "GET"}},
            "pathParameters": {"orderId": "missing"},
        }, None)
        self.assertEqual(result["statusCode"], 404)

    def test_cloudformation_inline_handler(self):
        template = Path(__file__).with_name("template.yaml").read_text()
        source = template.split("        ZipFile: |\n", 1)[1].split("\n  HttpApi:", 1)[0]
        namespace = {}
        exec(compile(textwrap.dedent(source), "template-inline.py", "exec"), namespace)
        created = namespace["handler"]({
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"itemName": "Template test"}),
        }, None)
        self.assertEqual(created["statusCode"], 201)
        self.assertEqual(json.loads(created["body"])["itemName"], "Template test")
        invalid = namespace["handler"]({
            "requestContext": {"http": {"method": "POST"}}, "body": "[]"
        }, None)
        self.assertEqual(invalid["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
