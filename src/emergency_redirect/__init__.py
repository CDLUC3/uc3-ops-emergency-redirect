#!/usr/bin/env python

import sys
import boto3
from botocore.exceptions import ClientError
import yaml
import click
import logging


emergency_message = """<?xml version="1.0"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Service Temporarily Unavailable</title>
<style type="text/css">
body { text-align: center; margin-top: 5em; font-family: Helvetica, sans-serif;
  font-weight: bold }
p.big { font-size: 200%% }
</style>
</head>
<body>
<p>This service is temporarily unavailable.  For more information please visit 
<a href="https://cdlib.org/contact/system-status/">CDL System Status page.</a></p>
</body>
</html>
"""
first_priority = '1'
elbv2 = boto3.client('elbv2')

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


@click.group(invoke_without_command=True)
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging.")
def cli(debug):
    """
    Implements ALB redirect to static page
    """
    if debug:
        logger.setLevel(logging.DEBUG)
        click.echo("Debug mode is active.")
    else:
        logger.setLevel(logging.INFO)


@cli.command('list')
def list():
    """
    List name and eligibility status of each active internet-facing ALB.
    """
    template = "{:<40} {:<12}"
    logger.info(template.format("ALB Name", "Eligibility"))
    logger.info("-" * 52)
    # check for "emegency-redirect" tag 
    for alb in get_internet_facing_alb():
        status = "-"
        if has_tag(alb['LoadBalancerArn'], 'emergency-redirect', 'eligible'):
            status = "eligible"
        logger.info(template.format(alb['LoadBalancerName'], status))


@cli.command('status')
@click.option('--alb-name',
    help='Show activation status only for named ALB')
@click.option("--verbose", "-v",
    is_flag=True,
    help='Display listener rules for named ALB. Requires "--alb-name"')
def status(alb_name, verbose):
    """
    Show emergency redirect activation status of ALBs
    """
    logger.debug(f"Parameters:\n  alb_name: {alb_name}\n  verbose: {verbose}")

    template = "{:<40} {:<12}"

    if alb_name is not None:
        alb = get_alb_by_name(alb_name)
        status = check_activation_status(alb, verbose)
        logger.info(template.format("ALB Name", "Status"))
        logger.info("-" * 52)
        logger.info(template.format(alb['LoadBalancerName'], status))
    else:
        logger.info(template.format("ALB Name", "Status"))
        logger.info("-" * 52)
        for alb in get_internet_facing_alb():
            status = check_activation_status(alb)
            logger.info(template.format(alb['LoadBalancerName'], status))


@cli.command('activate')
@click.option('--all-alb',
    is_flag=True,
    help='Include all eligible ALBs')
@click.option('--alb-name',
    help='Name of an ALB in current account')
def activate(all_alb, alb_name):
    """
    Activate emergency redirect for eligible ALBs
    """
    logger.debug(f"Parameters:\n  all: {all_alb}\n  alb_name: {alb_name}")
    if all_alb is True:
        for alb in get_internet_facing_alb():
            # check for "emegency-redirect" tag
            if has_tag(alb['LoadBalancerArn'], 'emergency-redirect', 'eligible'):
                insert_fixed_response_rule(alb['LoadBalancerArn'])
    elif alb_name is not None:
        alb = get_alb_by_name(alb_name)
        if has_tag(alb['LoadBalancerArn'], 'emergency-redirect', 'eligible'):
            insert_fixed_response_rule(alb['LoadBalancerArn'])
        else:
            logger.error(f"ALB {alb_name} is not elibible for emergency redirect. See documentation")
    else:
        raise click.UsageError("Error: You must provide at least one option: --alb-name or --all-alb")


@cli.command('deactivate')
@click.option('--all-alb',
    is_flag=True,
    help='Include all ALBs')
@click.option('--alb-name',
    help='Name of an ALB in current account')
def deactivate(all_alb, alb_name):
    """
    Deactivate emergency redirect for listed ALBs
    """
    logger.debug(f"Parameters:\n  all: {all_alb}\n  alb_name: {alb_name}")

    if all_alb is True:
        for alb in get_internet_facing_alb():
            delete_fixed_response_rule(alb['LoadBalancerArn'])
    elif alb_name is not None:
        alb = get_alb_by_name(alb_name)
        delete_fixed_response_rule(alb['LoadBalancerArn'])
    else:
        raise click.UsageError("Error: You must provide at least one option: --alb-name or --all-alb")


