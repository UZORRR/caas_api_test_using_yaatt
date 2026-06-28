#!/usr/bin/env python3
"""Generate yaatt tests from Postman caas collection scenarios (CaaS API only)."""
import copy
import json
from datetime import datetime, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
BASE_FILE = TESTS / "2025_12_30T16_12_35Z_test.yml"

# Skip scenarios already covered by existing files
SKIP_NAMES = {
    "Create order - success - without clientId",
    "Create order - fail - Invalid patient verification",
}


def load_base():
    with open(BASE_FILE) as f:
        doc = yaml.safe_load(f)
    body = copy.deepcopy(doc["requests"]["create_order"]["body"])
    return body


def dump_test(path: Path, doc: dict):
    class QuotedStr(str):
        pass

    def represent_quoted_str(dumper, data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")

    yaml.add_representer(QuotedStr, represent_quoted_str)

    def quote_special(obj):
        if isinstance(obj, dict):
            return {k: quote_special(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [quote_special(v) for v in obj]
        if isinstance(obj, str) and ("{{" in obj or obj.startswith("+")):
            return QuotedStr(obj)
        return obj

    doc = quote_special(doc)
    with open(path, "w") as f:
        yaml.dump(doc, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def req_post(key, desc, url, headers, body):
    return {
        key: {
            "description": desc,
            "method": "post",
            "url": url,
            "headers": headers,
            "body": body,
        }
    }


def req_patch(key, desc, url, headers, body):
    return {
        key: {
            "description": desc,
            "method": "patch",
            "url": url,
            "headers": headers,
            "body": body,
        }
    }


def req_get(key, desc, url, headers):
    return {
        key: {
            "description": desc,
            "method": "get",
            "url": url,
            "headers": headers,
        }
    }


def status(prop, code):
    return {"property": prop, "type": "status_code", "value": code}


def eq(prop, val):
    return {"property": prop, "type": "is_equals", "value": val}


def success_201(prop):
    return [
        status(prop, 201),
        eq(f"{prop}.status", "new"),
        eq(f"{prop}.patientId", "hhPati3nt2"),
    ]


def success_200_order(prop):
    return [
        status(prop, 200),
        eq(f"{prop}.status", "new"),
        eq(f"{prop}.patientId", "hhPati3nt2"),
    ]


def client_not_found(prop):
    return [
        status(prop, 412),
        eq(f"{prop}.code", 412),
        eq(f"{prop}.message", "ClientNotFoundException"),
    ]


def validation_400(prop):
    return [
        status(prop, 400),
        eq(f"{prop}.code", 400),
        eq(f"{prop}.message", "ValidationException"),
    ]


def patient_body(base):
    return copy.deepcopy(base["patient"])


def patient_update_payload(**patient_overrides):
    p = {
        "id": "{{env:CAAS_PATIENT_ID}}",
        "gender": "male",
        "givenName": "Updated",
        "familyName": "Patient HH",
        "phoneNumber": "+4471118973247",
        "email": "hhnewpatient@testemail.com",
        "dateOfBirth": "1970-10-30",
        "verification": "document-checked",
        "registeredAddress": {
            "line1": "Flat 19 Mansion House",
            "line2": "9 Super Street",
            "city": "Brighton",
            "state": "Texas",
            "postalCode": "N103LH",
            "countryCode": "GB",
        },
        "registeredProvider": {
            "internalId": "439764b7-eef6-4edd-bbba-b635e2ea2861",
            "clinicName": "RITCHIE STREET GROUP PRACTICE",
            "phoneNumber": "+4471118973247",
            "email": "hello@world.com",
            "address": {
                "line1": "Flat 19 Mansion House",
                "line2": "9 Super Street",
                "city": "Brighton",
                "state": "Texas",
                "postalCode": "N18YZ",
                "countryCode": "GB",
            },
        },
    }
    for k, v in patient_overrides.items():
        if k == "registeredAddress" and isinstance(v, dict):
            p["registeredAddress"].update(v)
        elif k == "registeredProvider" and isinstance(v, dict):
            if v is None:
                del p["registeredProvider"]
            else:
                p["registeredProvider"].update(v)
        else:
            p[k] = v
    return {"patient": p}


def build_scenarios(base_body):
    headers = {
        "x-api-key": "{{env:CAAS_API_KEY}}",
    }
    url_orders = "{{env:CAAS_BASE_URL}}/orders"
    scenarios = []

    def full_create_body(**mods):
        b = copy.deepcopy(base_body)
        b["order"]["id"] = "{{gen:uuid}}"
        for path, val in mods.items():
            parts = path.split(".")
            cur = b
            for p in parts[:-1]:
                cur = cur[p]
            cur[parts[-1]] = val
        return b

    # --- Create order success ---
    b = full_create_body()
    scenarios.append(
        (
            "Create order - success - with valid clientId",
            "POST /orders with x-client-id returns 201",
            req_post(
                "create_order",
                "Create order with valid client id header",
                url_orders,
                {
                    **headers,
                    "x-client-id": "{{env:CAAS_CLIENT_ID}}",
                },
                b,
            ),
            success_201("create_order"),
        )
    )

    for order_type in ("refill", "replacement"):
        b = full_create_body()
        b["order"]["type"] = order_type
        scenarios.append(
            (
                f"Create order - success - {order_type}",
                f"POST /orders with order type {order_type} returns 201",
                req_post(
                    "create_order",
                    f"Create {order_type} order",
                    url_orders,
                    headers,
                    b,
                ),
                success_201("create_order"),
            )
        )

    b1 = full_create_body()
    b2 = copy.deepcopy(b1)
    b2["order"]["id"] = "{{create_order.orderId}}"
    scenarios.append(
        (
            "Create order - success - Order already exists",
            "POST /orders with duplicate order id returns 200",
            {
                **req_post(
                    "create_order",
                    "Create new order",
                    url_orders,
                    headers,
                    b1,
                ),
                **req_post(
                    "create_order_duplicate",
                    "Submit same order id again",
                    url_orders,
                    headers,
                    b2,
                ),
            },
            success_200_order("create_order_duplicate"),
        )
    )

    b = full_create_body()
    del b["assessment"]["media"]
    scenarios.append(
        (
            "Create order - success - patient media is missing",
            "POST /orders without assessment media returns 200 for existing patient order",
            req_post(
                "create_order",
                "Create order without assessment media",
                url_orders,
                headers,
                b,
            ),
            success_200_order("create_order"),
        )
    )

    b = full_create_body()
    del b["patient"]["registeredProvider"]
    scenarios.append(
        (
            "Create order - success - GP is missing",
            "POST /orders without registeredProvider returns 201",
            req_post(
                "create_order",
                "Create order without GP",
                url_orders,
                headers,
                b,
            ),
            success_201("create_order"),
        )
    )

    b = full_create_body()
    b["patient"]["registeredProvider"]["internalId"] = ""
    scenarios.append(
        (
            "Create order - success- GP id is empty string",
            "POST /orders with empty GP internalId returns 201",
            req_post("create_order", "Create order with empty GP id", url_orders, headers, b),
            success_201("create_order"),
        )
    )

    b = full_create_body()
    b["patient"]["registeredProvider"]["internalId"] = None
    scenarios.append(
        (
            "Create order - success - GP id is null",
            "POST /orders with null GP internalId returns 201",
            req_post("create_order", "Create order with null GP id", url_orders, headers, b),
            success_201("create_order"),
        )
    )

    b = full_create_body()
    b["patient"]["registeredProvider"]["email"] = ""
    scenarios.append(
        (
            "Create order - success- GP email is empty",
            "POST /orders with empty GP email returns 201",
            req_post("create_order", "Create order with empty GP email", url_orders, headers, b),
            success_201("create_order"),
        )
    )

    b = full_create_body()
    b["patient"]["registeredProvider"]["email"] = None
    scenarios.append(
        (
            "Create order - success - GP email is null",
            "POST /orders with null GP email returns 201",
            req_post("create_order", "Create order with null GP email", url_orders, headers, b),
            success_201("create_order"),
        )
    )

    # --- Create order failures ---
    for label, client_id in [
        ("invalid clientId", "invalid"),
        ("clientId null", "null"),
        ("clientId empty string", ""),
        ("clientId any number", "1234567890"),
        ("clientId capitalized", "HH4125078311U0K"),
    ]:
        b = full_create_body()
        scenarios.append(
            (
                f"Create order - fail - {label}",
                f"POST /orders with bad x-client-id returns 412 ({label})",
                req_post(
                    "create_order",
                    "Create order with invalid client id",
                    url_orders,
                    {**headers, "x-client-id": client_id},
                    b,
                ),
                client_not_found("create_order"),
            )
        )

    scenarios.append(
        (
            "Create order - fail - empty payload",
            "POST /orders with empty body returns 400 ValidationException",
            req_post("create_order", "Empty payload", url_orders, headers, {}),
            validation_400("create_order"),
        )
    )

    scenarios.append(
        (
            "Create order - fail - all fields null",
            "POST /orders with null top-level fields returns 400",
            req_post(
                "create_order",
                "Null patient order assessment",
                url_orders,
                headers,
                {"patient": None, "order": None, "assessment": None},
            ),
            validation_400("create_order"),
        )
    )

    b = full_create_body()
    b["patient"] = {}
    scenarios.append(
        (
            "Create order - fail - missing patient required fields",
            "POST /orders with empty patient object returns 400",
            req_post("create_order", "Empty patient", url_orders, headers, b),
            validation_400("create_order"),
        )
    )

    b = full_create_body()
    b["patient"] = {
        "id": None,
        "gender": None,
        "givenName": None,
        "familyName": None,
        "phoneNumber": None,
        "email": None,
        "dateOfBirth": None,
        "verification": None,
        "registeredAddress": {
            "line1": None,
            "line2": None,
            "city": None,
            "state": None,
            "postalCode": None,
            "countryCode": None,
        },
        "registeredProvider": b["patient"]["registeredProvider"],
    }
    scenarios.append(
        (
            "Create order - fail - patient required fields are null",
            "POST /orders with null patient fields returns 400",
            req_post("create_order", "Null patient fields", url_orders, headers, b),
            validation_400("create_order"),
        )
    )

    b = full_create_body()
    b["order"] = {}
    scenarios.append(
        (
            "Create order - fail - order data required fields are missing",
            "POST /orders with empty order returns 400",
            req_post("create_order", "Empty order", url_orders, headers, b),
            validation_400("create_order"),
        )
    )

    b = full_create_body()
    b["order"] = {
        "id": None,
        "type": None,
        "serviceId": None,
        "productId": None,
        "shipping": {
            "priority": None,
            "address": {
                "line1": None,
                "line2": None,
                "city": None,
                "state": None,
                "postalCode": None,
                "countryCode": None,
            },
        },
    }
    scenarios.append(
        (
            "Create order - fail - order data required fields are null",
            "POST /orders with null order fields returns 400",
            req_post("create_order", "Null order fields", url_orders, headers, b),
            validation_400("create_order"),
        )
    )

    b = full_create_body()
    b["patient"]["verification"] = "not-verified"
    scenarios.append(
        (
            "Create order - fail - Invalid patient verification",
            "POST /orders with not-verified patient returns 422",
            req_post("create_order", "Invalid verification", url_orders, headers, b),
            [
                status("create_order", 422),
                eq("create_order.code", 422),
                eq("create_order.message", "PatientVerificationException"),
            ],
        )
    )

    b = full_create_body()
    b["patient"]["verification"] = "background-checked"
    b["order"]["shipping"]["priority"] = "none"
    scenarios.append(
        (
            "Create order - fail - Invalid shipping priority",
            "POST /orders with invalid shipping priority returns 400",
            req_post("create_order", "Invalid shipping priority", url_orders, headers, b),
            validation_400("create_order"),
        )
    )

    b = full_create_body()
    b["order"]["type"] = "none"
    b["order"]["shipping"]["priority"] = "express"
    scenarios.append(
        (
            "Create order - fail - Invalid order type",
            "POST /orders with invalid order type returns 400",
            req_post("create_order", "Invalid order type", url_orders, headers, b),
            validation_400("create_order"),
        )
    )

    b = full_create_body()
    del b["assessment"]["questionnaireResponse"]
    scenarios.append(
        (
            "Create order - fail - Questionnaire response is required",
            "POST /orders without questionnaireResponse returns 400",
            req_post("create_order", "Missing questionnaire", url_orders, headers, b),
            validation_400("create_order"),
        )
    )

    # --- Cancel order ---
    scenarios.append(
        (
            "Cancel - Order does not exist",
            "POST cancel for unknown order returns 404",
            req_post(
                "cancel_order",
                "Cancel nonexistent order",
                "{{env:CAAS_BASE_URL}}/orders/583920417651209834/cancel",
                headers,
                {},
            ),
            [
                status("cancel_order", 404),
                eq("cancel_order.code", 404),
                eq("cancel_order.message", "Order does not exist"),
            ],
        )
    )

    scenarios.append(
        (
            "Cancel - Forbidden",
            "POST cancel with invalid API key returns 403",
            req_post(
                "cancel_order",
                "Cancel with dummy key",
                "{{env:CAAS_BASE_URL}}/orders/123/cancel",
                {"x-api-key": "dummy"},
                {},
            ),
            [status("cancel_order", 403), eq("cancel_order.message", "Forbidden")],
        )
    )

    scenarios.append(
        (
            "Cancel - Dispensed with status delivered",
            "POST cancel for dispensed order returns 409",
            req_post(
                "cancel_order",
                "Cancel dispensed delivered order",
                "{{env:CAAS_BASE_URL}}/orders/{{env:CAAS_ORDER_DISPENSED}}/cancel",
                headers,
                {},
            ),
            [
                status("cancel_order", 409),
                eq("cancel_order.code", 409),
                eq(
                    "cancel_order.message",
                    "Order could not be canceled as it is already dispensed",
                ),
            ],
        )
    )

    scenarios.append(
        (
            "Cancel - Dispensed with status shipped",
            "POST cancel for shipped order returns 409",
            req_post(
                "cancel_order",
                "Cancel dispensed shipped order",
                "{{env:CAAS_BASE_URL}}/orders/{{env:CAAS_ORDER_SHIPPED}}/cancel",
                headers,
                {},
            ),
            [
                status("cancel_order", 409),
                eq("cancel_order.code", 409),
                eq(
                    "cancel_order.message",
                    "Order could not be canceled as it is already dispensed",
                ),
            ],
        )
    )

    b = full_create_body()
    scenarios.append(
        (
            "Cancel - Success",
            "Create order then cancel returns 200 with canceled status",
            {
                **req_post("create_order", "Create order to cancel", url_orders, headers, b),
                **req_post(
                    "cancel_order",
                    "Cancel the order",
                    "{{env:CAAS_BASE_URL}}/orders/{{create_order.orderId}}/cancel",
                    headers,
                    {},
                ),
            },
            [
                status("create_order", 201),
                status("cancel_order", 200),
                eq("cancel_order.status", "canceled"),
            ],
        )
    )

    scenarios.append(
        (
            "Cancel already canceled - Success",
            "Cancel same order twice returns 200 canceled",
            {
                **req_post("create_order", "Create order", url_orders, headers, b),
                **req_post(
                    "cancel_order",
                    "First cancel",
                    "{{env:CAAS_BASE_URL}}/orders/{{create_order.orderId}}/cancel",
                    headers,
                    {},
                ),
                **req_post(
                    "cancel_order_again",
                    "Second cancel",
                    "{{env:CAAS_BASE_URL}}/orders/{{create_order.orderId}}/cancel",
                    headers,
                    {},
                ),
            },
            [
                status("cancel_order", 200),
                status("cancel_order_again", 200),
                eq("cancel_order_again.status", "canceled"),
            ],
        )
    )

    # --- Update patient ---
    patient_url = "{{env:CAAS_BASE_URL}}/patients/{{env:CAAS_PATIENT_ID}}"

    scenarios.append(
        (
            "Update patient",
            "PATCH /patients returns 200 with updated patient",
            req_patch(
                "update_patient",
                "Update patient details",
                patient_url,
                headers,
                patient_update_payload(),
            ),
            [
                status("update_patient", 200),
                eq("update_patient.givenName", "Updated"),
                eq("update_patient.registeredAddress.countryCode", "GB"),
            ],
        )
    )

    scenarios.append(
        (
            "Update patient - missing registered provider",
            "PATCH patient without GP returns 200",
            req_patch(
                "update_patient",
                "Update without GP",
                patient_url,
                headers,
                patient_update_payload(registeredProvider=None),
            ),
            [status("update_patient", 200), eq("update_patient.givenName", "Updated")],
        )
    )

    scenarios.append(
        (
            "Cannot update patient - required fields missing",
            "PATCH patient with empty patient object returns 400",
            req_patch(
                "update_patient",
                "Empty patient",
                patient_url,
                headers,
                {"patient": {}},
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient  - null fields",
            "PATCH patient with null fields returns 400",
            req_patch(
                "update_patient",
                "Null patient fields",
                patient_url,
                headers,
                patient_update_payload(
                    id=None,
                    gender=None,
                    givenName=None,
                    familyName=None,
                    phoneNumber=None,
                    email=None,
                    dateOfBirth=None,
                    verification=None,
                    registeredAddress=None,
                ),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update email address",
            "PATCH patient with different email returns 422",
            req_patch(
                "update_patient",
                "Change email",
                patient_url,
                headers,
                patient_update_payload(email="xyz@testemail.com"),
            ),
            [
                status("update_patient", 422),
                eq("update_patient.code", 422),
                eq("update_patient.message", "PatientGatewayError"),
            ],
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Patient does not exist",
            "PATCH unknown patient returns 404",
            req_patch(
                "update_patient",
                "Update unknown patient",
                "{{env:CAAS_BASE_URL}}/patients/abcdef",
                headers,
                patient_update_payload(id="abcdef"),
            ),
            [
                status("update_patient", 404),
                eq("update_patient.code", 404),
                eq("update_patient.message", "PatientNotFoundException"),
            ],
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Gender is empty string",
            "PATCH patient with empty gender returns 400",
            req_patch(
                "update_patient",
                "Empty gender",
                patient_url,
                headers,
                patient_update_payload(gender=""),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Given name is empty string",
            "PATCH patient with empty givenName returns 422",
            req_patch(
                "update_patient",
                "Empty givenName",
                patient_url,
                headers,
                patient_update_payload(givenName=""),
            ),
            [
                status("update_patient", 422),
                eq("update_patient.code", 422),
                eq("update_patient.message", "PatientGatewayError"),
            ],
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Family name is empty string",
            "PATCH patient with empty familyName returns 422",
            req_patch(
                "update_patient",
                "Empty familyName",
                patient_url,
                headers,
                patient_update_payload(familyName=""),
            ),
            [
                status("update_patient", 422),
                eq("update_patient.code", 422),
                eq("update_patient.message", "PatientGatewayError"),
            ],
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Phone number empty string",
            "PATCH patient with empty phone returns 400",
            req_patch(
                "update_patient",
                "Empty phone",
                patient_url,
                headers,
                patient_update_payload(phoneNumber=""),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Email is empty string",
            "PATCH patient with empty email returns 400",
            req_patch(
                "update_patient",
                "Empty email",
                patient_url,
                headers,
                patient_update_payload(email=""),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient - DOB is empty string",
            "PATCH patient with empty dateOfBirth returns 400",
            req_patch(
                "update_patient",
                "Empty DOB",
                patient_url,
                headers,
                patient_update_payload(dateOfBirth=""),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Verification is required",
            "PATCH patient with empty verification returns 400",
            req_patch(
                "update_patient",
                "Empty verification",
                patient_url,
                headers,
                patient_update_payload(verification=""),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Registered address is required",
            "PATCH patient with empty registeredAddress returns 400",
            req_patch(
                "update_patient",
                "Empty registeredAddress",
                patient_url,
                headers,
                patient_update_payload(registeredAddress={}),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Registered address empty strings",
            "PATCH patient with empty address strings returns 400",
            req_patch(
                "update_patient",
                "Empty address strings",
                patient_url,
                headers,
                patient_update_payload(
                    registeredAddress={
                        "line1": "",
                        "line2": "",
                        "city": "",
                        "state": "",
                        "postalCode": "",
                        "countryCode": "",
                    }
                ),
            ),
            validation_400("update_patient"),
        )
    )

    scenarios.append(
        (
            "Cannot update patient - Registered address nulls",
            "PATCH patient with null address fields returns 400",
            req_patch(
                "update_patient",
                "Null address fields",
                patient_url,
                headers,
                patient_update_payload(
                    registeredAddress={
                        "line1": None,
                        "line2": None,
                        "city": None,
                        "state": None,
                        "postalCode": None,
                        "countryCode": None,
                    }
                ),
            ),
            validation_400("update_patient"),
        )
    )

    # --- Update order ---
    patch_url = "{{env:CAAS_BASE_URL}}/orders/{{create_order.orderId}}"
    shipping_patch = {
        "line1": "Flat 20 Not Mansion House",
        "line2": "9 Not Super Street",
        "city": "Brighton",
        "postalCode": "N1 8YZ",
        "countryCode": "GB",
    }
    media_patch = {
        "assessment": {
            "media": [
                {
                    "id": "{{gen:uuid}}",
                    "url": "https://res.cloudinary.com/zava-www-uk/image/upload/v1748882182/uk/misc/homepage/svf9yrbvjj13tyhtsnv9.png",
                    "label": "scale picture",
                }
            ]
        }
    }

    create_b = full_create_body()
    scenarios.append(
        (
            "Update order successfully - shipping address and assessment media are provided",
            "PATCH order with shipping and media returns 200",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Patch shipping and media",
                    patch_url,
                    headers,
                    {"shippingAddress": shipping_patch, **media_patch},
                ),
            },
            [
                status("create_order", 201),
                status("update_order", 200),
                eq("update_order.status", "new"),
            ],
        )
    )

    scenarios.append(
        (
            "Update order successfully - only assessment media is provided",
            "PATCH order with media only returns 200",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Patch media only",
                    patch_url,
                    headers,
                    media_patch,
                ),
            },
            [status("create_order", 201), status("update_order", 200)],
        )
    )

    scenarios.append(
        (
            "Update order successfully - only shipping address is provided",
            "PATCH order with shipping only returns 200",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Patch shipping only",
                    patch_url,
                    headers,
                    {"shippingAddress": shipping_patch},
                ),
            },
            [status("create_order", 201), status("update_order", 200)],
        )
    )

    scenarios.append(
        (
            "Update order fail - empty payload",
            "PATCH order with empty body returns 400",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch("update_order", "Empty patch", patch_url, headers, {}),
            },
            [status("create_order", 201), status("update_order", 400)],
        )
    )

    scenarios.append(
        (
            "Update order fail - payload nulls",
            "PATCH order with null shipping and assessment returns 400",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Null fields",
                    patch_url,
                    headers,
                    {"shippingAddress": None, "assessment": None},
                ),
            },
            [status("create_order", 201), status("update_order", 400)],
        )
    )

    scenarios.append(
        (
            "Update order fail - shipping address nulls fileds",
            "PATCH order with null nested fields returns 400",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Null nested",
                    patch_url,
                    headers,
                    {
                        "shippingAddress": {
                            "line1": None,
                            "line2": None,
                            "city": None,
                            "postalCode": None,
                            "countryCode": None,
                        },
                        "assessment": {"media": [{"id": None, "url": None, "label": None}]},
                    },
                ),
            },
            [status("create_order", 201), status("update_order", 400)],
        )
    )

    scenarios.append(
        (
            "Update order fail shipping address - required fields missing",
            "PATCH order with empty shippingAddress returns 400",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Empty shipping",
                    patch_url,
                    headers,
                    {"shippingAddress": {}},
                ),
            },
            [status("create_order", 201), status("update_order", 400)],
        )
    )

    scenarios.append(
        (
            "Update order fail shipping address - empty strings",
            "PATCH order with empty shipping strings returns 400",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Empty shipping strings",
                    patch_url,
                    headers,
                    {
                        "shippingAddress": {
                            "line1": "",
                            "line2": "",
                            "city": "",
                            "postalCode": "",
                            "countryCode": "",
                        },
                        **media_patch,
                    },
                ),
            },
            [status("create_order", 201), status("update_order", 400)],
        )
    )

    scenarios.append(
        (
            "Update order fail assessment media - required fields missing",
            "PATCH order with empty media object returns 400",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Empty media",
                    patch_url,
                    headers,
                    {"assessment": {"media": [{}]}},
                ),
            },
            [status("create_order", 201), status("update_order", 400)],
        )
    )

    scenarios.append(
        (
            "Update order fail assessment media - empty strings",
            "PATCH order with empty media strings returns 400",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Empty media strings",
                    patch_url,
                    headers,
                    {
                        "shippingAddress": shipping_patch,
                        "assessment": {"media": [{"id": "", "url": "", "label": ""}]},
                    },
                ),
            },
            [status("create_order", 201), status("update_order", 400)],
        )
    )

    scenarios.append(
        (
            "Update order fail - order is not in a new nor on hold state",
            "PATCH processed order returns 409 OrderAlreadyProcessedException",
            {
                **req_post("create_order", "Create order", url_orders, headers, create_b),
                **req_patch(
                    "update_order",
                    "Patch non-new order",
                    "{{env:CAAS_BASE_URL}}/orders/hh_order_NOT_new_or_on_hold_13eb928a-d09e-4133-98a7-b32a7153da6e",
                    headers,
                    {"shippingAddress": shipping_patch, **media_patch},
                ),
            },
            [
                status("create_order", 201),
                status("update_order", 409),
                eq("update_order.message", "OrderAlreadyProcessedException"),
            ],
        )
    )

    return scenarios


def main():
    base_body = load_base()
    scenarios = build_scenarios(base_body)
    start = datetime(2026, 6, 28, 22, 0, 0)
    created = []

    for i, (name, description, requests, assertions) in enumerate(scenarios):
        if name in SKIP_NAMES:
            continue
        ts = (start + timedelta(seconds=i)).strftime("%Y_%m_%dT%H_%M_%SZ")
        path = TESTS / f"{ts}_test.yml"
        doc = {
            "name": name,
            "description": description,
            "requests": requests,
            "assertions": assertions,
        }
        dump_test(path, doc)
        created.append(path.name)

    print(f"Generated {len(created)} test files")
    for f in created:
        print(f"  tests/{f}")


if __name__ == "__main__":
    main()
