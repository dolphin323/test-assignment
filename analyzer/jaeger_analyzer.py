import requests


class JaegerAnalyzer:
    TRACE_ENDPOINT = "/api/traces"
    TRACE_DETAILS_ENDPOINT = "/api/traces/{trace_id}"

    def __init__(
        self,
        base_url="http://localhost:16686",
        duration_threshold=50,
        count_threshold=5,
    ):
        self.base_url = base_url
        self.duration_threshold = duration_threshold
        self.count_threshold = count_threshold

    def load_traces(self, service_name, limit=20):
        url = f"{self.base_url}{self.TRACE_ENDPOINT}"
        params = {"service": service_name, "limit": limit}

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()["data"]

    def get_trace_details(self, trace_id):
        url = f"{self.base_url}{self.TRACE_DETAILS_ENDPOINT.format(trace_id=trace_id)}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()["data"][0]

    def extract_logs_from_trace(self, trace):
        logs = []
        for span in trace["spans"]:
            for log in span.get("logs", []):
                logs.append(log)
        return logs

    def extract_db_spans(self, spans):
        db_spans = []
        for span in spans:
            db_statement = None
            db_duration = span["duration"]
            for tag in span["tags"]:
                if tag["key"] == "db.statement":
                    db_statement = tag["value"]
            if db_statement:
                db_spans.append(
                    {
                        "spanID": span["spanID"],
                        "operationName": span["operationName"],
                        "statement": db_statement,
                        "duration": db_duration,
                        "startTime": span["startTime"],
                    }
                )
        return db_spans

    def detect_n_plus_one(self, traces):
        issues = []
        for trace in traces:
            trace_id = trace["traceID"]
            trace_details = self.get_trace_details(trace_id)
            spans = trace_details["spans"]

            db_spans = self.extract_db_spans(spans)
            db_span_total_duration = {}
            db_span_counts = {}

            for db_span in db_spans:
                statement = db_span["statement"]
                if statement not in db_span_counts:
                    db_span_counts[statement] = 0
                    db_span_total_duration[statement] = 0
                db_span_counts[statement] += 1
                db_span_total_duration[statement] += db_span["duration"]

            for statement, count in db_span_counts.items():
                total_duration = db_span_total_duration[statement]
                if (
                    count > self.count_threshold
                    and total_duration > self.duration_threshold
                ):

                    first_db_span_start_time = min(
                        db_span["startTime"]
                        for db_span in db_spans
                        if db_span["statement"] == statement
                    )
                    has_preceding_span = any(
                        span["startTime"] < first_db_span_start_time for span in spans
                    )

                    if has_preceding_span and not statement.endswith("..."):
                        issues.append(
                            {
                                "trace_id": trace_id,
                                "query": statement,
                                "count": count,
                                "total_duration": total_duration,
                                "description": "Potential N+1 query detected",
                            }
                        )
        return issues
