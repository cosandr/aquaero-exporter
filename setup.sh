#!/bin/bash

set -e -o pipefail -o noclobber -o nounset

! getopt --test > /dev/null
if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
    echo '`getopt --test` failed in this environment.'
    exit 1
fi

OPTIONS=h
LONGOPTS=help,no-check-exec,pkg-name:,listen-address:,systemd-path:,exec-cmd:

! PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    exit 2
fi

eval set -- "$PARSED"

### DEFAULTS ###

BIN_PATH="$(pwd -P)/aquaero_exporter/exporter.py"
DEVICE_ID="0c70:f001"
EXTRA_ARGS=""
LISTEN_ADDRESS="0.0.0.0:2782"
PKG_NAME="aquaero-exporter"
SYSTEMD_PATH="/usr/lib/systemd/system"
CHECK_EXEC=1

set +e
if command -v pyenv > /dev/null 2>&1; then
    EXEC_CMD="$(pyenv which $PKG_NAME 2>&1)"
    if [[ $? -ne 0 ]]; then
        EXEC_CMD="$(pyenv which python3) $BIN_PATH"
    fi
else
    EXEC_CMD="/usr/bin/env python3 $BIN_PATH"
fi
set -e

function print_help () {
# Using a here doc with standard out.
cat <<-END
Usage $0: COMMAND [OPTIONS] -- [EXTRA ARGS]

Commands:
pacman-build          Copy required files to build a pacman package from local files
systemd-unit          Create and install systemd service file

Options:
-h    --help            Show this message
      --no-check-exec   Don't check whether exec exists or not
      --exec-cmd        Override systemd exec (default $EXEC_CMD)
      --listen-address  Listen address (default $LISTEN_ADDRESS)
      --pkg-name        Change package name (default $PKG_NAME)
      --quadro          Use Quadro device
      --systemd-path    Path where systemd units are installed (default $SYSTEMD_PATH)
END
}

while true; do
    case "$1" in
        -h|--help)
            print_help
            exit 0
            ;;
        --no-check-exec)
            CHECK_EXEC=0
            shift
            ;;
        --exec-cmd)
            EXEC_CMD="$2"
            shift 2
            ;;
        --listen-address)
            LISTEN_ADDRESS="$2"
            shift 2
            ;;
        --pkg-name)
            PKG_NAME="$2"
            shift 2
            ;;
        --quadro)
            DEVICE_ID="0c70:f00d"
            EXTRA_ARGS="--quadro"
            shift
            ;;
        --systemd-path)
            SYSTEMD_PATH="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Programming error"
            exit 3
            ;;
    esac
done


if [[ $# -lt 1 ]]; then
    echo "$0: A command is required."
    exit 4
fi

CMD="$1"
EXTRA_ARGS+=" ${*:2}"

SERVICE_FILE="$SYSTEMD_PATH/$PKG_NAME.service"

case "$CMD" in
      pacman-build)
        rm -rf ./build
        mkdir -p ./build/src/"$PKG_NAME"
        rsync -a ./ ./build/src/"$PKG_NAME" --exclude build --exclude PKGBUILD
        cp -f ./PKGBUILD ./build/
        cd ./build
        makepkg --noextract
        ;;
    systemd-unit)
        if [[ $CHECK_EXEC -eq 1 ]] && ! eval "$EXEC_CMD" --help > /dev/null; then
            echo "Cannot run $EXEC_CMD"
            exit 1
        fi
        echo -e "\n########## Systemd service ##########\n"
        cat <<EOF | tee "$SERVICE_FILE"
[Unit]
Description=$PKG_NAME service
Requires=network-online.target
After=network-online.target

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
# Don't start if we can't find any aquaero devices
ExecStartPre=lsusb -d $DEVICE_ID
ExecStart=$EXEC_CMD --listen-address $LISTEN_ADDRESS $EXTRA_ARGS
Restart=always
NoNewPrivileges=true
ProtectHome=read-only
ProtectSystem=full

[Install]
WantedBy=multi-user.target
EOF
        ;;
      *)
        echo "Unrecognized command: $1"
        print_help
        exit 2
        ;;
esac
