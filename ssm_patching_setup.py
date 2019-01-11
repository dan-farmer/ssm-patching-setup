#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""Create SSM Patch Manager resources for simple automated patching use-cases."""

import argparse
import logging
import calendar
import boto3
from helpers import get_valid_region

def main():
    """Create SSM Patch Manager resources.

    Parse arguments
    Establish region
    Create Patch Baseline
    Register Baseline for Patch Groups
    Create Maintenance Windows
    Register Patch Groups to MWs
    Register MW Tasks
    """

    args = parse_args()
    if args.loglevel:
        logging.basicConfig(level=args.loglevel)
    region = get_valid_region(args.region)

    logging.info('Using region %s', region)
    ssm_client = boto3.client('ssm', region_name=region)

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
                mw_timezone = args.timezone
                register_baseline_patch_group(ssm_client, baseline_id, patch_group)
                mw_id = create_maintenance_window(ssm_client, mw_name, mw_schedule, mw_timezone)
                target_id = register_patch_group_maintenance_window(ssm_client, mw_id, patch_group)
                register_task(ssm_client, mw_id, target_id)

def parse_args():
    """Create arguments and populate variables from args.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--weeks', type=int, choices=range(1, 6), nargs='+', default=[1, 2],
                        help='Weeks to create maintenance windows (Note: Not full week)')
    parser.add_argument('-d', '--days', type=int, choices=range(0, 8), nargs='+', default=[2, 3],
                        help='Days to create maintenance windows (0 = Sunday)')
    parser.add_argument('-t', '--hours', type=int, choices=range(0, 24), nargs='+', default=[3, 4],
                        help='Hours (time) to create maintenance windows (0 = Midnight)')
    parser.add_argument('-z', '--timezone', type=str, default=False,
                        help='Timezone for maintenance window schedules (TZ database name)')
    parser.add_argument('-r', '--region', type=str, help='AWS region', default=False)
    parser.add_argument('-l', '--loglevel', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging/output verbosity')
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
    if baseline['BaselineId']:
        print("Created Patch Baseline {0}".format(baseline['BaselineId']))
    else:
        raise Exception('Failed to create Patch Baseline')
    return baseline['BaselineId']

def register_baseline_patch_group(ssm_client, baseline_id, patch_group):
    """Register Patch Baseline for Patch Group."""
    response = ssm_client.register_patch_baseline_for_patch_group(BaselineId=baseline_id,
                                                                  PatchGroup=patch_group)
    if response['PatchGroup']:
        print('Registered Patch Baseline {0} for Patch Group {1}'.format(baseline_id, patch_group))
    else:
        logging.warning('Failed to register Patch Baseline %s for Patch Group %s',
                        baseline_id, patch_group)

def create_maintenance_window(ssm_client, name, schedule, timezone):
    """Create Maintenance Window.

    Return Maintenance Window ID
    """
    if timezone:
        logging.info('Creating Maintenance Window with schedule %s and timezone %s',
                     schedule, timezone)
        maintenance_window = ssm_client.create_maintenance_window(Name=name,
                                                                  Schedule=schedule,
                                                                  ScheduleTimezone=timezone,
                                                                  Duration=1,
                                                                  Cutoff=0,
                                                                  AllowUnassociatedTargets=True)
    else:
        logging.info('Creating Maintenance Window with schedule %s', schedule)
        maintenance_window = ssm_client.create_maintenance_window(Name=name,
                                                                  Schedule=schedule,
                                                                  Duration=1,
                                                                  Cutoff=0,
                                                                  AllowUnassociatedTargets=True)
    if maintenance_window['WindowId']:
        print("Created Maintenance Window {0}".format(maintenance_window['WindowId']))
    else:
        raise Exception('Failed to created Maintenance Window for schedule {0}'.format(schedule))
    return maintenance_window['WindowId']

def register_patch_group_maintenance_window(ssm_client, mw_id, target_patch_group):
    """Register Patch Group as Maintenance Window Target.

    Return Target ID
    """
    logging.info('Registering Patch Group %s as target for Maintenance Window %s',
                 target_patch_group, mw_id)
    target = {'Key': 'tag:Patch Group', 'Values': [target_patch_group]}
    registration = ssm_client.register_target_with_maintenance_window(WindowId=mw_id,
                                                                      ResourceType='INSTANCE',
                                                                      Targets=[target])
    if registration['WindowTargetId']:
        print("Created Maintenance Window target {0}".format(registration['WindowTargetId']))
    else:
        raise Exception('Failed to register Patch Group {0} as Maintenance Window Target'.format(
            target_patch_group))
    return registration['WindowTargetId']

def register_task(ssm_client, mw_id, target_id):
    """Register Task in Maintenance Window."""
    logging.info('Registering Task for Target %s in Maintenance Window %s', target_id, mw_id)
    targets = [{'Key': 'WindowTargetIds',
                'Values': [target_id]}]
    parameters = {'RunCommand': {'Parameters': {'Operation': ['Install']}}}
    task = ssm_client.register_task_with_maintenance_window(WindowId=mw_id,
                                                            Targets=targets,
                                                            TaskArn='AWS-ApplyPatchBaseline',
                                                            TaskType='RUN_COMMAND',
                                                            TaskInvocationParameters=parameters,
                                                            MaxConcurrency='2',
                                                            MaxErrors='1')
    if task['WindowTaskId']:
        print("Created Maintenance Window task {0}".format(task['WindowTaskId']))
    else:
        logging.warning('Failed to register Task for Target %s in Maintenance Window %s',
                        target_id, mw_id)

if __name__ == '__main__':
    main()
