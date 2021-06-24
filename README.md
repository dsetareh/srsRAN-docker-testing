# srsRAN-docker-testing

Script for executing tests upon a srsRAN environment in docker.

[Current srsRAN Build Commit](https://github.com/dsetareh/srsRAN/tree/91557b14c25a3d6ae819175149237c8c00061c62)

[Old Repository](https://github.com/dsetareh/srsRAN-docker-emulated)
## commands

### start and stop containers
`./fuzztest_helper.py fuzz <start index> <end index> <(optional)docker-compose directory>`

### generate docker-composes
`./fuzztest_helper.py generate <start index> <end index> <template file> <output dir>`

### start containers
`./fuzztest_helper.py start <start index> <end index> <(optional)docker-compose directory>`

### stop containers
`./fuzztest_helper.py stop <start index> <end index> <(optional)docker-compose directory>`
