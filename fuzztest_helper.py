import yaml, sys, subprocess, time
from pathlib import Path

# fuzztest_helper.py
#
# Generates and executes fuzztesting on srsran docker containers
#
# run without arguments to see options

CONTAINER_ACTION_STEP = 4  # ! max number of containers started at once

COMPOSE_DIRECTORY = "compose/"

# colored text stuff
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def mass_generate_compose(startNum, endNum, templateFilename, outputDir):
    """generates composes from [startNum - endNum]

    Args:
        startNum (int): start val for range
        endNum (int): end val for range
    """
    for test in range(startNum, endNum + 1):
        generate_compose(templateFilename, outputDir, test)
    print()


def generate_compose(templateFilename, outputDir, testNumber):
    """generates and writes to file a docker-compose for fuzz testing from template

    Args:
        templateFilename (str): template file for docker-compose generation
        outputDir (str): output directory for docker-compose outputs
        testNumber (int): current test number
    """
    with open(templateFilename, 'r') as ymlfile:
        try:
            docker_config = yaml.safe_load(ymlfile)
        except yaml.YAMLError as exc:
            print(exc)

    test_number = str(testNumber)  # ! current test iteration

    subnet = generate_subnet_string(testNumber)  # ! this iterations subnet

    # NOTE: using 3 and 5 as we have space for 14 addrs in our subnet, also it wasnt working with 1 and 2
    epc_ip = generate_ip(testNumber, 3)  # ! 'ip 1'
    enb_ip = generate_ip(testNumber, 5)  # ! 'ip 2'

    output_folder = Path(outputDir)
    output_filename = output_folder / ("docker-compose_" + test_number +
                                       ".yml")

    docker_config['services']['srsue'][
        'command'] = 'stdbuf -oL srsue /etc/srsran/ue.conf.fauxrf -f' + test_number

    docker_config['services']['srsepc'][
        'command'] = 'stdbuf -oL srsepc /etc/srsran/epc.conf --mme.mme_bind_addr=' + epc_ip + ' --spgw.gtpu_bind_addr=' + epc_ip

    docker_config['services']['srsepc']['networks']['corenet'][
        'ipv4_address'] = epc_ip

    docker_config['services']['srsenb'][
        'command'] = 'srsenb /etc/srsran/enb.conf.fauxrf --enb.mme_addr=' + epc_ip + ' --enb.gtp_bind_addr=' + enb_ip + ' --enb.s1c_bind_addr=' + enb_ip

    docker_config['services']['srsenb']['volumes'][
        0] = './pcaps/' + test_number + ':/pcaps/'

    docker_config['services']['srsenb']['networks']['corenet'][
        'ipv4_address'] = enb_ip

    docker_config['networks']['corenet']['ipam']['config'][0][
        'subnet'] = subnet

    # container_name
    docker_config['services']['srsepc'][
        'container_name'] = 'virtual-srsepc' + test_number
    docker_config['services']['srsenb'][
        'container_name'] = 'virtual-srsenb' + test_number
    docker_config['services']['srsue'][
        'container_name'] = 'virtual-srsue' + test_number

    with open(output_filename, 'w') as newconf:
        yaml.dump(docker_config, newconf, default_flow_style=False)

    print("Generated Test# " + f"{testNumber:07d}" + " | Subnet: " + subnet,
          end='\r')


def generate_subnet_string(iterationNum):
    """
    when given current iteration, generate a subnet range.
    each subnet is comprised of a /28 block, thus the last
    4 bits of the ip address are available, along with
    10.***.*** ranges, so 20 bits are available to us,
    and about 1mil subnets can be created

     Parameters:
        iterationNum (int): Current Test Number

    Returns:
        subnet_string (str): /28 subnet for current iteration
    """

    first = str(iterationNum >> 12)  # first 8 bits [0-7]
    second = str((iterationNum & 4080) >> 4)  # middle 8 bits [8 - 15]
    third = str(
        16 * (iterationNum & 15)
    )  # final 4 bits, multiplied by 16 to obtein this iterations subnet
    if iterationNum > 1048575:  # 20 bit max val
        print(
            "generate_subnet_string doesnt support more than 1mil iterations")
        quit(1)

    return "10." + first + "." + second + "." + third + "/28"


def generate_ip(iterationNum, ipNum):
    """
        generate a valid ip within this current iteration's
        subnet. /28 blocks allow for 15 ips maximum, thus ipNum
        cannot be above 15


     Parameters:
        iterationNum (int): Current Test Number
        ipNum (int): ip needed within block, valid values are 1 thru 15

    Returns:
        ip_address (str): ip within iterations subnet
    """

    if ipNum > 16:
        print("ipNum too large for a /28 subnet!")
        quit(1)
    first = str(iterationNum >> 12)  # first 8 bits [0-7]
    second = str((iterationNum & 4080) >> 4)  # middle 8 bits [8 - 15]
    # final 4 bits, multiplied by 16 to obtein this iterations subnet,
    # then added to ipNum to obtain a unique ip
    third = str((16 * (iterationNum & 15)) + ipNum)

    return "10." + first + "." + second + "." + third


