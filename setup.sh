#!/bin/bash

set -e -o pipefail -o noclobber -o nounset

! getopt --test > /dev/null
if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
    echo '`getopt --test` failed in this environment.'
    exit 1
fi

OPTIONS=h
LONGOPTS=help,pkg-name:,host:,port:,bin-path:,systemd-path:,py-path:

! PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    exit 2
fi

eval set -- "$PARSED"

### DEFAULTS ###

PKG_NAME="aquaero-exporter"
BIN_PATH="$(pwd -P)/aquaero_exporter/exporter.py"
SYSTEMD_PATH="/usr/lib/systemd/system"
LISTEN_HOST="0.0.0.0"
LISTEN_PORT="2782"

if [[ -d $PYENV_ROOT/versions/$PKG_NAME/bin ]]; then
    PY_PATH="$PYENV_ROOT/versions/$PKG_NAME/bin/python"
else
    PY_PATH="/usr/bin/python"
fi

function print_help () {
# Using a here doc with standard out.
cat <<-END
Usage $0: COMMAND [OPTIONS]

Commands:
systemd-unit          Create and install systemd service file
pacman-build          Copy required files to build a pacman package from local files

Options:
-h    --help            Show this message
      --host            Listen address host (default $LISTEN_HOST)
      --port            Listen address port (default $LISTEN_PORT)
      --pkg-name        Change package name (default $PKG_NAME)
      --bin-path        Path where the script is installed (default $BIN_PATH)
      --systemd-path    Path where systemd units are installed (default $SYSTEMD_PATH)
      --py-path         Path to interpreter (default $PY_PATH)
END
}

while true; do
    case "$1" in
        -h|--help)
            print_help
            exit 0
            ;;
        --host)
            LISTEN_HOST="$2"
            shift 2
            ;;
        --port)
            LISTEN_PORT="$2"
            shift 2
            ;;
        --pkg-name)
            PKG_NAME="$2"
            shift 2
            ;;
        --bin-path)
            BIN_PATH="$2"
            shift 2
            ;;
        --systemd-path)
            SYSTEMD_PATH="$2"
            shift 2
            ;;
        --py-path)
            PY_PATH="$2"
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

if [[ $# -ne 1 ]]; then
    echo "$0: A command is required."
    exit 4
fi

SERVICE_FILE="$SYSTEMD_PATH/$PKG_NAME.service"

case "$1" in
    systemd-unit)
        if [[ ! -f $BIN_PATH ]]; then
            echo "Script not found at $BIN_PATH"
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
# Don't start if we can't find any aquaero devices
ExecStartPre=sh -c "set -o pipefail; lsusb | grep '0c70:f001'"
ExecStart=$PY_PATH $BIN_PATH --host $LISTEN_HOST --port $LISTEN_PORT
Restart=always
NoNewPrivileges=true
ProtectHome=read-only
ProtectSystem=strict

[Install]
WantedBy=multi-user.target
EOF
        ;;
      pacman-build)
        rm -rf ./build
        mkdir -p ./build/src/"$PKG_NAME"
        rsync -a ./ ./build/src/"$PKG_NAME" --exclude build --exclude PKGBUILD
        cp -f ./PKGBUILD ./build/
        cd ./build
        makepkg --noextract
        ;;
      *)
        echo "Unrecognized command: $1"
        print_help
        exit 2
        ;;
esac