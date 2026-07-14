from __future__ import annotations
import argparse
import json
from .agent import EdgeAgent


def main() -> None:
    parser = argparse.ArgumentParser(prog="openinspect-edge")
    parser.add_argument("--root", default="./edge-data")
    parser.add_argument("--device-id", default="edge-local")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest")
    ingest.add_argument("image")
    ingest.add_argument("--mission-type", choices=["structural", "pipeline"], required=True)
    sub.add_parser("health")
    args = parser.parse_args()
    agent = EdgeAgent(args.root, args.device_id)
    if args.command == "ingest":
        print(json.dumps(agent.ingest(args.image, args.mission_type), indent=2))
    else:
        from dataclasses import asdict
        print(json.dumps(asdict(agent.health()), indent=2))


if __name__ == "__main__":
    main()