def print_guide():
    """prints usage instructions and exits script
    """
    print("\nSupported commands:\n")
    print(
        f"     [Main Function] Automatically start and stop containers per fuzzing spec:"
    )
    print(
        f"          ./fuzztest_helper.py {bcolors.HEADER}fuzz{bcolors.ENDC} <start index> <end index> <(optional)docker-compose directory>\n"  # len(args) = 5
    )
    print("     Generate docker-compose files:")
    print(
        f"          ./fuzztest_helper.py {bcolors.HEADER}generate{bcolors.ENDC} <start index> <end index> <template file> <output dir>\n"  # len(args) = 6
    )
    print("     Start containers from generated compose files:")
    print(
        f"          ./fuzztest_helper.py {bcolors.HEADER}start{bcolors.ENDC} <start index> <end index> <(optional)docker-compose directory>\n"  # len(args) = 5
    )
    print("     Stop containers from generated compose files, generate logs:")
    print(
        f"          ./fuzztest_helper.py {bcolors.HEADER}stop{bcolors.ENDC} <start index> <end index> <(optional)docker-compose directory>\n"  # len(args) = 5
    )
    quit(1)


def start_and_stop_containers(startNum, endNum):
    for groupIdx, groupStartIdx in enumerate(
            range(startNum, endNum + 1, CONTAINER_ACTION_STEP)):
        print(f"{bcolors.HEADER} Fuzzing Group " + str(groupIdx + 1) +
              f"{bcolors.ENDC}")
        print("!! Starting Group" + str(groupIdx) + " [" +
              str(groupStartIdx) + ":" +
              str(min((groupStartIdx + 1 + CONTAINER_ACTION_STEP), endNum)) +
              "] !!")
        start_test_containers(
            groupStartIdx, min(endNum, groupStartIdx + CONTAINER_ACTION_STEP))
        print("!! Stopping container group" + str(groupIdx) + " [" +
              str(groupStartIdx) + ":" +
              str(min((groupStartIdx + 1 + CONTAINER_ACTION_STEP), endNum)) +
              "] !!")
        stop_test_containers(
            groupStartIdx, min(endNum, groupStartIdx + CONTAINER_ACTION_STEP))
        print(f"{bcolors.HEADER} Fuzz Group " + str(groupIdx) +
              f" Complete, starting next group in 2 seconds {bcolors.ENDC}")
        time.sleep(2)


def start_test_containers(startNum, endNum):
    """starts containers in range specified, in groups of CONTAINER_ACTION_STEP (currently 5)

    Args:
        startNum (int): start index
        endNum (int): end index

    Returns:
        [subprocess.Popen]: array of handles for started processes
    """
    popenObjs = []
    for groupIdx in range(startNum, endNum + 1, CONTAINER_ACTION_STEP):
        for currIterNum in range(groupIdx, groupIdx + CONTAINER_ACTION_STEP):
            if currIterNum <= endNum:
                popenObjs.append(start_container(currIterNum))

    return popenObjs


def stop_test_containers(startNum, endNum, ignoreCompletion=False):
    """stops containers in range specified and saves logs, in groups of CONTAINER_ACTION_STEP (currently 5)

    Args:
        startNum (int): start index
        endNum (int): end index
        ignoreCompletion (boolean, optional, default=False): if True, stops containers without checking whether they've completed their task
    """
    for groupIdx in range(startNum, endNum + 1, CONTAINER_ACTION_STEP):
        for currIterNum in range(groupIdx, groupIdx + CONTAINER_ACTION_STEP):
            if currIterNum <= endNum:
                stop_container(currIterNum, ignoreCompletion)


def stop_container(contNum, ignoreCompletion=False):
    """stops a single container

    Args:
        contNum (int): container # to stop
        ignoreCompletion (boolean, optional, default=False): if True, stops containers without checking whether they've completed their task

    """
    numSecWaited = 0
    while not (check_test_completion(contNum) or ignoreCompletion):
        numSecWaited += 1
        print(f"{bcolors.WARNING}Waiting " + str(numSecWaited) +
              "s for test completion on container " + str(contNum) +
              F"{bcolors.ENDC}",
              end='\r')
        time.sleep(1)
    print()
    print("closing container" + str(contNum))
    subprocess.call([
        'docker-compose', '-p', 'srsRAN_' + str(contNum), '-f',
        f'{COMPOSE_DIRECTORY}docker-compose_' + str(contNum) + '.yml', 'down',
        '-v'
    ],
                    stdin=None,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True)
    print("requested to close container " + str(contNum))


