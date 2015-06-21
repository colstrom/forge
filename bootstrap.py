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


def ssh_keyscan(host):
    """ Get the SSH host key from a remote server by connecting to it """
    from paramiko import transport
    with transport.Transport(host) as ssh:
        ssh.start_client()
        return ssh.get_remote_server_key()


def ssh_host_key(host, port=22):
    """ Get SSH host key, return string formatted for known_hosts """
    if port != 22:
        host = "{host}:{port}".format(host=host, port=port)
    key = ssh_keyscan(host)
    return "{host} {key_name} {key}".format(
        host=host,
        key_name=key.get_name(),
        key=key.get_base64())


def in_known_hosts(host_key):
    """ Checks if a key is in known_hosts """
    from os import path
    if not path.isfile('/etc/ssh/ssh_known_hosts'):
        return False
    with open('/etc/ssh/ssh_known_hosts', 'r') as known_hosts:
        for entry in known_hosts:
            if host_key in entry:
                return True
    return False


def add_to_known_hosts(host_key):
    """ Appends line to a file """
    if in_known_hosts(host_key):
        return
    with open('/etc/ssh/ssh_known_hosts', 'a') as known_hosts:
        known_hosts.write(host_key + "\n")


def configure_ansible():
    """ Fetches ansible configurations from ForgeBucket """
    download_from_s3('ansible.hosts', '/etc/ansible/hosts')
    download_from_s3('ansible.cfg', '/etc/ansible/ansible.cfg')
    add_to_known_hosts(ssh_host_key('github.com'))
    add_to_known_hosts(ssh_host_key('bitbucket.org'))


def set_permissions(files, mode):
    """ Sets permissions on a list of files """
    from os import chmod
    for filename in files:
        try:
            chmod(filename, mode)
        except OSError:
            pass


def get_credentials():
    """ Fetches credentials needed for private repositories """
    download_from_s3('ssh.ed25519', '/root/.ssh/id_ed25519')
    download_from_s3('ssh.rsa', '/root/.ssh/id_rsa')
    set_permissions(['/root/.ssh/id_ed25519', '/root/.ssh/id_rsa'], 0400)


def self_provision():
    """ Bring it all together and follow your dreams, little server! """
    install_with_pip(['ansible', 'awscli', 'boto'])
    configure_ansible()
    get_credentials()

    for playbook in applicable_playbooks():
        get_dependencies(playbook)
        execute(playbook)

self_provision()
