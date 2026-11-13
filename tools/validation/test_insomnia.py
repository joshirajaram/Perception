import json
import re
import unittest
from pathlib import Path
from urllib.parse import quote, urlsplit

from validate import unique_keys


PACKAGE = Path(__file__).resolve().parents[2] / "API" / "Insomnia-collection"
GRAPH_ROOT = "https://graph.microsoft.com/beta/security/agenticSecurity"
TEMPLATE = re.compile(r"\{\{\s*_\.(\w+)(?:\s*\|\s*(json))?\s*\}\}")


class InsomniaCollectionTests(unittest.TestCase):
    def setUp(self):
        self.collection = json.loads(
            (PACKAGE / "perception-graph.insomnia.json").read_text(encoding="utf-8"),
            object_pairs_hook=unique_keys,
        )
        self.resources = {
            resource["_id"]: resource for resource in self.collection["resources"]
        }
        self.requests = [
            resource for resource in self.resources.values()
            if resource["_type"] == "request"
        ]
        self.base = self.resources["__BASE_ENVIRONMENT_ID__"]

    def test_import_has_complete_acyclic_parent_relationships(self):
        self.assertEqual(self.collection["_type"], "export")
        self.assertEqual(self.collection["__export_format"], 4)
        self.assertEqual(len(self.resources), len(self.collection["resources"]))
        self.assertEqual(len(self.requests), 16)
        self.assertEqual(
            sum(item["_type"] == "workspace" for item in self.resources.values()), 1
        )
        for resource in self.resources.values():
            with self.subTest(resource=resource["_id"]):
                self.assertRegex(
                    resource["_id"],
                    r"^__(?:WORKSPACE_ID|BASE_ENVIRONMENT_ID|[a-z_]+_\d+)__$",
                )
                seen = {resource["_id"]}
                parent = resource["parentId"]
                while parent is not None:
                    self.assertIn(parent, self.resources)
                    self.assertNotIn(parent, seen)
                    seen.add(parent)
                    parent = self.resources[parent]["parentId"]

    def test_private_defaults_match_manifest_and_contain_no_tenant_values(self):
        manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
        names = {item["name"] for item in manifest["inputs"]}
        private = self.resources["__env_1__"]
        self.assertEqual(self.base["parentId"], "__WORKSPACE_ID__")
        self.assertFalse(self.base["isPrivate"])
        self.assertEqual(private["parentId"], self.base["_id"])
        self.assertTrue(private["isPrivate"])
        for environment in (self.base, private):
            self.assertEqual(set(environment["data"]), names)
            self.assertEqual(environment["data"]["access_token"], "")
            self.assertEqual(environment["data"]["write_access_token"], "")
            self.assertEqual(
                {pair["name"]: pair["value"] for pair in environment["kvPairData"]},
                environment["data"],
            )
            self.assertTrue(all(
                pair["enabled"] and pair["type"] == "str"
                for pair in environment["kvPairData"]
            ))
            for name, value in environment["data"].items():
                if name.endswith("_id") or name == "input_value":
                    self.assertRegex(value, r"^REPLACE_WITH_[A-Z_]+$")
        self.assertNotRegex(
            json.dumps(self.collection),
            r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
        )

    def test_public_routes_and_query_options(self):
        expected = {
            "GET /playbookDefinitions",
            "GET /playbookDefinitions/:playbook_definition_id",
            "GET /sessions",
            "POST /sessions",
            "GET /sessions/:session_id",
            "POST /sessions/:session_id/cancel",
            "GET /sessions/:session_id/playbookDefinition",
            "GET /sessions/:session_id/inputs",
            "GET /sessions/:session_id/inputs/:input_id",
            "GET /sessions/:session_id/outputs",
            "GET /sessions/:session_id/outputs/:output_id",
            "GET /sessions/:session_id/outputs/:output_id/content",
            "GET /sessions/:session_id/agentRuns",
            "GET /sessions/:session_id/agentRuns/:agent_run_id",
        }
        actual = set()
        for request in self.requests:
            with self.subTest(request=request["name"]):
                self.assertTrue(request["url"].startswith(GRAPH_ROOT + "/"))
                route = request["url"][len(GRAPH_ROOT):]
                actual.add(f'{request["method"]} {route}')
                parameters = {
                    item["name"]: item["value"]
                    for item in request.get("pathParameters", [])
                }
                self.assertEqual(set(parameters), set(re.findall(r":([a-z_]+)", route)))
                for name, value in parameters.items():
                    self.assertIn(name, self.base["data"])
                    self.assertEqual(value, "{{ _." + name + " }}")
                if request["method"] == "POST" or route.endswith("/content"):
                    allowed = set()
                elif route == "/sessions":
                    allowed = {"$filter", "$top", "$select"}
                else:
                    allowed = {"$select"}
                self.assertTrue(
                    {item["name"] for item in request["parameters"]} <= allowed
                )
        self.assertEqual(actual, expected)

    def test_reads_cannot_supply_write_credentials_and_no_hidden_actions_exist(self):
        for resource in self.resources.values():
            self.assertIn(
                resource["_type"],
                {"workspace", "environment", "request_group", "request"},
            )
            self.assertFalse(resource.get("preRequestScript"))
            self.assertFalse(resource.get("afterResponseScript"))
            if resource["_type"] == "request_group":
                self.assertEqual(resource["environment"], {})
        for request in self.requests:
            token = "write_access_token" if request["method"] == "POST" else "access_token"
            self.assertEqual(request["authentication"], {
                "type": "bearer", "token": "{{ _." + token + " }}",
                "prefix": "Bearer", "disabled": False,
            })
            self.assertFalse(any(
                item["name"].lower() in {"authorization", "cookie"}
                for item in request["headers"]
            ))
            self.assertEqual(request["settingFollowRedirects"], "off")
            self.assertFalse(request["settingStoreCookies"])
            self.assertFalse(request["settingSendCookies"])
            parent = self.resources[request["parentId"]]
            self.assertEqual(parent["_type"], "request_group")
            if request["method"] == "POST":
                self.assertTrue(request["name"].startswith("WRITE - "))
                self.assertIn("WRITE", parent["name"])
            else:
                self.assertEqual(request["body"], {})

    def test_body_escaping_and_opaque_path_parameter_contract(self):
        values = {
            **self.base["data"],
            "playbook_definition_id": "00000000-0000-4000-8000-000000000001",
            "session_id": "00000000-0000-4000-8000-000000000002",
            "input_value": 'synthetic "quoted" value\nwith\\backslash',
            "output_id": "synthetic/id with space?x=1#fragment",
        }

        def render(text):
            return TEMPLATE.sub(
                lambda match: json.dumps(values[match[1]])
                if match[2] else values[match[1]],
                text,
            )

        create = next(item for item in self.requests if item["name"] == "WRITE - Create session")
        body = json.loads(render(create["body"]["text"]))
        self.assertEqual(body, {
            "playbookDefinition@odata.bind":
                GRAPH_ROOT + "/playbookDefinitions/" + values["playbook_definition_id"],
            "inputs": [{"kind": values["input_kind"], "value": values["input_value"]}],
        })
        self.assertEqual(create["body"]["mimeType"], "application/json")
        cancel = next(item for item in self.requests if item["name"] == "WRITE - Cancel session")
        self.assertEqual(cancel["body"], {})
        self.assertEqual(cancel["parameters"], [])
        download = next(item for item in self.requests if item["name"] == "Download output content")
        parameters = {item["name"]: render(item["value"]) for item in download["pathParameters"]}
        address = re.sub(
            r"/:([a-z_]+)",
            lambda match: "/" + quote(parameters[match[1]], safe=""),
            download["url"],
        )
        parsed = urlsplit(address)
        self.assertEqual((parsed.scheme, parsed.netloc), ("https", "graph.microsoft.com"))
        self.assertEqual((parsed.query, parsed.fragment), ("", ""))
        self.assertIn("synthetic%2Fid%20with%20space%3Fx%3D1%23fragment", parsed.path)


if __name__ == "__main__":
    unittest.main()
