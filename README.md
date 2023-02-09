# Sourcherrypick : A Cherrypick Re-Implementation

This is an implementation of the architecture described in [CherryPick: Adaptively Unearthing the Best Cloud Configurations for Big Data Analytics](https://www.usenix.org/conference/nsdi17/technical-sessions/presentation/alipourfard)

## Description

TBD

## Getting Started

### Dependencies

* Docker runtime and python client library
```sh
apt-get install docker
pip3 install docker
```

* [Bayesian Optimization](https://github.com/fmfn/BayesianOptimization) python package
```sh
pip3 install bayesian-optimization
```

### Installing

* Build the docker image:
```sh
make build
```

* Remove the docker image:
```sh
make demolish
```

### Executing Tests

* The tests can be executed via the makefile as well:
```sh
make test
```

## Help

* See help about the makefile and the available targets:
```sh
make help
```

## Authors

Dimosthenes Fioretos
[Contact](cs2210027@di.uoa.gr)

## Version History

* 0.1
    * Initial Release

## License

This project is licensed under the [GPLv3] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [CherryPick: Adaptively Unearthing the Best Cloud Configurations for Big Data Analytics](https://www.usenix.org/conference/nsdi17/technical-sessions/presentation/alipourfard)
* [YeSQL](https://github.com/athenarc/YeSQL)
