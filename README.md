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
- can be applied to individual application or in bulk to all UC3 apps

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
1. Applications must __enroll__ by adding a specific resource tag to the app's ALB.
   ALBs missing this tag are ignored.  This is a failsafe for bulk activation:
   ```
   Key: 'emergency-redirect'
   Value: 'eligible'
   ```

### Execution Prerequisites

This is a cli tool.  The operator must have a shell environnment with the following:

- Python 3 environment
- AWS SSO role with permission to describe load balancers, tags, listeners,
  and rules, and to create and delete listener rules:
  - `elasticloadbalancing:DescribeLoadBalancers`
  - `DescribeTags`
  - `DescribeListeners`
  - `DescribeRules`
  - `CreateRule` 
  - `DeleteRule`



## Installation

Install the Python dependencies:

```sh
python3 -m pip install boto3 PyYAML click
```

## Usage

Run the script from the repository root:

```sh
python3 bin/emergency-redirect.py --help
```

List active, internet-facing application load balancers and whether each is eligible for bulk activation:

```sh
python3 bin/emergency-redirect.py list
```

Eligibility is controlled by the load balancer tag `emergency_redirect=eligible`.

Check redirect status for all active, internet-facing application load balancers or for one named load balancer:

```sh
python3 bin/emergency-redirect.py status --all-alb
python3 bin/emergency-redirect.py status --alb-name my-load-balancer
```

Activate the redirect for one load balancer, or for all eligible load balancers:

```sh
python3 bin/emergency-redirect.py activate --alb-name my-load-balancer
python3 bin/emergency-redirect.py activate --all
```

Activation by name does not require the eligibility tag. Bulk activation only applies to load balancers tagged as eligible.

Deactivate a redirect by load balancer name:

```sh
python3 bin/emergency-redirect.py deactivate --alb-name my-load-balancer
```

Add `--verbose` before the subcommand to enable debug logging, for example:

```sh
python3 bin/emergency-redirect.py --verbose status --alb-name my-load-balancer
```

## Behavior and operational notes

- Activation adds a priority-`1` rule to each listener. The rule matches all
  paths (`/*`) and returns the built-in HTML maintenance page with HTTP status
  `200`.
- If a listener already has a priority-`1` rule, the tool does not add another
  rule to that listener.
- Deactivation deletes priority-`1` rules tagged `emergency_redirect=active`
  from the named load balancer's listeners. Other priority-`1` rules are left
  alone.
- Review the target load balancer and its listener rules before activation.
  Ensure priority `1` is reserved for this tool and that the configured AWS
  credentials target the intended account and region.

The `status --all-alb` option checks all active, internet-facing application
load balancers, whether or not they have the eligibility tag.
