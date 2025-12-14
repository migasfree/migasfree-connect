#!/bin/bash
set -e

# Configuration
VERSION="1.0"
RELEASE="1"
ARCH="noarch"
PKG_NAME="migasfree-connect"

# Clean
rm -rf dist build
mkdir -p dist build

# --- Build DEB ---
echo "Building DEB packet..."
DEB_STAGE="build/deb_stage"
mkdir -p "$DEB_STAGE/usr/bin"
mkdir -p "$DEB_STAGE/DEBIAN"

# Copy control files
cp -r packaging/deb/DEBIAN/* "$DEB_STAGE/DEBIAN/"

# Copy binary
cp connect/migasfree-connect "$DEB_STAGE/usr/bin/"
chmod 755 "$DEB_STAGE/usr/bin/migasfree-connect"

# Build package
dpkg-deb --build "$DEB_STAGE" "dist/${PKG_NAME}_${VERSION}-${RELEASE}_all.deb"


# --- Build RPM ---
echo "Building RPM packet..."
RPM_ROOT="packaging/rpm"
# Ensure clean rpm build structure in build dir if desired, but for now we use the one in packaging as source
# ideally we should copy to build/rpm to avoid artifacts in packaging/rpm/RPMS etc if we want to be super clean
# checking previous implementation, it used packaging/rpm as root.
# Let's clean up packaging/rpm artifacts if they exist from previous runs to be safe or ignore them.
# The user prompt implies keeping source tree clean.
mkdir -p "$RPM_ROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create source tarball
TAR_NAME="${PKG_NAME}-${VERSION}"
mkdir -p "/tmp/$TAR_NAME/$PKG_NAME"
# Improved copy to flattened structure for tarball if needed, but current structure is fine
cp connect/migasfree-connect "/tmp/$TAR_NAME/$PKG_NAME/"
tar czf "$RPM_ROOT/SOURCES/$TAR_NAME.tar.gz" -C /tmp "$TAR_NAME"
rm -rf "/tmp/$TAR_NAME"

# Build RPM
# Check if rpmbuild exists
if command -v rpmbuild &> /dev/null; then
    rpmbuild --define "_topdir $(pwd)/$RPM_ROOT" -ba "$RPM_ROOT/SPECS/migasfree-connect.spec"
    
    # Move RPMs to dist
    find "$RPM_ROOT/RPMS" -name "*.rpm" -exec cp {} dist/ \;
    find "$RPM_ROOT/SRPMS" -name "*.rpm" -exec cp {} dist/ \;
else
    echo "rpmbuild not found. Skipping RPM build."
fi

echo "Build complete. Packages are in dist/"
