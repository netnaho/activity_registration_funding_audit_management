import logging

from app.logging.logger import JsonFormatter


def test_json_formatter_includes_channel_category_event_and_context():
    logger = logging.getLogger("test.logger")
    record = logger.makeRecord(
        "test.logger",
        logging.WARNING,
        fn="x.py",
        lno=1,
        msg="sample_event",
        args=(),
        exc_info=None,
        extra={
            "category": "operational",
            "event": "request_completed",
            "request_id": "abc123",
            "context": {"status_code": 404, "token": "secret"},
        },
    )

    formatter = JsonFormatter()
    output = formatter.format(record)
    assert '"channel": "WARNING"' in output
    assert '"category": "operational"' in output
    assert '"event": "request_completed"' in output
    assert '"request_id": "abc123"' in output
    assert '"token": "***REDACTED***"' in output
