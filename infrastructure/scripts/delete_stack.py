#!/usr/bin/env python3
"""Delete a CloudFormation stack with safety checks."""

import argparse
import sys
import time

import boto3
from botocore.exceptions import ClientError


def delete_stack(stack_name: str, region: str, force: bool = False) -> None:
    """Delete a CloudFormation stack."""
    cf = boto3.client("cloudformation", region_name=region)

    # Check stack exists
    try:
        response = cf.describe_stacks(StackName=stack_name)
        stack = response["Stacks"][0]
    except ClientError as e:
        if "does not exist" in str(e):
            print(f"Stack '{stack_name}' does not exist.")
            return
        raise

    # Safety check for production
    env_tag = next(
        (t["Value"] for t in stack.get("Tags", []) if t["Key"] == "Environment"), ""
    )
    if env_tag == "production" and not force:
        print("ERROR: Cannot delete production stack without --force flag.")
        sys.exit(1)

    # Confirm
    if not force:
        confirm = input(f"Delete stack '{stack_name}' ({env_tag})? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

    # Disable termination protection if enabled
    if stack.get("EnableTerminationProtection"):
        print("Disabling termination protection...")
        cf.update_termination_protection(
            StackName=stack_name, EnableTerminationProtection=False
        )

    # Delete
    print(f"Deleting stack '{stack_name}'...")
    cf.delete_stack(StackName=stack_name)

    # Wait for deletion
    print("Waiting for deletion to complete...")
    waiter = cf.get_waiter("stack_delete_complete")
    try:
        waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60})
        print(f"Stack '{stack_name}' deleted successfully.")
    except Exception as e:
        print(f"ERROR: Stack deletion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a CloudFormation stack")
    parser.add_argument("stack_name", help="Name of the stack to delete")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--force", action="store_true", help="Force delete (skip confirmation)")
    args = parser.parse_args()

    delete_stack(args.stack_name, args.region, args.force)
