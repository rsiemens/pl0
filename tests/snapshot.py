import json
from os import path

DIR = path.dirname(path.realpath(__file__))
SNAPSHOTS = path.join(DIR, "snapshots.json")


def load():
    try:
        snapshots_fd = open(SNAPSHOTS, "r", encoding="utf8")
    except IOError:
        return {}

    snapshots = json.loads(snapshots_fd.read())
    snapshots_fd.close()
    return snapshots


def capture(snapshot_name, output):
    snapshots = load()
    snapshots[snapshot_name] = output
    with open(SNAPSHOTS, "w+", encoding="utf8") as snapshots_fd:
        snapshots_fd.write(json.dumps(snapshots))


def assert_matches_snapshot(snapshot_name, output):
    snapshots = load()

    if snapshots.get(snapshot_name) is None:
        capture(snapshot_name, output)
        snapshots = load()

    assert (
        output == snapshots[snapshot_name]
    ), f"snapshot {snapshot_name} doesn't match the output"
