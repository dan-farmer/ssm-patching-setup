#!/usr/bin/env python3
#
# Author: Dan Farmer
# License: GPL3
#   See the "LICENSE" file for full details

"""Common functions for ssm-patching-setup"""

import sys
import boto3
import botocore.exceptions

def get_region(proposed_region):
    """Check if passed region is valid/available, or use user's default region.

    Return region name"""
    if proposed_region:
        # If proposed region is present, check it against available regions
        if proposed_region in get_region_list():
            region = proposed_region
        else:
            raise Exception('Could not find region {0} in list of available regions'.format(
                proposed_region))
    else:
        # If proposed region is False, try to establish the user's default region
        try:
            session = boto3.session.Session()
            region = session.region_name
        except:
            raise Exception('Could not establish region. Specify -r or configure AWS_CREDENTIALS')
    return region

def get_items(client, function, item_name, **args):
    """Generic paginator.

    Yield items in client.function(args)['item_name']
    """
    # Used because botocore is still missing many documented paginators
    # See: https://github.com/boto/botocore/issues/1462
    response = getattr(client, function)(**args)
    while response:
        for item in response[item_name]:
            yield item
        if 'NextToken' in response:
            # If there are more items, re-query with returned NextToken
            response = getattr(client, function)(NextToken=response['NextToken'], **args)
        else:
            response = None

def get_region_list():
    """Return list of AWS regions."""
    try:
        ec2_client = boto3.client('ec2')
    except botocore.exceptions.NoRegionError:
        # If we fail because the user has no default region, use us-east-1
        # This is for listing regions only
        # Iterating resources is then performed in each region
        ec2_client = boto3.client('ec2', region_name='us-east-1')
    try:
        region_list = ec2_client.describe_regions()['Regions']
    except botocore.exceptions.ClientError as err:
        # Handle auth errors etc
        # It is possible for our auth details to expire between this and any later request;
        # We consider this an acceptable race condition
        print('ERROR: {0}'.format(err), file=sys.stderr)
        sys.exit(10)
    for region in region_list:
        yield region['RegionName']
