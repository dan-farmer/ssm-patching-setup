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
    ssm_client = boto3.client('ssm')

    # Iterate through Maintenance Windows
    for maintenance_window in get_maintenance_windows(ssm_client):
        logging.info('Considering Maintenance Window %s', maintenance_window['WindowId'])
        # Iterate through Tasks
        for task in get_maintenance_window_tasks(ssm_client, maintenance_window['WindowId']):
            logging.info('Considering Task %s', task['WindowTaskId'])
            # If TaskArn is one of the AWS-supplied SSM Patch Manager tasks, delete it
            if ((task['TaskArn'] == 'AWS-ApplyPatchBaseline') or
                    (task['TaskArn'] == 'AWS-RunPatchBaseline')):
                logging.info('Task %s has TaskArn %s, deleting',
                             task['WindowTaskId'], task['TaskArn'])
                delete_task(ssm_client, maintenance_window['WindowId'], task['WindowTaskId'])
            else:
                logging.info('Task %s has TaskArn %s',
                             task['WindowTaskId'], task['TaskArn'])
        # Re-fetch the Tasks for this Maintenance Window
        tasks = get_maintenance_window_tasks(ssm_client, maintenance_window['WindowId'])
        tasks_number = sum(1 for task in tasks)
        logging.info('Number of tasks remaining for Maintenance Window %s: %s',
                     maintenance_window['WindowId'], tasks_number)
        # If no Tasks remain for this Maintenance Window, delete it
        if tasks_number == 0:
            delete_maintenance_window(ssm_client, maintenance_window['WindowId'])

    # Iterate through Patch Groups; Deregister baselines
    for patch_group in get_patch_groups(ssm_client):
        deregister_baseline(ssm_client,
                            patch_group['PatchGroup'],
                            patch_group['BaselineIdentity']['BaselineId'])

    # Iterate through Baselines
    for baseline in get_baselines(ssm_client):
        logging.info('Considering Patch Baseline %s', baseline['BaselineId'])
        # If this is not a Default Baseline, delete it
        if not baseline['DefaultBaseline']:
            logging.info('Baseline %s is not a Default Baseline, deleting', baseline['BaselineId'])
            delete_baseline(ssm_client, baseline['BaselineId'])
        else:
            logging.info('Baseline %s is a Default Baseline', baseline['BaselineId'])

def parse_args():
    """Create arguments.

    Return args namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loglevel', type=str, required=False,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Output logging verbosity')
    return parser.parse_args()

def get_maintenance_windows(ssm_client):
    """Yield SSM Maintenance Windows."""
    next_token = True
    filters = {'Key':'Enabled', 'Values':['true']}
    while next_token:
        if next_token is not True:
            maint_window_list = ssm_client.describe_maintenance_windows(
                Filters=[filters],
                NextToken=next_token)
        else:
            maint_window_list = ssm_client.describe_maintenance_windows(
                Filters=[filters])
        if 'NextToken' in maint_window_list:
            next_token = maint_window_list['NextToken']
        else:
            next_token = False
        for window in maint_window_list['WindowIdentities']:
            yield window

def get_maintenance_window_tasks(ssm_client, maint_window_id):
    """Yield Maintenance Window Tasks."""
    next_token = True
    while next_token:
        if next_token is not True:
            task_list = ssm_client.describe_maintenance_window_tasks(
                WindowId=maint_window_id,
                NextToken=next_token)
        else:
            task_list = ssm_client.describe_maintenance_window_tasks(
                WindowId=maint_window_id)
        if 'NextToken' in task_list:
            next_token = task_list['NextToken']
        else:
            next_token = False
        for task in task_list['Tasks']:
            yield task

def delete_task(ssm_client, maint_window_id, task_id):
    """Delete Maintenance Window Task."""
    response = ssm_client.deregister_task_from_maintenance_window(WindowId=maint_window_id,
                                                                  WindowTaskId=task_id)
    if response['WindowTaskId']:
        print("Deregistered Task {0} from Maintenance Window {1}".format(task_id, maint_window_id))
    else:
        logging.error('Failed to deregister Task %s from Maintenance Window %s',
                      task_id, maint_window_id)

def delete_maintenance_window(ssm_client, maint_window_id):
    """Delete Maintenance Window."""
    response = ssm_client.delete_maintenance_window(WindowId=maint_window_id)
    if response['WindowId']:
        print("Deleted Maintenance Window {0}".format(maint_window_id))
    else:
        logging.error('Failed to delete Maintenance Window %s', maint_window_id)

def get_patch_groups(ssm_client):
    """Yield Patch Groups."""
    next_token = True
    while next_token:
        if next_token is not True:
            patch_group_list = ssm_client.describe_patch_groups(NextToken=next_token)
        else:
            patch_group_list = ssm_client.describe_patch_groups()
        if 'NextToken' in patch_group_list:
            next_token = patch_group_list['NextToken']
        else:
            next_token = False
        for patch_group in patch_group_list['Mappings']:
            yield patch_group

def deregister_baseline(ssm_client, patch_group, baseline):
    """Deregister Baseline for Patch Group."""
    response = ssm_client.deregister_patch_baseline_for_patch_group(BaselineId=baseline,
                                                                    PatchGroup=patch_group)
    if response['PatchGroup']:
        print("Deregistered Baseline {0} for Patch Group {1}".format(baseline, patch_group))
    else:
        logging.error('Failed to deregister Baseline %s for Patch Group %s', baseline, patch_group)

def get_baselines(ssm_client):
    """Yield Patch Baselines."""
    next_token = True
    while next_token:
        if next_token is not True:
            baseline_list = ssm_client.describe_patch_baselines(NextToken=next_token)
        else:
            baseline_list = ssm_client.describe_patch_baselines()
        if 'NextToken' in baseline_list:
            next_token = baseline_list['NextToken']
        else:
            next_token = False
        for baseline in baseline_list['BaselineIdentities']:
            yield baseline

def delete_baseline(ssm_client, baseline):
    """Delete a Patch Baseline."""
    response = ssm_client.delete_patch_baseline(BaselineId=baseline)
    if response['BaselineId']:
        print("Deleted Patch Baseline {0}".format(baseline))
    else:
        logging.error('Failed to delete Patch Baseline %s', baseline)

if __name__ == '__main__':
    main()
