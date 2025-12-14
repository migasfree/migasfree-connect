#!/bin/bash
set -e

PROJECT_ROOT=$(pwd)
VERSION=${1:-"1.0.0"}
# Strip 'v' prefix if present (e.g. v1.0.0 -> 1.0.0)
VERSION=${VERSION#v}
DEB_DIR="packaging/deb"
RPM_DIR="packaging/rpm"
DIST_DIR="dist"

echo "Building version $VERSION..."
mkdir -p $DIST_DIR

# Update Debian Control File Version
sed -i "s/^Version: .*/Version: $VERSION/" $DEB_DIR/DEBIAN/control

# --- BUILD DEB ---
echo "--- Building DEB Package ---"
# Copy files to structure
mkdir -p $DEB_DIR/usr/bin
cp connect/migasfree-connect $DEB_DIR/usr/bin/migasfree-connect
chmod 755 $DEB_DIR/usr/bin/migasfree-connect

# Build
dpkg-deb --build $DEB_DIR $DIST_DIR

# --- BUILD RPM ---
echo "--- Building RPM Package ---"
# Check if rpmbuild exists
if command -v rpmbuild >/dev/null 2>&1; then
    # Create structure
    mkdir -p $RPM_DIR/{SOURCES,BUILD,RPMS,SRPMS}

    # Create source tarball
    TAR_DIR="migasfree-connect-$VERSION"
    mkdir -p /tmp/$TAR_DIR
    cp connect/migasfree-connect /tmp/$TAR_DIR/
    tar czf $RPM_DIR/SOURCES/migasfree-connect-$VERSION.tar.gz -C /tmp $TAR_DIR
    rm -rf /tmp/$TAR_DIR
    
    # Build
    rpmbuild --define "_topdir $PROJECT_ROOT/$RPM_DIR" --define "version $VERSION" -bb $RPM_DIR/SPECS/migasfree-connect.spec
    
    # Copy to dist
    cp $RPM_DIR/RPMS/noarch/*.rpm $DIST_DIR/
else
    echo "rpmbuild not found. Skipping RPM build."
fi

echo "✅ Build complete. Packages in $DIST_DIR/"
ls -l $DIST_DIR/
