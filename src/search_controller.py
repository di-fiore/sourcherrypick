#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Orchestrates the container resource configuration selection process. Users
supply a representative workload (udf+data in our case) and its constraints
(budget, max running time, min/max CPU/RAM, etc)). Based on these inputs, the
search controller obtains a list of candidate container configurations and
passes it to the BO engine.

This is the main entrypoint to the application. Sets up the workloads via the
Docker Controller, creates and runs the container and monitors the Bayesian
Optimization Engine to steer and store the result of the search.
"""

import argparse
import logging
import multiprocessing
import os
import random
import sys
import time

import docker

import docker_controller
import bayesian_optimization_engine

log = logging.getLogger('search_controller')

def parse_args(available_memory):
    """Argument parsing function"""

    parser = argparse.ArgumentParser(
        description="Sourcherry cost optimization search."
    )

    parser.add_argument(
        '-c', '--cpu_limit',
        type=float,
        required=True,
        help="The (float) max number of CPUs to give to the container. "
             "Mandatory."
    )
    parser.add_argument(
        '-m', '--memory_limit',
        type=int,
        required=True,
        help="The (int) max bytes of RAM to give to the container. Mandatory."
    )
    parser.add_argument(
        '-t', '--time_limit',
        type=int,
        required=True,
        help="The (int) seconds of max running time to give to the container. "
             "Mandatory."
    )
    parser.add_argument(
        '-s', '--sql_script',
        type=str,
        required=True,
        help="The sql queries script file to run against the database. "
             "Mandatory."
    )
    parser.add_argument(
        '-i', '--iterations',
        type=int,
        required=False,
        default=5,
        help="The number of bayesian optimization steps to perform. The more "
             "steps the more likely to find a good minimum. Optional. Default "
             "value is 5."
    )
    parser.add_argument(
        '-d', '--debug',
        required=False,
        action='store_true',
        default=False,
        help="Enable debug logging. Optional."
    )

    args = parser.parse_args()

    # negative values not allowed
    if any(x<0 for x in [args.cpu_limit, args.time_limit, args.memory_limit]):
        print("Negative parameters not allowed.", file=sys.stderr)
        sys.exit(1)

    # path provided must be valid file
    if not os.path.isfile(args.sql_script):
        print(f"Bad command or file name: {args.sql_script}", file=sys.stderr)
        sys.exit(1)

    # limit CPUs to what we actually have
    max_cpu = multiprocessing.cpu_count()
    if args.cpu_limit > max_cpu:
        print(f"A maximum of {max_cpu} CPUs are allowed.",
              file=sys.stderr)
        sys.exit(1)

    # limit memory to what we actually have minus an arbitrary ~100MB
    if available_memory < 0:
        print("Could not detect available memory. If you ask too much, the "
              "system might hang or the OOM killer engaged.", file=sys.stderr)
    else:
        allowed_memory = available_memory - 100 * 1024**2
        if args.memory_limit > allowed_memory:
            print(f"A maximum of {bytes2human(allowed_memory)} of RAM are "
                  "allowed.", file=sys.stderr)
            sys.exit(1)

    # arbitrary limit of container maximum runtime to one hour
    if args.time_limit > 3600:
        print("A maximum of one hour is allowed for container time limit.",
              file=sys.stderr)
        sys.exit(1)

    # sanity check for iterations
    if not 1 <= args.iterations <= 100:
        print("Iterations must be between 1 and 100", file=sys.stderr)
        sys.exit(1)

    # convert to absolute path, as it is required by docker to be moutned
    args.sql_script = os.path.abspath(args.sql_script)

    return args
###############################################################################


def setup_logging(verbose=False):
    """Setup logging"""
    loglevel = logging.NOTSET
    if verbose is False:
        loglevel = logging.INFO
    elif verbose is True:
        loglevel = logging.DEBUG

    log_fmt = '%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s'
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(loglevel)
    formatter = logging.Formatter(log_fmt)
    stdout_handler.setFormatter(formatter)
    log.addHandler(stdout_handler)
    log.setLevel(loglevel)
###############################################################################


def run_until(condition_function, timeout, *args):
    """Run a function until the condition_functionr returns true or timeout """
    start = time.time()
    while not condition_function(*args) and time.time() - start < timeout:
        time.sleep(0.5)

    if time.time() - start > timeout:
        return False
    return True
###############################################################################


def bytes2human(num):
    """Convert int bytes to human readable format"""
    for unit in ["", "K", "M", "G"]:
        if abs(num) < 1024:
            return f"{num:3.1f}{unit}B"
        num /= 1024.0
    return "\_(o_o)_/ ETOOMUCHRAM \_(o_o)_/"
###############################################################################


def cpuinfo():
    """Get CPU info for the host"""
    if sys.platform == "linux":
        with open('/proc/cpuinfo', encoding='utf-8') as infile:
            for line in infile:
                if line.startswith('model name'):
                    return line.split(':')[1].strip()
    else:
        print(f"Unsupported platform: {sys.platform}. Exiting.",
              file=sys.stderr)
        sys.exit(2)

    return 'not detected'
###############################################################################


def meminfo():
    """Get RAM info for the host"""
    total = -1
    available = -1
    if sys.platform == "linux":
        with open('/proc/meminfo', encoding='utf-8') as infile:
            for line in infile:
                if line.startswith('MemTotal'):
                    total = int(line.split()[1].strip()) * 1024
                elif line.startswith('MemAvailable'):
                    available = int(line.split()[1].strip()) * 1024
    else:
        print(f"Unsupported platform: {sys.platform}. Exiting.",
              file=sys.stderr)
        sys.exit(2)

    if total > 0 and available > 0:
        return (total, available)
    return (-1, -1)
###############################################################################


def run_experiment(controller, cpu, ram, sql_script, max_time):
    """The black box function we want to minimize.

    We give it cpu and ram (our only resources) and it calculates time to run
    to completion.

    Note: return negative, as the underlying library only supports maximization
    (so essentially we do minimization).
    """

    # accomodate for the underlying library using only full float numbers
    cpu = round(cpu, 2)
    ram = int(ram)

    log.info("Attempting to start container")
    container = controller.run_container(
        'sourcherrypick', 'latest',
        int(cpu * 10**9),
        ram,
        sql_script
    )
    log.info("Container started")

    try:
        # run container until completion or time out
        log.info(
            "Running container with CPU limit: %s, RAM limit: %s, SQL script: "
            "%s, until it completes or %s seconds pass.", cpu,
            bytes2human(ram), sql_script, max_time
        )

        start = time.time()

        in_time = run_until(
            controller.not_running,
            max_time,
            container.name
        )


        # return a special, random "too big" value
        # needs to be random, else the BO process cannot properly explore the
        # search space
        if not in_time:
            total_time = (max_time + random.randint(0,1000)) * -2

            try:
                container.kill()
            except docker.errors.APIError as exc:
                log.error("Couldn't kill container %s due to %s. Please "
                          "manually verify if it is still running after "
                          "execution completes.", container.name, exc)
            log.warning("Execution timed out")
        else:
            exit_code = controller.container_exit_code(container.name)
            if exit_code == 0:
                total_time = time.time() - start
                log.info("Container execution finished on time")
            else:
                # return a special, random "too big" value
                # needs to be random, else the BO process cannot properly
                # explore the search space
                total_time = (max_time + random.randint(0,1000)) * -2
                log.info("Container execution finished unsuccessfully")

        log.info("Execution logs follow\n")
        logs = container.logs(timestamps=True)
        for item in logs.decode('utf-8').split('\n'):
            print(f"    {item}")
    finally:
        log.info("Performing pre-exit cleanup")
        if controller.still_running(container.name):
            container.stop()
        container.remove()
        log.info("Pre-exit cleanup completed")

    if total_time < 0:
        return total_time
    return total_time * -1
###############################################################################


def main():
    """main function"""
    cpu_info = cpuinfo()
    total_ram, available_ram = meminfo()

    args = parse_args(available_ram)
    setup_logging(args.debug)

    log.info("Initializing...")
    log.info("Detected CPU: %s", cpu_info)
    log.info("Total / Available Memory: %s / %s", bytes2human(total_ram),
             bytes2human(available_ram))

    vm_controller = docker_controller.DockerController()
    log.info("Connection to docker daemon established")

    bayes_optimizer = bayesian_optimization_engine.BayesianOptimizationEngine(
        min_cpu=min(args.cpu_limit, 0.1),             # 10 percent of one cpu
        max_cpu=args.cpu_limit,
        min_ram=min(args.memory_limit, 60*10**6),     # 60 MB of RAM
        max_ram=args.memory_limit,
        black_box_function = lambda cpu, ram: run_experiment(
            vm_controller, cpu, ram,args.sql_script, args.time_limit)
    )

    log.info("Starting bayes optimization")
    start = time.time()

    bayes_optimizer.optimize(
        initialization_points=3,    # same value as the paper (using the same kernel function, Matern)
        iterations=args.iterations
    )

    log.info("Finished bayes optimization after %s secs", time.time() - start)
    log.info("Best values: CPU: %.2f RAM: %s execution time: %.2f cost: %.3f",
        bayes_optimizer.optimizer.max['params']['cpu'],
        bytes2human(int(bayes_optimizer.optimizer.max['params']['ram'])),
        bayes_optimizer.optimizer.max['target']*-1,
        bayes_optimizer.cost(bayes_optimizer.optimizer.max['params']['cpu'],
        bayes_optimizer.optimizer.max['params']['ram'],
        bayes_optimizer.optimizer.max['target']*-1
    ))
    if bayes_optimizer.optimizer.max['target'] <= args.time_limit*-2:
        log.warning("No valid parameters found due to the given constraints.")

    log.info("Full bayesian optimization log:")
    for i, item in enumerate(bayes_optimizer.optimizer.res):
        log.info("Iteration %s: cpu %.2f ram %s  exec time: %.2f", i,
            item['params']['cpu'],
            bytes2human(int(item['params']['ram'])),
            item['target']*-1)

    log.info("Exiting successfully")
###############################################################################


if __name__ == "__main__":
    main()
