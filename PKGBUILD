# Maintainer: Andrei Costescu <andrei@costescu.no>

# shellcheck shell=bash

pkgname=aquaero-exporter-git
_pkgname="${pkgname%-git}"
pkgver=9879e6b
pkgrel=1
pkgdesc="Prometheus exporter for Aquaero devices"
arch=("any")
url="https://github.com/cosandr/aquaero-exporter"
license=("MIT")
provides=("${_pkgname}" "python-pyquaero")
conflicts=("${_pkgname}" "python-pyquaero")
depends=("python" "python-pyusb" "python-prometheus_client" "python-aiohttp")
source=("git+$url")
md5sums=("SKIP")

pkgver() {
    cd "${_pkgname}"
  ( set -o pipefail
    git describe --long 2>/dev/null | sed 's/\([^-]*-g\)/r\1/;s/-/./g' ||
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
  )
}

build() {
    git clone https://github.com/shred/pyquaero pyquaero
    cd pyquaero
    /usr/bin/python3 setup.py build
    cd "../${_pkgname}"
    /usr/bin/python3 setup.py build
    ./setup.sh systemd-unit \
        --no-check-exec \
        --pkg-name "${_pkgname}" \
        --systemd-path . \
        --exec-cmd "/usr/bin/${_pkgname}"
}

package() {
    cd pyquaero
    /usr/bin/python3 setup.py install --root="$pkgdir" --optimize=1 --skip-build
    cd "../${_pkgname}"
    install -d "${pkgdir}/usr/lib/systemd/system"
    /usr/bin/python3 setup.py install --root="$pkgdir" --optimize=1 --skip-build
    install -m 644 "${_pkgname}.service" "${pkgdir}/usr/lib/systemd/system/"
    install -Dm 644 LICENSE "${pkgdir}/usr/share/licenses/${_pkgname}/LICENSE"
}
