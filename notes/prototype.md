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
- option to check if emergency redirect is currenlty active
- option to list all ALB in account by name
- option (or syntax) to activate/deactivate on multiple ALB all at once




How is works
------------

operator executes a `emergency-redirect` script which does the following:

- insert a new rule into each active Listener configuration of the application ALB
- this new rule is set to priority 1
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
emergency-redirect.py [-h|--help]                                  # print usage message
emergency-redirect.py list                                         # print list of ALB names in current AWS account
                                                                   #   also shows if a matching message file exists in this project 
emergency-redirect.py status [--all]                               # print list of ALB names along with current ER activation status
emergency-redirect.py status --alb-name <string>                   # print current ER activation status for 'alb-name'
emergency-redirect.py generate --alb-name <string>                 # generate a message-file from template for this ALB and save it to project data.
emergency-redirect.py activate --alb-name <string> [--message-file <string>]  
                                                                   # activate ER for 'alb-name'
                                                                   #   if no 'message-file' is supplied, use pre-defined file in this project matching 'alb-name'
                                                                   #   if no pre-defined file is found, generate a default message-file from template.
emergency-redirect.py activate --all                               # activate ER for all pre-configured ALB in this AWS account
                                                                   #   a pre-configured ALB is one for which a matching message file exists in this project
emergency-redirect.py deactivate [--alb-name <string> | --all]     # deactivate ER for 'alb-name' or for 'all' active ALB in this AWS account
```



Prerequisites
-------------

- Existing listener rules in the application ALB configuration must be set to a priority greater than 1.
