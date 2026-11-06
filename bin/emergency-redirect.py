#!/usr/bin/env python

import sys
import boto3
import yaml
import click


elbv2 = boto3.client('elbv2')

document = """<?xml version="1.0"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>EZID</title>
<style type="text/css">
body { text-align: center; margin-top: 5em; font-family: Helvetica, sans-serif;
  font-weight: bold }
p.big { font-size: 200%% }
</style>
</head>
<body>
%s<p class="big">%s</p>
<p>EZID's regularly scheduled maintenance window is Thursday <a
href="http://www.thetimezoneconverter.com/?t=5:00am&amp;tz=Oakland">5:00am</a>&ndash;<a
href="http://www.thetimezoneconverter.com/?t=6:00am&amp;tz=Oakland">6:00am</a>
Pacific time. For more information on system availability,
check <a href="https://ezidstatus.wordpress.com/">EZID's status page.</a></p>
</body>
</html>
"""

first_priority = '1'


# Parse the command-line parameters using 'click' decorators

@click.group(invoke_without_command=True)
def cli():
    """
    Implements ALB redirect to static page
    """
    #click.echo('starts')


# if sub-command 'list'
    # print list ALB names in this account. indicate if a matching message file exists.
@cli.command('list')
def list():
    """
    List names of all active internet-facing ALBs in current AWS account
    """
    for alb in get_internet_facing_alb():
        #print(yaml.dump(lb))
        print(alb['LoadBalancerName'])


# if sub-command 'status'
    # if 'alb_name' add listed alb name to targets list
    # else add all ALB in account to targets list
    # for each target ABL
        # gather listeners and rules
        # determine if emergency-redirect is already active
        # print summery of listeners, rules and ER activation status
    # exit
@cli.command('status')
@click.option('--all',
    is_flag=True,
    help='Include all ALBs')
@click.option('--alb-name',
    help='Name of an ALB in current account')
def status(all, alb_name):
    """
    Show emergency redirect status of ALBs
    """
    print(f"all: {all}")
    print(f"alb_name: {alb_name}")



# if sub-command 'generate'
    # generate a message file from template for this ALB and save it to project data
    # display generate message file
    # direct user to modify and commit saved file into project repository
    # exit




# if option 'activate'
    # if 'message_file'
        # if file exists and is readable
            # read file into 'message' var
        # else
            # error out
    # else 
        # check for matching message file in project data
        # if found 
            # read file into 'message' var
        # else 
            # generate contents of 'message' var from template
    # for each ALB listener create a new rule with priority 1

@cli.command('activate')
@click.option('--all',
    is_flag=True,
    help='Include all ALBs')
@click.option('--alb-name',
    help='Name of an ALB in current account')
@click.option('--message-file',
    help='Path to a html file on the local system')
def activate(all, alb_name, message_file):
    """
    Activate emergency redirect for listed ALBs
    """
    print(f"all: {all}")
    print(f"alb_name: {alb_name}")
    print(f"message_file: {message_file}")

    alb_list = get_internet_facing_alb()
    if alb_name is not None:
        arn = [alb['LoadBalancerArn'] for alb in alb_list if alb['LoadBalancerName'] == alb_name]
        if not arn:
            print(f"Could not find ALB with name {alb_name}")
            sys.exit(1)
        else:
            alb_arn = arn.pop()
        print(f"alb_arn: {alb_arn}")

        listeners = get_listeners(alb_arn)
        for listener in listeners:
            #print(yaml.dump(listener))
            listener_arn = listener['ListenerArn']
            rules = get_listener_rules(listener_arn)
            print(yaml.dump(rules))
            priorities = [rule['Priority'] for rule in rules]
            print(priorities)
            if not first_priority in priorities:
                # insert new fixed-response rule as first priority
                response = elbv2.create_rule(
                    ListenerArn=listener_arn,
                    Priority=first_priority,
                    Actions=[{
                        'Type': 'fixed-response',
                        'FixedResponseConfig': {
                            'MessageBody': document,
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
                        'Key': 'emergency_redirect',
                        'Value': 'active'
                    }],
                )
    


@cli.command('deactivate')
@click.option('--all',
    is_flag=True,
    help='Include all ALBs')
@click.option('--alb-name',
    help='Name of an ALB in current account')
def activate(all, alb_name):
    """
    Deactivate emergency redirect for listed ALBs
    """
    print(f"all: {all}")
    print(f"alb_name: {alb_name}")

    alb_list = get_internet_facing_alb()
    if alb_name is not None:
        arn = [alb['LoadBalancerArn'] for alb in alb_list if alb['LoadBalancerName'] == alb_name]
        if not arn:
            print(f"Could not find ALB with name {alb_name}")
            sys.exit(1)
        else:
            alb_arn = arn.pop()
        print(f"alb_arn: {alb_arn}")

        listeners = get_listeners(alb_arn)
        for listener in listeners:
            #print(yaml.dump(listener))
            listener_arn = listener['ListenerArn']
            print(listener_arn)
            rules = get_listener_rules(listener_arn)
            #print(yaml.dump(rules))
            for rule in rules:
                if rule['Priority'] == first_priority:
                    #print(rule['RuleArn'])
                    tags = get_tags(rule['RuleArn'])
                    #print(yaml.dump(tags))
                    if emergency_redirect_rule_is_active(tags):
                        # delete rule
                        #print(yaml.dump(rule))
                        elbv2.delete_rule(RuleArn=rule['RuleArn'])



def get_tags(resource_arn):
    response = elbv2.describe_tags(ResourceArns=[resource_arn])
    return response['TagDescriptions'][0]['Tags']

def emergency_redirect_rule_is_active(tags):
    key = 'emergency_redirect'
    value = 'active'
    tag = next((item for item in tags if item["Key"] == key and item["Value"] == value), False)
    if tag:
        return True
    return False

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


def get_listeners(alb_arn):
    paginator = elbv2.get_paginator('describe_listeners')
    for response in paginator.paginate(LoadBalancerArn=alb_arn):
        alb_listeners = [l for l in response['Listeners']]
        #print(alb_listeners)
    return alb_listeners


def get_listener_rules(listener_arn):
    paginator = elbv2.get_paginator('describe_rules')
    for response in paginator.paginate(ListenerArn=listener_arn):
        listener_rules = [r for r in response['Rules']]
    return listener_rules


if __name__ == '__main__':
    cli()
