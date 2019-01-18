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
import helpers

def main():
    """Delete SSM Patch Manager resources.

    Parse command-line arguments
    Establish region
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
    region = helpers.get_region(args.region)

    logging.info('Using region %s', region)
    ssm_client = boto3.client('ssm', region_name=region)

    # Iterate through Maintenance Windows
    mw_enabled_filter = {'Key':'Enabled', 'Values':['true']}
    for maint_window in helpers.get_items(client=ssm_client,
                                          function='describe_maintenance_windows',
                                          item_name='WindowIdentities',
                                          Filters=[mw_enabled_filter]):
        logging.info('Considering Maintenance Window %s', maint_window['WindowId'])
        # Iterate through Tasks
        for task in helpers.get_items(client=ssm_client,
                                      function='describe_maintenance_window_tasks',
                                      item_name='Tasks',
                                      WindowId=maint_window['WindowId']):
            logging.info('Considering Task %s', task['WindowTaskId'])
            # If TaskArn is one of the AWS-supplied SSM Patch Manager tasks, delete it
            if ((task['TaskArn'] == 'AWS-ApplyPatchBaseline') or
                    (task['TaskArn'] == 'AWS-RunPatchBaseline')):
                logging.info('Task %s has TaskArn %s, deleting',
                             task['WindowTaskId'], task['TaskArn'])
                delete_task(ssm_client, maint_window['WindowId'], task['WindowTaskId'])
            else:
                logging.info('Task %s has TaskArn %s',
                             task['WindowTaskId'], task['TaskArn'])
        # Re-fetch the Tasks for this Maintenance Window
        tasks = helpers.get_items(client=ssm_client,
                                  function='describe_maintenance_window_tasks',
                                  item_name='Tasks',
                                  WindowId=maint_window['WindowId'])
        tasks_number = sum(1 for task in tasks)
        logging.info('Number of tasks remaining for Maintenance Window %s: %s',
                     maint_window['WindowId'], tasks_number)
        # If no Tasks remain for this Maintenance Window, delete it
        if tasks_number == 0:
            delete_maintenance_window(ssm_client, maint_window['WindowId'])

    # Iterate through Patch Groups; Deregister baselines
    for patch_group in helpers.get_items(client=ssm_client,
                                         function='describe_patch_groups',
                                         item_name='Mappings'):
        deregister_baseline(ssm_client,
                            patch_group['PatchGroup'],
                            patch_group['BaselineIdentity']['BaselineId'])

    # Iterate through Baselines
    for baseline in helpers.get_items(client=ssm_client,
                                      function='describe_patch_baselines',
                                      item_name='BaselineIdentities'):
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
    parser.add_argument('-r', '--region', type=str, help='AWS region', default=False)
    parser.add_argument('-l', '--loglevel', type=str, required=False,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging/output verbosity')
    return parser.parse_args()

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

def deregister_baseline(ssm_client, patch_group, baseline):
    """Deregister Baseline for Patch Group."""
    response = ssm_client.deregister_patch_baseline_for_patch_group(BaselineId=baseline,
                                                                    PatchGroup=patch_group)
    if response['PatchGroup']:
        print("Deregistered Baseline {0} for Patch Group {1}".format(baseline, patch_group))
    else:
        logging.error('Failed to deregister Baseline %s for Patch Group %s', baseline, patch_group)

def delete_baseline(ssm_client, baseline):
    """Delete a Patch Baseline."""
    response = ssm_client.delete_patch_baseline(BaselineId=baseline)
    if response['BaselineId']:
        print("Deleted Patch Baseline {0}".format(baseline))
    else:
        logging.error('Failed to delete Patch Baseline %s', baseline)

if __name__ == '__main__':
    main()
