# srsRAN-docker-testing

Executes simultaneous fuzzing tests on srsRAN within docker containers

## quick start

```
# clone repo to current dir
git clone https://github.com/dsetareh/srsRAN-docker-testing ./

# build and tag container
docker build -t srsran-fuzz-testing:latest ./

# generate [1:1000] docker-compose files in ./
python3 ./fuzztest_helper.py generate 1 1000 ./docker-compose-template.yml ./ 

# start testing containers [1:1000]
python3 ./fuzztest_helper.py generate 1 1000 ./docker-compose-template.yml ./ 

```

#### Output Directories:
- `logs/` stdout logs from each container group

- `pcaps/` enb pcap files from each container group
## Commands
```
$ python3 ./fuzztest_helper.py 

Supported commands:

     [Main Function] Automatically start and stop containers per fuzzing spec:
          ./fuzztest_helper.py fuzz <start index> <end index> <(optional)docker-compose directory>

     Generate docker-compose files:
          ./fuzztest_helper.py generate <start index> <end index> <template file> <output dir>

     Start containers from generated compose files:
          ./fuzztest_helper.py start <start index> <end index> <(optional)docker-compose directory>

     Stop containers from generated compose files, generate logs:
          ./fuzztest_helper.py stop <start index> <end index> <(optional)docker-compose directory>
```

## Links

[Current srsRAN Build Commit](https://github.com/dsetareh/srsRAN/tree/91557b14c25a3d6ae819175149237c8c00061c62)

[Old Forked Repository](https://github.com/dsetareh/srsRAN-docker-emulated)
