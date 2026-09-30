"""Attach a daily SPICE refresh schedule to a QuickSight dataset.

Deploy-time helper: run it after the QuickSight dataset exists (created
from the Athena table per quicksight/dashboard_spec.md). Needs AWS
credentials with quicksight:CreateRefreshSchedule permissions.

Usage:
    python python/schedule_quicksight_refresh.py \
        --dataset-id <dataset-id> --account <aws-account-id> \
        [--region us-east-1] [--hour 5]
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone


def main(argv=None):
    parser = argparse.ArgumentParser(description="Schedule a daily QuickSight SPICE refresh.")
    parser.add_argument("--dataset-id", required=True, help="QuickSight dataset id")
    parser.add_argument("--account", required=True, help="AWS account id owning the dataset")
    parser.add_argument("--region", default=None, help="AWS region (defaults to your CLI config)")
    parser.add_argument("--hour", type=int, default=5, help="refresh hour in UTC (default: 5)")
    parser.add_argument("--schedule-id", default="daily-refresh", help="schedule id")
    args = parser.parse_args(argv)

    if not 0 <= args.hour <= 23:
        sys.exit("--hour must be between 0 and 23")

    try:
        import boto3
    except ImportError:
        sys.exit("boto3 is required: pip install boto3")

    quicksight = boto3.client("quicksight", region_name=args.region)
    tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)

    response = quicksight.create_refresh_schedule(
        DatasetId=args.dataset_id,
        AwsAccountId=args.account,
        Schedule={
            "ScheduleId": args.schedule_id,
            "ScheduleFrequency": {"Frequency": "DAILY"},
            "StartAfterDateTime": datetime(
                tomorrow.year, tomorrow.month, tomorrow.day,
                args.hour, 0, 0, tzinfo=timezone.utc,
            ),
            "Timezone": "UTC",
        },
    )
    status = response.get("Status")
    schedule_id = response.get("Schedule", {}).get("ScheduleId", args.schedule_id)
    print(f"Daily refresh scheduled (HTTP {status}): dataset={args.dataset_id} "
          f"schedule={schedule_id} at {args.hour:02d}:00 UTC")


if __name__ == "__main__":
    main()
