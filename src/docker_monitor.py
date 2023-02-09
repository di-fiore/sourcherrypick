#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run benchmarking workloads to measure the cloud noise. It is then fed to the
BOE as the ε_c parameter. Lightweight, only need to run it every few hours with
a few instances.

As we do not use an actual cloud in this implementation, a value from the
Gaussian distribution with mean 0 and variance 1 is returned.
"""

import logging
import random


log = logging.getLogger('docker_monitor')  # pylint: disable=invalid-name


def get_noise():
    """Get the observed noise from a cloud environment, by emulating well known
    workloads to it.

    In reality, just return a value from the normal distrubution N(0,100). See
    the top of this file for more information.
    """
    noise = random.gauss(mu=0.0, sigma=10.0)
    log.info("Generated noise: %s", noise)
    return noise
###############################################################################
