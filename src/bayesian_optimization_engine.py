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

    def __init__(self, min_cpu, max_cpu, min_ram, max_ram, black_box_function):
        """Initialization function"""
        self.bounds = {
            'cpu': (min_cpu, max_cpu),
            'ram': (min_ram, max_ram)
        }
        self.optimizer = BayesianOptimization(
            f=black_box_function,
            pbounds=self.bounds
        )
    ###########################################################################

    def cost(self, cpu_used, ram_used, total_time):
        """Measure the cost of an execution.
           The noise "epsilon" is also used, to emulate the functions of the
           paper.
        """
        # if for whatever reason the computation didn't succeed,
        # set the cost as infinite
        if total_time < 0:
            return float('inf')

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

    def optimize(self, initialization_points, iterations):
        """Run the optimization loop and return the optimal values.

        Select initialization_points number of points based off random
        exploration, to map out the search space.

        Run iterations number steps of the bayesian optimization.

        Return the best values found.
        """
        self.optimizer.maximize(
            init_points=initialization_points,
            n_iter=iterations
        )

        return self.optimizer.max
    ###########################################################################
###############################################################################
