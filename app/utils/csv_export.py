"""CSV streaming helper for the conversations export endpoint."""
import csv
import io
from flask import Response


def stream_csv(rows, headers, filename="export.csv"):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
