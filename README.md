# AWS SAM Deployer

## Overview

Some common functionality for deploying a SAM application on AWS:

- creating zips for the lambdas (including requirements)
- preparing and deploying a stack
- cleaning up dist folders

Especially handy for small/new projects where a CI/CD setup is still missing.

Tries a functional approach using pymonad (hence the dependency). 
Though far from perfectly implemented, does allow a lot of flexibility in combining/chaining small functions together into larger functionality.

## Usage

Add a python file to the root of your project directory.

```
from awssamdeployer.deploy import create_zips, remove_dists, create_stack, deploy, StackData

# create your lambda zips. optional parameter = source root of the lambdas (default is 'lambdas')
create_zips()
# package and create the stack. StackData takes two more optional parameters: bucket prefix and template name (default is template.yaml)
create_stack(StackData('example-stack-for-deploy', 'bucket-for-uploaded-zips'))
# remove the dists we created. optional parameter = source root of the lambdas
remove_dists()

# or do all at once with:
deploy(StackData('example-stack-for-deploy', 'bucket-for-uploaded-zips'))
```

## Install

`pip3 install git+https://github.com/VanOvermeire/aws-sam-deployer.git`

## Requirements

AWS CLI should be installed and configured.
Because the code runs `zip`, the create_zips() command may not work properly on Windows. 

## Possible TODO's

- tests would be nice
- add common directory to the zips
- save config somewhere and check that location? (like the bucket for example)
