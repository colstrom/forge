# forge

Convention Driven Instance Autonomy

Description
-----------

Forge is designed to facilitate autonomous server configuration. At first boot, a server should execute the bootstrap code, which will in turn:
* Install the tools required for the rest of the code, using pip.
* Determine the purpose of the server, using a handful of APIs.
* Download any playbooks that are applicable to the server, install their dependent roles, and execute them.

_Forge is only actively tested against Amazon Web Services (AWS)._

Dependencies
------------
Forge will fulfill its own dependencies, if ```pip``` is available. If it is not, the following python packages must be available.
* [ansible](https://github.com/ansible/ansible/)
* [awscli](https://aws.amazon.com/cli/)
* [boto](https://boto.readthedocs.org/)

Requirements
------------
* An S3 bucket to store roles in.
* An IAM Role to apply to autonomous servers, with a [User Policy](https://github.com/colstrom/forge/blob/master/examples/policy.json) granting access to the above bucket.
* (optional) One or more Ansible Roles in the bucket.

Self-Discovery via Conventions
------------------------------
Forge will attempt to figure out what needs to happen on its own. To do this, it relies on conventions enforced by the tools it was built to work alongside: ```meta/infrastructure``` and ```superluminal```. If you are not using these tools, Forge should work without hassle as long as you follow similar conventions.

An instance should have resource tags. Among these, we should expect to find:
* ```Project```: The project this instance belongs to.
* ```Role```: The purpose of this specific instance, within that project.
* ```ForgeBucket```: The name of the S3 bucket Forge should pull from.
* ```ForgeRegion```: Which region is ForgeBucket found in?

If sufficient resource tags are not present, Forge will make reasonable guesses. It assumes security groups are named like ```your-project-name-role```, and infers 'implicit tags' from this. Additional data can be provided via environment variables. If the instance has two security groups named ```['your-project-name-application', 'your-project-name-managed']```

* Project will be ```'your-project-name'```
* Role will be ```['application', 'managed']``` and both will be configured.
* ForgeBucket can be provided as ```FORGE_BUCKET``` in the environment.
* ForgeRegion can be provided as ```FORGE_REGION``` in the environment.

Resource tags are considered explicit statements of intent, and discovery stops there. Everything else is a fallback.

How to Use (Hardcore Mode)
--------------------------
If you're cool with allowing arbitrary code from the internet to run with root privileges with no human oversight, you can do this:

```curl https://raw.github.com/colstrom/forge/master/bootstrap.py | python```

How to Use (Recommended)
------------------------
If you'd prefer a more sane approach, upload ```bootstrap.py``` to somewhere you control.

```curl https://YOUR_URL_HERE/bootstrap.py | python```

License
-------
[MIT](https://tldrlegal.com/license/mit-license)

Contributors
------------
* [Chris Olstrom](https://colstrom.github.io/) | [e-mail](mailto:chris@olstrom.com) | [Twitter](https://twitter.com/ChrisOlstrom)
