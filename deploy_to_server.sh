#!/bin/bash
set -e
# Default values
REMOTE_USER="..." #user name on the computing cluster
REMOTE_HOST="export...." # address of the remote host
REMOTE_FOLDER="/work/..."
COPY_DATA_AGAIN=false
LOGIN_NODE="login...." # specification of the login node
USE_OSM=false

# ---- HUGGINGFACE CACHE CONFIG (edit path if needed) ----
HF_HOME_DIR="/work/..."
HF_HUB_CACHE_DIR="${HF_HOME_DIR}/hub"
# --------------------------------------------------------

usage() {
  cat << EOF
Usage: $0 [options]

Options:
  -u USER          Remote user (default: $REMOTE_USER)
  -H HOST          Remote host (default: $REMOTE_HOST)
  -d FOLDER        Remote folder (default: $REMOTE_FOLDER)
  -c [true|false]  Copy data again? (default: $COPY_DATA_AGAIN)
  -l LOGIN_NODE    Login node (default: $LOGIN_NODE)
  -o [true|false]  Use OSM simulation script? (default: $USE_OSM)
  -h               Show this help message and exit

Example:
  $0 -u alice -H cluster.example.com -d /work/alice/project -c false -l login01 -o true
EOF
}

# Parse options
while getopts ":u:H:d:c:l:o:h" opt; do
  case $opt in
    u) REMOTE_USER="$OPTARG" ;;      # remote user
    H) REMOTE_HOST="$OPTARG" ;;      # remote host
    d) REMOTE_FOLDER="$OPTARG" ;;    # destination folder
    c) COPY_DATA_AGAIN="$OPTARG" ;;  # copy data flag
    l) LOGIN_NODE="$OPTARG" ;;       # login node
    o) USE_OSM="$OPTARG" ;;          # switch between scripts
    h) usage; exit 0 ;;              # help
    :) echo "Error: -$OPTARG requires an argument." >&2; usage; exit 1 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 1 ;;
  esac
done

# Determine which script to run
if [ "$USE_OSM" = true ]; then
  SCRIPT_NAME="run_otp_sim.sh"
else
  SCRIPT_NAME="run_sumo_sim.sh"
fi

# Display configuration
cat << EOF
Configuration:
  User:        $REMOTE_USER
  Host:        $REMOTE_HOST
  Folder:      $REMOTE_FOLDER
  Copy data?:  $COPY_DATA_AGAIN
  Login node:  $LOGIN_NODE
  Script:      $SCRIPT_NAME

HF cache config:
  HF_HOME:      $HF_HOME_DIR
  HF_HUB_CACHE: $HF_HUB_CACHE_DIR
EOF

# Ensure the target folder and HF cache dirs exist (via login node)
ssh "${REMOTE_USER}@${LOGIN_NODE}" "mkdir -p '${REMOTE_FOLDER}' '${HF_HOME_DIR}' '${HF_HUB_CACHE_DIR}'"

# (Re-)copy data if requested
if [ "$COPY_DATA_AGAIN" = true ]; then
  scp -r ./data "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_FOLDER}"
fi

# Copy code and script
scp -r ./src                 "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_FOLDER}"
scp -r ./scripts             "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_FOLDER}"
scp    ./setup.py            "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_FOLDER}"
scp    ./requirements.txt    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_FOLDER}"
scp    "${SCRIPT_NAME}"      "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_FOLDER}"

# Submit the job via the login node, exporting only HF vars
ssh "${REMOTE_USER}@${LOGIN_NODE}" << EOF
  cd "${REMOTE_FOLDER}"
  sbatch --export=ALL,HF_HOME='${HF_HOME_DIR}',HF_HUB_CACHE='${HF_HUB_CACHE_DIR}' "${SCRIPT_NAME}"
EOF