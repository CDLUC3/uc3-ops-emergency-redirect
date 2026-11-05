#!/usr/bin/env python

import sys
import boto3
import yaml
import click

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
        for l in listeners:
            print(yaml.dump(l))
    






def get_internet_facing_alb():
    elbv2 = boto3.client('elbv2')
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
    elbv2 = boto3.client('elbv2')
    paginator = elbv2.get_paginator('describe_listeners')
    for response in paginator.paginate(LoadBalancerArn=alb_arn):
        alb_listeners = [l for l in response['Listeners']]
        print(alb_listeners)
    return alb_listeners



if __name__ == '__main__':
    cli()
