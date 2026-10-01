import json
from unittest.mock import patch
import pytest
from ffed_qlc.local_otlp import emit_gateway_submit_counter, emit_otel_counter, local_metrics_endpoint


def test_telemetry_is_disabled_without_explicit_opt_in():
    with patch.dict("os.environ", {}, clear=True), patch("urllib.request.build_opener") as transport:
        assert emit_gateway_submit_counter("enforcer_check", ()) is False
        transport.assert_not_called()


@pytest.mark.parametrize("endpoint", ["https://example.com/v1/metrics", "http://localhost:4318/v1/metrics", "http://127.0.0.1:4318/v1/metrics?token=x", "http://user:password@127.0.0.1:4318/v1/metrics", "http://127.0.0.1:8125/v1/metrics"])
def test_remote_credentials_and_unapproved_endpoints_are_rejected(endpoint):
    assert not local_metrics_endpoint(endpoint)
    with patch.dict("os.environ", {"SECUREDME_OTEL_ENABLED": "true", "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT": endpoint}), patch("urllib.request.build_opener") as transport:
        assert not emit_gateway_submit_counter("enforcer_check", ())
        transport.assert_not_called()


class Response:
    status = 200
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, maximum): return self.body[:maximum]


def test_otlp_counter_excludes_arbitrary_identifiers_and_content():
    with patch.dict("os.environ", {"SECUREDME_OTEL_ENABLED": "true", "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT": "http://127.0.0.1:4318/v1/metrics"}), patch("urllib.request.build_opener") as factory:
        factory.return_value.open.return_value = Response(b"{}")
        assert emit_gateway_submit_counter("enforcer_check", ("platform:codex", "decision:allow", "school:private-school", "route:private-prompt", "repo:private-repo"))
        req = factory.return_value.open.call_args.args[0]
        body = json.loads(req.data)
        point = body["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["sum"]["dataPoints"][0]
        assert point["asInt"] == "1"
        assert {a["key"] for a in point["attributes"]} == {"platform", "decision"}
        assert "private" not in req.data.decode()
        assert factory.return_value.open.call_args.kwargs["timeout"] == 0.5


@pytest.mark.parametrize("response", [b'{"partialSuccess":{"rejectedDataPoints":"1"}}', b"x" * 8193, b"not-json", b"[]"])
def test_rejected_or_unbounded_responses_are_not_success(response):
    with patch.dict("os.environ", {"SECUREDME_OTEL_ENABLED": "true", "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT": "http://127.0.0.1:4318/v1/metrics"}), patch("urllib.request.build_opener") as factory:
        factory.return_value.open.return_value = Response(response)
        assert not emit_otel_counter("securedme.education.auth.enforcer_check")
