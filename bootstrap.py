#!/usr/bin/env python

# Copyright (c) 2015 Chris Olstrom <chris@olstrom.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from subprocess import call


def install_with_pip(packages):
    """ Installs packages with pip """
    for package in packages:
        call('pip install -U ' + package, shell=True)


def detect(setting):
    """ Detects a setting in tags, falls back to environment variables """
    import os
    if setting in resource_tags():
        return resource_tags()[setting]
    else:
        return os.getenv(shell_style(setting))


def shell_style(name):
    """ Translates reasonable names into names you would expect for environment
    variables. Example: 'ForgeRegion' becomes 'FORGE_REGION' """
    import re
    return re.sub('(?!^)([A-Z]+)', r'_\1', name).upper()


def download_from_s3(source, destination):
    """ Downloads a file from an S3 bucket """
    call("aws s3 cp --region {region} s3://{bucket}/{file} {save_to}".format(
        region=detect('ForgeRegion'),
        bucket=detect('ForgeBucket'),
        file=source,
        save_to=destination
        ), shell=True)


def instance_metadata(item):
    """ Returns information about the current instance from EC2 Instace API """
    import httplib
    api = httplib.HTTPConnection('169.254.169.254')
    api.request('GET', '/latest/meta-data/' + item)
    metadata = api.getresponse().read()
    api.close()
    return metadata


def instance_id():
    """ Returns the ID of the current instance """
    return instance_metadata('instance-id')


def region():
    """ Returns the region the current instance is located in """
    return instance_metadata('placement/availability-zone')[:-1]


def resource_tags():
    """ Returns a dictionary of all resource tags for the current instance """
    import boto.ec2
    api = boto.ec2.connect_to_region(region())
    tags = api.get_all_tags(filters={'resource-id': instance_id()})
    return {tag.name: tag.value for tag in tags}


def security_groups():
    """ Returns a list of sercurity groups for the current instance """
    return instance_metadata('security-groups').split('\n')


def infer_tags(security_group):
    """ Attempts to infer tags from a security group name """
    import re
    matches = re.search(r'(?P<Project>[\w-]+)-(?P<Role>\w+)$', security_group)
    return matches.groupdict()


def implicit_tags():
    """ Returns a list of tags inferred from security groups """
    return [infer_tags(name) for name in security_groups()]


def discover(trait):
    """ Tries to find a trait in tags, makes a reasonable guess if it fails """
    if trait in resource_tags():
        return [resource_tags()[trait]]
    else:
        return [implicit_tags()[trait]]


def project_path():
    """ Returns the forge path for the discovered project """
    return discover('Project')[0] + '/'


def role_paths():
    """ Returns a list of forge paths for all discovered roles """
    return [project_path() + role + '/' for role in discover('Role')]


def unique(enumerable):
    """ Returns a list without duplicate items """
    return list(set(enumerable))


def applicable_playbooks():
    """ Returns a list of playbooks that should be applied to this system """
    playbooks = ['']                  # Base Playbook
    playbooks.append(project_path())  # Project Playbook
    playbooks.extend(role_paths())    # System Roles
    return unique(playbooks)


def temp_path(playbook):
    """ Returns a flattened path under /tmp for a playbook """
    import re
    return '/tmp/' + re.sub('/', '-', playbook)


def get_dependencies(playbook):
    """ Downloads and installs all roles required for a playbook to run """
    path = temp_path(playbook)
    download_from_s3(playbook + 'dependencies.yml', path + 'dependencies.yml')
    call('ansible-galaxy install -ifr' + path + 'dependencies.yml', shell=True)


def execute(playbook):
    """ Downloads and executes a playbook. """
    path = temp_path(playbook)
    download_from_s3(playbook + 'playbook.yml', path + 'playbook.yml')
    call('ansible-playbook ' + path + 'playbook.yml', shell=True)


def self_provision():
    """ Bring it all together and follow your dreams, little server! """
    install_with_pip(['ansible', 'awscli', 'boto'])
    download_from_s3('ansible.hosts', '/etc/ansible/hosts')

    for playbook in applicable_playbooks():
        get_dependencies(playbook)
        execute(playbook)

self_provision()
