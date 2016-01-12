# forge

Convention Driven Instance Autonomy

## Description

Forge is designed to facilitate autonomous server configuration. At first boot, a server should execute the bootstrap code, which will in turn:

* Install the tools required for the rest of the code, using pip.
* Determine the purpose of the server, using a handful of APIs.
* Download any playbooks that are applicable to the server.
* Install any Ansible roles those playbooks depend on.
* Apply any playbooks downloaded in this way.

_Forge is only actively tested against Amazon Web Services (AWS)._

## Dependencies

Forge will fulfill its own dependencies, if `pip` is available. If it is not, the following python packages must be available.

* [ansible](https://github.com/ansible/ansible/)
* [awscli](https://aws.amazon.com/cli/)
* [boto](https://boto.readthedocs.org/)

## Compatibility

Forge testing uses the current Long-Term Support release of Ubuntu. However, it should run on any Linux with Python.

**Forge 1.x is not compatible with Python3.** This is resolvable with a minor change which breaks Python 2.x compatibility.

## Requirements

* An S3 bucket to store roles in.
* An IAM Role to apply to autonomous servers, with a [User Policy](https://github.com/colstrom/forge/blob/master/examples/policy.json) granting access to the above bucket.
* (optional) One or more Ansible Roles in the bucket.

## Self-Discovery via Conventions

Forge will attempt to figure out what needs to happen on its own. To do this, Forge relies on conventions enforced by the tools it is typically used with.

* [https://github.com/colstrom/ansible-aws-infrastructure](aws-infrastructure)
* [https://github.com/colstrom/superluminal](superluminal)

These tools are optional, and Forge should be fine as long as you follow similar conventions.

### Supported Resource Tags

Forge understands specific resource tags, and expects an instance to have them.

| Resource Tag  | Description
|---------------|------------
| `Project`     | The project this instance belongs to.
| `Role`        | The purpose of this specific instance, within that project.
| `ForgeBucket` | The name of the S3 bucket Forge should pull from.
| `ForgeRegion` | The region to find `ForgeBucket` in.

If sufficient resource tags are not present, Forge will make reasonable guesses. It assumes security group naming like `your-project-name-role`, and infers implicit tags from this. Environment variables can provide additional data.


### Example

An untagged instance with two security groups named `your-project-name-application` and  `your-project-name-managed`.

* Project will be `your-project-name`.
* ForgeBucket will read `FORGE_BUCKET` from the environment.
* Role will be `['application', 'managed']`, and Forge will configure both.
* ForgeRegion will read `FORGE_REGION` from the environment.

_Resource tags are explicit statements of intent, and discovery stops there. Everything else is a fallback._

## How to Use (Hardcore Mode)

If running arbitrary code from the internet with root privileges and no human oversight excites you, this should do it.

```
curl https://raw.github.com/colstrom/forge/master/bootstrap.py | python
```

## How to Use (Recommended)

For a more reasonable approach, upload ```bootstrap.py``` to somewhere you control.

```
curl https://YOUR_URL_HERE/bootstrap.py | python
```

## License

[MIT](https://tldrlegal.com/license/mit-license)

## Contributors

* [Chris Olstrom](https://colstrom.github.io/) | [e-mail](mailto:chris@olstrom.com) | [Twitter](https://twitter.com/ChrisOlstrom)
