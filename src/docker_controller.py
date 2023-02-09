#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An adaptation layer that handles the container control. Provides A uniform API
for the other components of the architecture to use for operations such as:
    1. create/delete VM
    2. create/delete virtual network
    3. capture image from VM
    4. list available instance types

Also implements direct communication to the containers via the docker native
library, for facilitating the control of the running workloads.
"""

import logging

import docker

log = logging.getLogger('docker_controller')  # pylint: disable=invalid-name



class DockerController:
    """Controls docker containers and images"""
    def __init__(self, docker_server=None):
        """Initialization function"""
        if docker_server:
            self.client = docker.DockerClient(base_url=docker_server)
        else:
            self.client = docker.from_env()
    ###########################################################################

    def run_container(self, name, version, cpu_limit, memory_limit,
                      sql_script):
        """run a container"""
        return self.client.containers.run(
            f'{name}:{version}',
            mem_limit=memory_limit,
            nano_cpus=cpu_limit,
            volumes= {
                sql_script: {
                    'bind': '/test_script.sql',
                    'mode': 'ro'
                }
            },
            detach=True,
            stdout=True,
            stderr=True
        )
        # nano_cpus=2 * 10**9 for 2 CPUs
    ###########################################################################

    def still_running(self, name):
        """check if a container is still running"""
        container = self.client.containers.get(name)
        return container.status.upper() == 'RUNNING'
    ###########################################################################

    def not_running(self, name):
        """check if a container is still running"""
        return not self.still_running(name)
    ###########################################################################

    def container_exit_code(self, name):
        """check if a container exited successfully"""
        if self.still_running(name):
            return None

        container = self.client.containers.get(name)
        result = container.wait()
        print(result)
        return result['StatusCode']
    ###########################################################################
###############################################################################
