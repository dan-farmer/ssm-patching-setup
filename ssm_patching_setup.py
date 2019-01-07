#!/usr/bin/env python3

"""Create SSM Patch Manager resources for simple automated patching use-cases."""

import argparse
import boto3

def main():
    """Create SSM Patch Manager resources.

    Create Patch Baseline
    Register Baseline for Patch Groups
    Create Maintenance Windows
    Register Patch Groups to MWs
    Register MW Tasks
    """
    args = parse_args()

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    return parser.parse_args()

def create_patch_baseline(ssm_client):
    """Create Patch Baseline.

    Return Baseline ID
    """

def register_baseline_patch_group(ssm_client, baseline_id, patch_group):
    """Register Patch Baseline for Patch Group."""

def create_maintenance_window(ssm_client, name, schedule, timezone):
    """Create Maintenance Window.

    Return Maintenance Window ID
    """

def register_patch_group_maintenance_window(ssm_client, mw_id, target_patch_group):
    """Register Patch Group as Maintenance Window Target.

    Return Target ID
    """

def register_task(ssm_client, mw_id, target_id):
    """Register Task in Maintenance Window."""

if __name__ == '__main__':
    main()