def start_container(contNum):
    """starts a single container

    Args:
        contNum (int): container # to start

    Returns:
        [subprocess.Popen]: handle for started process
    """
    print("requested to start container " + str(contNum))
    handle = subprocess.Popen([
        'docker-compose', '-p', 'srsRAN_' + str(contNum), '-f',
        f'{COMPOSE_DIRECTORY}docker-compose_' + str(contNum) + '.yml', 'up',
        '-d'
    ],
                              stdin=None,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,
                              close_fds=True)
    return handle


def save_logs(contNum):
    """save docker-compose logs for container to file

    Args:
        contNum (int): container #
    """
    print("saving logs for container " + str(contNum))
    with open("tests/" + str(contNum) + ".txt", "w") as text_file:
        text_file.write(get_logs(contNum))


def check_test_completion(contNum):
    """check if RRCCONNECTIONREQUEST has occured in container

    Args:
        contNum (int): container #

    Returns:
        [boolean]: True if connected, False if not
    """
    logs = get_logs(contNum)
    return "Network attach successful." in logs


def get_logs(contNum):
    """returns logs from container group

    Args:
        contNum (int): container #

    Returns:
        [str]: logs from docker-compose
    """
    logs = subprocess.run([
        'docker-compose', '-p', 'srsRAN_' + str(contNum), '-f',
        f'{COMPOSE_DIRECTORY}docker-compose_' + str(contNum) + '.yml', 'logs',
        '--no-color'
    ],
                          stdout=subprocess.PIPE).stdout.decode('utf-8')
    return logs


def range_check_helper_functions(startNum, endNum):
    """When using start container helper function, check if range is large and exit if it is

    Args:
        startNum (int): start index
        endNum (int): end index
    """
    if 1 + endNum - startNum > CONTAINER_ACTION_STEP:
        print("range too large, try fuzz instead of start")
        quit(1)


if __name__ == "__main__":

    if len(sys.argv) < 4:
        print_guide()
    if len(sys.argv) == 5 and (sys.argv[1] == "start" or sys.argv[1] == "stop"
                               or sys.argv[1] == "fuzz"
                               or sys.argv[1] == "stopforce"):
        print(f"{bcolors.FAIL}COMPOSE DIRECTORY SET: " + sys.argv[4] +
              f"{bcolors.ENDC}")
        COMPOSE_DIRECTORY = sys.argv[4]

    if sys.argv[1] == "generate":
        mass_generate_compose(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4],
                              sys.argv[5])
        print(f"{bcolors.OKGREEN}Generated docker-composes [" + sys.argv[2] +
              ":" + str(int(sys.argv[3])) + f"].{bcolors.ENDC}")
        quit(0)

    if sys.argv[1] == "start":
        print("Starting tests [" + sys.argv[2] + ":" + str(int(sys.argv[3])) +
              "].")
        range_check_helper_functions(int(sys.argv[2]), int(sys.argv[3]))
        start_test_containers(int(sys.argv[2]), int(sys.argv[3]))
        print(f"{bcolors.OKGREEN}Containers [" + sys.argv[2] + ":" +
              str(int(sys.argv[3])) + f"] Started.{bcolors.ENDC}")
        quit(0)

    if sys.argv[1] == "stop":
        print("Stopping tests [" + sys.argv[2] + ":" + str(int(sys.argv[3])) +
              "].")
        stop_test_containers(int(sys.argv[2]), int(sys.argv[3]))
        print(f"{bcolors.OKGREEN}Containers [" + sys.argv[2] + ":" +
              str(int(sys.argv[3])) + f"] Stopped.{bcolors.ENDC}")
        quit(0)

    if sys.argv[1] == "stopforce":
        print("FORCE STOPPING tests [" + sys.argv[2] + ":" + str(int(sys.argv[3])) +
              "].")
        stop_test_containers(int(sys.argv[2]), int(sys.argv[3]), True)
        print(f"{bcolors.OKGREEN}Containers [" + sys.argv[2] + ":" +
              str(int(sys.argv[3])) + f"] FORCE Stopped.{bcolors.ENDC}")
        quit(0)

    if sys.argv[1] == "fuzz":
        print("Running full fuzz tests on [" + sys.argv[2] + ":" +
              str(int(sys.argv[3])) + "].")
        start_and_stop_containers(int(sys.argv[2]), int(sys.argv[3]))
        print(f"{bcolors.OKGREEN}Testing [" + sys.argv[2] + ":" +
              str(int(sys.argv[3])) + f"] Complete.{bcolors.ENDC}")
        quit(0)

    print_guide()
