# UC3 Emergency Redirect

A command-line tool for temporarily replacing application responses with a static maintenance page by adding a fixed-response rule to an AWS Application Load Balancer (ALB). The page directs visitors to the [CDL System Status page](https://cdlib.org/contact/system-status/).

## Requirements

- Python 3
- AWS credentials and a default AWS region configured for [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
- An AWS identity with permission to describe load balancers, tags, listeners, and rules, and to create and delete listener rules (`elasticloadbalancing:DescribeLoadBalancers`, `DescribeTags`, `DescribeListeners`, `DescribeRules`, `CreateRule`, and `DeleteRule`)
- Existing listener rules must leave priority `1` available for the emergency redirect

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

- Activation adds a priority-`1` rule to each listener. The rule matches all paths (`/*`) and returns the built-in HTML maintenance page with HTTP status `200`.
- If a listener already has a priority-`1` rule, the tool does not add another rule to that listener.
- Deactivation deletes priority-`1` rules tagged `emergency_redirect=active` from the named load balancer's listeners. Other priority-`1` rules are left alone.
- Review the target load balancer and its listener rules before activation. Ensure priority `1` is reserved for this tool and that the configured AWS credentials target the intended account and region.

The `status --all-alb` option checks all active, internet-facing application load balancers, whether or not they have the eligibility tag.