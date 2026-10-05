"""Deterministic admin API testbed. No mocked test may reach a real API."""
from copy import deepcopy
from urllib.parse import urlsplit, parse_qs
from utils.helpers import iso_now, make_postal_codes_payload, make_devices_payload, make_discrepancy_payload

BARCODE = "100010000000000000000001"
DEVICE_ID = "DEV-001"
EDGE_ID = "QA-EDGE-001"
FAKE_SECRET = "QA-only-secret-not-a-real-credential"


class AdminTestbed:
    def __init__(self):
        self.calls = []
        self.unexpected = []
        self.faults = {}
        self.overrides = {}
        self.devices = make_devices_payload()["items"]
        for i, device in enumerate(self.devices, 1):
            device["logicalCode"] = f"QA-SCANNER-{i}"
            device.update(owner="QA", description="QA device", updatedAt=iso_now())
        self.edges = [dict(edgeId=f"QA-EDGE-00{i}", authorizedCenterCode="10001",
                           isActive=i == 1, createdAtUtc=iso_now(), disabledAtUtc=None,
                           lastCredentialRotationAt=None, securityVersion=1) for i in (1, 2)]
        self.parcels = [dict(parcelBarcode=f"100010000000000000000{i:03d}",
                            parcelType="Parcel", serviceType="Express" if i % 2 else "Registered",
                            originCode="10001", destinationCode="10002", exchangeCenterCode="10001",
                            inboundFinalStatus="Accepted", createdAtUtc=iso_now()) for i in range(1, 13)]
        self.bags = [dict(bagBarcode=f"QA-BAG-{i:03d}", state="Closed", originCenter="10001",
                         destCenter="10002", sealNumber=f"QA-SEAL-{i}", transportType="Road",
                         createdAtUtc=iso_now()) for i in range(1, 13)]
        self.dispatches = [dict(dispatchId=f"QA-DISPATCH-{i:03d}", destCenter="10002",
                               createdAtUtc=iso_now()) for i in range(1, 13)]

    @property
    def mutations(self):
        return [call for call in self.calls if call["method"] not in ("GET", "OPTIONS")]

    def page_data(self, items, query):
        page = int(query.get("page", [1])[0]); size = int(query.get("pageSize", [10])[0])
        center = query.get("exchangeCenterCode", [""])[0]
        filtered = [x for x in items if not center or
                    x.get("exchangeCenterCode", x.get("authorizedCenterCode", x.get("originCenter", "10001"))) == center]
        return dict(items=deepcopy(filtered[(page - 1)*size:page*size]),
                    page=page, pageSize=size, totalCount=len(filtered))

    def install(self, page):
        page.route("**/api/**", self.handle)

    def handle(self, route):
        request = route.request
        path = urlsplit(request.url).path; query = parse_qs(urlsplit(request.url).query)
        body = request.post_data_json if request.post_data else None
        self.calls.append(dict(method=request.method, path=path, query=query, body=body))
        def reply(data=None, status=200):
            if status == 204:
                route.fulfill(status=204, body="")
            else:
                route.fulfill(status=status, json=data)
        if request.method == "OPTIONS":
            route.fulfill(status=204, headers={"Access-Control-Allow-Origin": "*"})
            return
        key = (request.method, path)
        if key in self.faults:
            reply(dict(title="QA simulated API failure", detail="QA simulated API failure"), self.faults[key]); return
        if key in self.overrides:
            reply(self.overrides[key]); return
        if path == "/api/admin/postal-codes" and request.method == "GET":
            payload = make_postal_codes_payload()
            term = query.get("search", [""])[0]
            payload["items"] = [x for x in payload["items"] if not term or term in x["code"] or term in x["name"]]
            payload["totalCount"] = len(payload["items"]); reply(payload); return
        if path == "/api/admin/parcels/discrepancies" and request.method == "GET":
            reply(make_discrepancy_payload()); return
        for suffix, data in (("parcels", self.parcels), ("bags", self.bags), ("dispatches", self.dispatches),
                             ("devices", self.devices), ("edges", self.edges)):
            if path == f"/api/admin/{suffix}" and request.method == "GET":
                reply(self.page_data(data, query)); return
        if path.startswith("/api/admin/parcels/") and request.method == "GET":
            barcode = path.rsplit("/", 1)[-1]
            parcel = next((x for x in self.parcels if x["parcelBarcode"] == barcode), None)
            if not parcel: reply(dict(title="Parcel not found"), 404); return
            reply(dict(**deepcopy(parcel), operationalDestinationCode="10002", exportStatus="Pending",
                       events=[dict(id="QA-EVENT-1", title="QA inbound accepted", description="QA scan",
                                    exchangeCenterCode="10001", occurredAt=iso_now(), state="active")],
                       readings=[dict(readingId="QA-READ-1", deviceId=DEVICE_ID, exchangeCenterCode="10001",
                                      edgeEventTimeUtc=iso_now(), coreReceiveTimeUtc=iso_now(), weight=750,
                                      discrepancies=[dict(discrepancyType="Weight", description="QA weight difference",
                                                          createdAtUtc=iso_now())],
                                      attachments=[dict(objectKey="qa/images/parcel-001.jpg", contentType="image/jpeg",
                                                        attachmentType="Image", receivedAtUtc=iso_now())])]))
            return
        if path == "/api/admin/devices" and request.method == "POST":
            item = dict(body, deviceId="DEV-NEW", activationStatus="Active", createdAt=iso_now(),
                        updatedAt=iso_now(), rowVersion="QA-V1")
            self.devices.append(item); reply(dict(item, deviceToken=FAKE_SECRET), 201); return
        if path.startswith("/api/admin/devices/"):
            device_id = path.split('/')[4]
            item = next((x for x in self.devices if x["deviceId"] == device_id), None)
            if item and request.method == "GET": reply(item); return
            if item and request.method == "PUT":
                item.update(body); item["rowVersion"] = "QA-V2"; reply(item); return
            if item and request.method == "PATCH" and path.endswith(("/activate", "/deactivate")):
                item["activationStatus"] = "Active" if path.endswith('/activate') else "Inactive"
                item["rowVersion"] = "QA-V2"; reply(status=204); return
        if path == "/api/admin/edges" and request.method == "POST":
            self.edges.append(dict(edgeId=body["edgeId"], authorizedCenterCode=body["authorizedCenterCode"],
                                   isActive=True, createdAtUtc=iso_now(), disabledAtUtc=None,
                                   lastCredentialRotationAt=None, securityVersion=1))
            reply(dict(edgeId=body["edgeId"], clientId=body["clientId"], plaintextSecret=FAKE_SECRET), 201); return
        if path.startswith('/api/admin/edges/'):
            edge_id = path.split('/')[4]
            item = next((x for x in self.edges if x["edgeId"] == edge_id), None)
            if item and request.method == "GET": reply(item); return
            if item and request.method == "POST" and path.endswith(("/enable", "/disable")):
                item["isActive"] = path.endswith('/enable'); reply(status=204); return
        if path == "/api/admin/configuration-snapshots" and request.method == "POST":
            reply(dict(**body, configVersion=2, generatedAt=iso_now(), publishedAt=iso_now(),
                       deviceIds=[DEVICE_ID], postalCodes=make_postal_codes_payload()["items"])); return
        self.unexpected.append(f"{request.method} {path}")
        reply(dict(title="Unmocked API request blocked"), 501)
