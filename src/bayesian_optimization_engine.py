#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Bayesian Optimization implementation.

* Prior function
* Acquisition function
*
"""

import logging

import docker_monitor

from bayes_opt import BayesianOptimization


log = logging.getLogger('bayesian_opt_engine')  # pylint: disable=invalid-name


class BayesianOptimizationEngine:
    """Performs Bayesian optimization on black box computing cost functions."""

    # Arbitrarily, we assume the following costs:
    #    CPU is measured to cost 100 price units per 1 cpu per 1 second
    #    RAM is measured to cost 10 price units per 1 megabyte per 1 second
    COSTS = {
        'CPU': {
            'unit': 1,
            'price': 100
        },
        'RAM': {
            'unit': 1024**2,
            'price': 10
        }
    }

    # TODO: missing functionality:
    #   * compute next parameters
    #   * decide when you meet stop criteria
    def __init__(self):
        """Initialization function"""
        self.iterations = 0
        self.improvements = []
    ###########################################################################

    def cost(self, cpu_used, ram_used, total_time):
        """Measure the cost of an execution.
           The noise "epsilon" is also used, to emulate the functions of the
           paper.
        """
        cpu_epsilon = docker_monitor.get_noise()
        ram_epsilon = docker_monitor.get_noise()

        actual_cpu = int(cpu_used + cpu_used * cpu_epsilon / 100.0)
        actual_ram = int(ram_used + ram_used * ram_epsilon / 100.0)

        effective_cpu = actual_cpu / self.COSTS['CPU']['unit']
        effective_ram = int(actual_ram / self.COSTS['RAM']['unit'])

        cpu_cost = effective_cpu * self.COSTS['CPU']['price']
        ram_cost = effective_ram * self.COSTS['RAM']['price']

        return (cpu_cost + ram_cost) * total_time
    ###########################################################################
###############################################################################
