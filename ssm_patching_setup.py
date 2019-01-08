#!/usr/bin/env python3

"""Create SSM Patch Manager resources for simple automated patching use-cases."""

import argparse
import logging
import calendar
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
    if args.loglevel:
        logging.basicConfig(level=args.loglevel)
    ssm_client = boto3.client('ssm')
    baseline_id = create_patch_baseline(ssm_client)
    for week in args.weeks:
        for day in args.days:
            for hour in args.hours:
                # String formatting for 'Patch Group' tag
                patch_group = "Week {0} Day {1} - Unattended - {2}:00".format(
                    str(week), str(day), str(hour).zfill(2))
                # String formatting for Maintenance Window name
                mw_name = "Week{0}Day{1}Unattended{2}00".format(
                    str(week), str(day), str(hour).zfill(2))
                # String formatting for Maintenance Window cron schedule
                mw_schedule = "cron(00 {2} ? * {1}#{0} *)".format(
                    str(week), calendar.day_abbr[day-1].upper(), str(hour).zfill(2))
                # Default timezone; Will need parameterising
                mw_timezone = "Europe/London"
                register_baseline_patch_group(ssm_client, baseline_id, patch_group)
                mw_id = create_maintenance_window(ssm_client, mw_name, mw_schedule, mw_timezone)

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace with 'weeks', 'days' and 'hours' lists"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--weeks', type=int, choices=range(1, 6), nargs='+', required=True,
                        help='Weeks to create maintenance windows (Note: Not full week)')
    parser.add_argument('-d', '--days', type=int, choices=range(0, 8), nargs='+', required=True,
                        help='Days to create maintenance windows (0 = Sunday)')
    parser.add_argument('-t', '--hours', type=int, choices=range(0, 24), nargs='+', required=True,
                        help='Hours (time) to create maintenance windows (0 = Midnight)')
    parser.add_argument('-l', '--loglevel', type=str, required=False,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Hours (time) to create maintenance windows (0 = Midnight)')
    return parser.parse_args()

def create_patch_baseline(ssm_client):
    """Create Patch Baseline.

    Return Baseline ID
    """
    logging.info('Creating Patch Baseline from inline defaults')
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
    print("Created Patch Baseline {0}".format(baseline['BaselineId']))
    return baseline['BaselineId']

def register_baseline_patch_group(ssm_client, baseline_id, patch_group):
    """Register Patch Baseline for Patch Group."""
    # Relying on boto to raise an exception if this fails;
    # This may need revisiting and custom error handling added
    ssm_client.register_patch_baseline_for_patch_group(BaselineId=baseline_id,
                                                       PatchGroup=patch_group)

def create_maintenance_window(ssm_client, name, schedule, timezone):
    """Create Maintenance Window.

    Return Maintenance Window ID
    """
    logging.info('Creating Maintenance Window with schedule %s and timezone %s',
                 schedule, timezone)
    maintenance_window = ssm_client.create_maintenance_window(Name=name,
                                                              Schedule=schedule,
                                                              ScheduleTimezone=timezone,
                                                              Duration=1,
                                                              Cutoff=0,
                                                              AllowUnassociatedTargets=True)
    print("Created Maintenance Window {0}".format(maintenance_window['WindowId']))
    return maintenance_window['WindowId']

def register_patch_group_maintenance_window(ssm_client, mw_id, target_patch_group):
    """Register Patch Group as Maintenance Window Target.

    Return Target ID
    """

def register_task(ssm_client, mw_id, target_id):
    """Register Task in Maintenance Window."""

if __name__ == '__main__':
    main()
