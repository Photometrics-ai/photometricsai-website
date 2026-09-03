"""Small in-process fakes for the boto3 clients lambda_function.py creates
at module level (`dynamodb = boto3.client("dynamodb")`,
`ses = boto3.client("sesv2")`). No network calls, no moto (moto is not
installed in this environment and must not be used).

Not a test module (no test_* functions) — pytest will not collect this
file as tests.
"""


class FakeDynamoDB:
    """Records every call made against it (self.calls, self.put_items) and
    serves configurable canned responses per DynamoDB table:

    - scan(): FIFO queue per table (queue_scan) — supports pagination
      tests where consecutive calls to the same table must return
      different pages.
    - get_item(): a single, repeatable response per table (set_get_item) —
      matches real DynamoDB semantics (the same key returns the same item
      within one request) and lets a test seed one canned "session row"
      that both get_verified_representative_emails() and a possible
      log_send() lookup can each read.
    - put_item(): always recorded (self.put_items / self.put_calls);
      returns {} (DynamoDB's put_item response has no Item unless
      ReturnValues is requested, which this codebase never sets).
    - query() / update_item(): recorded; query has a settable per-table
      response (set_query), update_item always returns {}.

    Any call to a table with no configured response gets a safe empty
    default ({"Items": []} for scan/query, {} for get_item/put_item/
    update_item) so code paths that don't care about the response (e.g.
    failure-tolerant try/except blocks) still work without extra setup.
    """

    def __init__(self):
        self.calls = []  # list of (method_name, kwargs), in call order
        self._scan_queues = {}       # table_name -> list[dict], popped FIFO
        self._get_item_responses = {}   # table_name -> dict, repeatable
        self._query_responses = {}      # table_name -> dict, repeatable
        self.put_items = []          # every Item dict passed to put_item
        self.put_calls = []          # every full kwargs passed to put_item

    # -- test setup -----------------------------------------------------
    def queue_scan(self, table_name, response):
        """Queue one canned response for the next scan() call against
        table_name. Call multiple times to simulate multiple pages."""
        self._scan_queues.setdefault(table_name, []).append(response)

    def set_get_item(self, table_name, response):
        """Set the (repeatable) response for get_item() against
        table_name. response should be {} (no Item) or {"Item": {...}}."""
        self._get_item_responses[table_name] = response

    def set_query(self, table_name, response):
        self._query_responses[table_name] = response

    def calls_for(self, method, table_name=None):
        return [
            kwargs for name, kwargs in self.calls
            if name == method and (table_name is None or kwargs.get("TableName") == table_name)
        ]

    # -- boto3 client surface --------------------------------------------
    def scan(self, **kwargs):
        self.calls.append(("scan", kwargs))
        table = kwargs.get("TableName")
        queue = self._scan_queues.get(table)
        if queue:
            return queue.pop(0)
        return {"Items": []}

    def get_item(self, **kwargs):
        self.calls.append(("get_item", kwargs))
        table = kwargs.get("TableName")
        return self._get_item_responses.get(table, {})

    def put_item(self, **kwargs):
        self.calls.append(("put_item", kwargs))
        self.put_calls.append(kwargs)
        self.put_items.append(kwargs.get("Item", {}))
        return {}

    def query(self, **kwargs):
        self.calls.append(("query", kwargs))
        table = kwargs.get("TableName")
        return self._query_responses.get(table, {"Items": []})

    def update_item(self, **kwargs):
        self.calls.append(("update_item", kwargs))
        return {}


class FakeSES:
    """Records every send_email call (self.calls). Raises for any
    ToAddresses[0] present (case-insensitively) in self.raise_for,
    otherwise returns a canned MessageId."""

    def __init__(self):
        self.calls = []
        self.raise_for = set()  # lowercase emails that should raise
        self.default_message_id = "fake-message-id-0001"

    def send_email(self, **kwargs):
        self.calls.append(kwargs)
        to_addrs = kwargs.get("Destination", {}).get("ToAddresses", [])
        to_addr = (to_addrs[0] if to_addrs else "").lower()
        if to_addr in self.raise_for:
            raise Exception(f"FakeSES: simulated send failure for {to_addr}")
        return {"MessageId": self.default_message_id}