def get_internet_facing_alb():
    paginator = elbv2.get_paginator('describe_load_balancers')
    for response in paginator.paginate():
        alb_list = [
                lb for lb in response['LoadBalancers'] if (
                    lb['Scheme'] == 'internet-facing' and
                    lb['State']['Code'] == 'active' and
                    lb['Type'] == 'application'
                )
        ]
    return alb_list

def get_alb_by_name(alb_name):
    try:
        response = elbv2.describe_load_balancers(Names=[alb_name])
        logger.debug(yaml.dump(response))
        loadbalancer = response['LoadBalancers'].pop()
    except ClientError as e:
        logger.error(f"Exception: {type(e).__name__}")
        logger.error(e)
        sys.exit(1)
    return loadbalancer

def get_listeners(alb_arn):
    paginator = elbv2.get_paginator('describe_listeners')
    for response in paginator.paginate(LoadBalancerArn=alb_arn):
        logger.debug(yaml.dump(response))
        alb_listeners = [l for l in response['Listeners']]
    return alb_listeners

def get_listener_rules(listener_arn):
    paginator = elbv2.get_paginator('describe_rules')
    for response in paginator.paginate(ListenerArn=listener_arn):
        logger.debug(yaml.dump(response))
        listener_rules = [r for r in response['Rules']]
    return listener_rules

def has_tag(resource_arn, key, value):
    response = elbv2.describe_tags(ResourceArns=[resource_arn])
    tags = response['TagDescriptions'][0]['Tags']
    logger.debug(f"Resource tags:\n{yaml.dump(tags)}")
    matching_tag = next((item for item in tags if item["Key"] == key and item["Value"] == value), False)
    if matching_tag:
        return True
    return False

def check_activation_status(alb, verbose=False):
    status = '-'
    listeners = get_listeners(alb['LoadBalancerArn'])
    if verbose:
        logger.info(f"Listener rules for ALB: {alb['LoadBalancerName']}\n")
    for listener in listeners:
        listener_arn = listener['ListenerArn']
        rules = get_listener_rules(listener_arn)
        if verbose:
            logger.info(f"Listener: {listener_arn}\n")
            logger.info(f"Listener Rules:\n{yaml.dump(rules)}")
        for rule in rules:
            if rule['Priority'] == first_priority:
                logger.debug(rule['RuleArn'])
                if has_tag(rule['RuleArn'], 'emergency-redirect', 'active'):
                    status = 'activated'
    return status

def insert_fixed_response_rule(alb_arn):
    listeners = get_listeners(alb_arn)
    for listener in listeners:
        listener_arn = listener['ListenerArn']
        rules = get_listener_rules(listener_arn)
        priorities = [rule['Priority'] for rule in rules]
        if not first_priority in priorities:
            try:
                # insert new fixed-response rule as first priority
                response = elbv2.create_rule(
                    ListenerArn=listener_arn,
                    Priority=int(first_priority),
                    Actions=[{
                        'Type': 'fixed-response',
                        'FixedResponseConfig': {
                            'MessageBody': emergency_message,
                            'StatusCode': '200',
                            'ContentType': 'text/html'
                        },
                    }],
                    Conditions=[{
                        'Field': 'path-pattern',
                        'PathPatternConfig': {
                            'Values': ['/*']
                        }
                    }],
                    Tags=[{
                        'Key': 'emergency-redirect',
                        'Value': 'active'
                    }],
                )
            except ClientError as e:
                logger.error(f"Exception: {type(e).__name__}")

def delete_fixed_response_rule(alb_arn):
    listeners = get_listeners(alb_arn)
    for listener in listeners:
        listener_arn = listener['ListenerArn']
        rules = get_listener_rules(listener_arn)
        for rule in rules:
            if rule['Priority'] == first_priority:
                logger.debug(rule['RuleArn'])
                if has_tag(rule['RuleArn'], 'emergency-redirect', 'active'):
                    logger.debug(f"deleting rule:\n{yaml.dump(rule)}")
                    elbv2.delete_rule(RuleArn=rule['RuleArn'])


if __name__ == '__main__':
    cli()
