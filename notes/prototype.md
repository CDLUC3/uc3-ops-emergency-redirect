Prototype Notes for an Emergency Redirect Tool
==============================================

11/3/2026


Requirements
------------
- upon activation all internet traffic to an ALB is redirected to a static page
- simple mechnism to activate/deactivate emergency redirect
- can be applied to any application using an ALB
- any UC3 or IAS worker can activate including service owners and managers



Wish list
---------
- operators can still access applications and resources while emergency redirect is active
- waf and alb logs continue to be indexed into opensearch
- option to select specific listeners




How is works
------------

operator executes a `emergency-redirect` script which does the following:

- insert a new rule into each active Listener configuration of the application ALB
- this new rule is set to priority 0
- the action type of this rule is `fixed-response`
    https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-action-types.html#fixed-response-actions
- the fixed-response text is obtained from a local html file


to deactivate the operator runs `emergency-redirect` script with `--deactivate` flag:

- locate each listener rule inserted by a previous execution of `emergency-redirect` script
- delete each inserted rule



Script syntax
-------------

assuming python for now

```
emergency-redirect.py --alb-name <string> --message-file <string>
emergency-redirect.py --alb-name <string> --deactivate
```



Prerequisites
-------------

- Existing listener rules in the application ALB configuration must be set to a priority greater than 0.
