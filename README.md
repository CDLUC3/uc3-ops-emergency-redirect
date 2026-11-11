# UC3 Emergency Redirect

A command-line tool for temporarily replacing application responses with a
static maintenance page.


## Rationale

In the face of AI driven software exploits, we may need to block access to UC3
applications at a moments notice until the risk is understood and mitigation is
available.  

#### Goals

- easy to use mechnism to activate/deactivate emergency redirect
- any UC3 or IAS worker can activate including service owners and managers
- can be applied to any application using an ALB
- can be applied to individual application or in bulk to all eligible UC3 apps

#### How it Works

Upon activation all internet traffic to a public facing web application is
redirected to a static page by adding a fixed-response rule to an AWS
Application Load Balancer (ALB). This new rule is set to priority 1 and
applies a path pattern to capture all connections (`path-pattern: '/*'`).

The redirect is deactivated by simply deleting the injected fixed-response rule.

While the redirect is active client connection attempts are still logged via
WAF and ALB logging.  Messages are indexed into OpenSearch

Currently the fixed-response page directs visitors to the [CDL System Status
page](https://cdlib.org/contact/system-status/).


## Prerequisites

### Application Prerequisites

There are 2 requirements for a UC3 app to participate in emergency-redirect:

1. An application's ALB must not have a Listener Rule set with `priority: 1`.
   This priority is reserved for use by emergency-redirect.
1. Applications must _enrole_ by adding a specific resource tag to the app's ALB.
   ```
   Key: 'emergency-redirect'
   Value: 'eligible'
   ```
   ALBs missing this tag are ignored.  This is a failsafe for bulk activation:

### Execution Prerequisites

This is a cli tool.  The operator must have a shell environment with the following:

- Python 3 environment
- AWS SSO role with permission to describe load balancers, tags, listeners,
  and rules, and to create and delete listener rules:
  - `elasticloadbalancing:DescribeLoadBalancers`
  - `elasticloadbalancing:DescribeTags`
  - `elasticloadbalancing:DescribeListeners`
  - `elasticloadbalancing:DescribeRules`
  - `elasticloadbalancing:CreateRule` 
  - `elasticloadbalancing:DeleteRule`



## Installation

Clone this repo onto your local workstation and install into your python environment with pip:

```sh
> git clone git@github.com:CDLUC3/uc3-ops-emergency-redirect.git
> cd uc3-ops-emergency-redirect/
uc3-ops-emergency-redirect> pip install .
```

The executible `emergency-redirect` should now be in your shell path.


## Usage

`emergency-redirect` has 4 subcommands for activating redirects and querying redirect status.

```sh
agould@linux:~> emergency-redirect --help
Usage: emergency-redirect [OPTIONS] [COMMAND] [ARGS]...

  Implements ALB redirect to static page

Options:
  -d, --debug  Enable debug logging.
  --help       Show this message and exit.

Commands:
  activate    Activate emergency redirect for eligible ALBs
  deactivate  Deactivate emergency redirect for listed ALBs
  list        List name and eligibility status of each active...
  status      Show emergency redirect activation status of ALBs
```

All subcommands have thier own `--help` menu.


### list

List active, internet-facing application load balancers and whether each is
eligible for bulk activation.

```
agould@linux:~> emergency-redirect list --help
Usage: emergency-redirect list [OPTIONS]

  List name and eligibility status of each active internet-facing ALB.

Options:
  --help  Show this message and exit.

agould@linux:~> emergency-redirect list
ALB Name                                 Eligibility 
----------------------------------------------------
dmp-tool-dev-alb-ALB                     -           
mrt-ecs-ephemeral-ELB-ui                 -           
uc3-ops-ecs-dev-alb-ALB                  eligible    
mrt-ecs-dbsnapshot-ELB-ui                -           
mrt-ecs-dbsnapshot-ELB-admin             -           
mrt-ecs-ephemeral-ELB-admin              -           
rams-dev-alb                             -           
mrt-ecs-dev-ELB-admin                    -           
mrt-ecs-dev-ELB-ui                       -           
ezid-n2t-dev-network-ALB                 -           
```

Eligibility is controlled by the load balancer tag `emergency-redirect=eligible`.


### status

Show emergency redirect activation status of ALBs.  By default all
internet-facing ALBs are listed.

```
agould@linux:~> emergency-redirect status --help
Usage: emergency-redirect status [OPTIONS]

  Show emergency redirect activation status of ALBs

Options:
  --alb-name TEXT  Show activation status only for named ALB
  -v, --verbose    Display listener rules for named ALB. Requires "--alb-name"

agould@linux:~> emergency-redirect status 
ALB Name                                 Status      
----------------------------------------------------
dmp-tool-dev-alb-ALB                     -           
mrt-ecs-ephemeral-ELB-ui                 -           
uc3-ops-ecs-dev-alb-ALB                  active           
mrt-ecs-dbsnapshot-ELB-ui                -           
mrt-ecs-dbsnapshot-ELB-admin             -           
mrt-ecs-ephemeral-ELB-admin              -           
rams-dev-alb                             -           
mrt-ecs-dev-ELB-admin                    -           
mrt-ecs-dev-ELB-ui                       -           
ezid-n2t-dev-network-ALB                 -           

```

### activate

Activate the redirect for one load balancer, or for all eligible load balancers.

```
agould@linux:~> emergency-redirect activate --help
Usage: emergency-redirect activate [OPTIONS]

  Activate emergency redirect for eligible ALBs

Options:
  --all-alb        Include all ALBs
  --alb-name TEXT  Name of an ALB in current account

agould@linux:~> emergency-redirect activate --alb-name dmp-tool-dev-alb-ALB
agould@linux:~> emergency-redirect activate --all-alb
```

Activation adds a priority-`1` rule to each listener. The rule matches all
paths (`/*`) and returns the built-in HTML maintenance page with HTTP status
`200`.  Added rules are tagged `emergency-redirect=active`


### deactivate

Deactivate a redirect by load balancer name or in bulk.

```
agould@linux:~> emergency-redirect deactivate --help
Usage: emergency-redirect deactivate [OPTIONS]

  Deactivate emergency redirect for listed ALBs

Options:
  --all-alb        Include all ALBs
  --alb-name TEXT  Name of an ALB in current account

agould@linux:~> emergency-redirect deactivate --alb-name uc3-ops-ecs-dev-alb-ALB
agould@linux:~> emergency-redirect deactivate --all-alb
```

Deactivation deletes priority-`1` rules tagged `emergency_redirect=active`
from the named load balancer's listeners, irregardless of _eligibility_.



## Development

This tool is packaged with [uv](https://docs.astral.sh/uv/guides/package/).  To update 
the python package when making changes, run `uv build` at the root of the project working tree:
```
agould@linux:~/git/github/cdluc3/uc3-ops-emergency-redirect> uv build
Building source distribution...
Building wheel from source distribution...
Successfully built dist/emergency_redirect-0.1.0.tar.gz
Successfully built dist/emergency_redirect-0.1.0-py3-none-any.whl
```

