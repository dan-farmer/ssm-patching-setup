#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""Destroy SSM Patch Manager resources on an AWS account.

- All Maintenance Window Tasks for 'AWS-ApplyPatchBaseline' or 'AWS-RunPatchBaseline'
- All Maintenance Windows with no tasks or only patching tasks as above
- All Patch Baseline registrations for Patch Groups
- All custom Patch Baselines"""

import argparse
import logging
import boto3

def main():
    """Delete SSM Patch Manager resources.

    Parse command-line arguments
    Iterate through Maintenance Windows
    Iterate through Tasks
    Delete patching-specific Tasks
    Delete Maintenance Windows with no Tasks
    Iterate through Patch Groups
    Deregister Baseline for Patch Groups
    Iterate through Patch Baselines
    Delete non-default Baselines"""
    args = parse_args()
    if args.loglevel:
        logging.basicConfig(level=args.loglevel)

def parse_args():
    """Create arguments.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loglevel', type=str, required=False,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Output logging verbosity')
    return parser.parse_args()

def get_maintenance_windows():
    """."""

def get_maintenance_window_tasks():
    """."""

def delete_task():
    """."""

def delete_maintenance_window():
    """."""

def deregister_baseline():
    """."""

def get_baselines():
    """."""

def delete_baseline():
    """."""

if __name__ == '__main__':
    main()
