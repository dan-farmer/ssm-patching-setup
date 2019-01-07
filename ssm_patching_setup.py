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
    ssm_client = boto3.client('ssm')
    baseline_id = create_patch_baseline(ssm_client)

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace with 'weeks', 'days' and 'hours' lists"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--weeks', type=int, choices=range(1, 6), nargs='+', required=True,
                        help='Weeks to create maintenance windows (Note: Not full week)')
    parser.add_argument('-d', '--days', type=int, choices=range(0, 8), nargs='+', required=True,
                        help='Days to create maintenance windows (0 = Sunday)')
    parser.add_argument('-h', '--hours', type=int, choices=range(0, 24), nargs='+', required=True,
                        help='Hours to create maintenance windows (0 = Midnight)')
    return parser.parse_args()

def create_patch_baseline(ssm_client):
    """Create Patch Baseline.

    Return Baseline ID
    """
    baseline = ssm_client.create_patch_baseline(
        OperatingSystem='WINDOWS',
        Name='Windows-0day-Important',
        GlobalFilters={
            'PatchFilters': [
                {
                    'Key': 'PRODUCT',
                    'Values': [
                        '*'
                    ]
                }
            ]
        },
        ApprovalRules={
            'PatchRules': [
                {
                    'PatchFilterGroup': {
                        'PatchFilters': [
                            {
                                'Key': 'CLASSIFICATION',
                                'Values': [
                                    'CriticalUpdates',
                                    'SecurityUpdates'
                                ]
                            },
                            {
                                'Key': 'MSRC_SEVERITY',
                                'Values': [
                                    'Important'
                                ]
                            }
                        ]
                    },
                    'ComplianceLevel': 'UNSPECIFIED',
                    'ApproveAfterDays': 0,
                    'EnableNonSecurity': False
                }
            ]
        },
        ApprovedPatches=[],
        ApprovedPatchesComplianceLevel='UNSPECIFIED',
        ApprovedPatchesEnableNonSecurity=False,
        RejectedPatches=[],
        RejectedPatchesAction='ALLOW_AS_DEPENDENCY',
        Description='Custom baseline with auto approval at 0 days and MSRC severity "Important"',
        Sources=[]
    )
    return baseline['BaselineId']

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
