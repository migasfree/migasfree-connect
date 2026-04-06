#!/bin/bash
set -e

PROJECT_ROOT=$(pwd)
# Use version from argument, or fall back to pyproject.toml
if [ -n "$1" ]
then
    VERSION=${1#v}
else
    VERSION=$(grep -m1 '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
fi
DEB_DIR="packaging/deb"
RPM_DIR="packaging/rpm"
DIST_DIR="dist"

echo "Building version $VERSION..."
mkdir -p $DIST_DIR

# Update Debian Control File Version
sed -i "s/^Version: .*/Version: $VERSION/" $DEB_DIR/DEBIAN/control

# --- BUILD DEB ---
echo "--- Building DEB Package ---"
if command -v dpkg-deb >/dev/null 2>&1
then
    # Create directories
    mkdir -p $DEB_DIR/usr/bin
    mkdir -p $DEB_DIR/usr/lib/python3/dist-packages/migasfree_connect

    # Generate entry point wrapper instead of the legacy script
    cat <<EOF > $DEB_DIR/usr/bin/migasfree-connect
#!/usr/bin/python3
from migasfree_connect.cli import main
if __name__ == "__main__":
    main()
EOF
    cp -r migasfree_connect/* $DEB_DIR/usr/lib/python3/dist-packages/migasfree_connect/

    chmod 755 $DEB_DIR/usr/bin/migasfree-connect

    # Build
    dpkg-deb --build $DEB_DIR $DIST_DIR
else
    echo "dpkg-deb not found. Skipping DEB build."
fi

# --- BUILD RPM ---
echo "--- Building RPM Package ---"
# Check if rpmbuild exists
if command -v rpmbuild >/dev/null 2>&1
then
    # Create structure
    mkdir -p $RPM_DIR/{SOURCES,BUILD,RPMS,SRPMS}

    # Create source tarball
    TAR_DIR="migasfree-connect-$VERSION"
    mkdir -p "/tmp/$TAR_DIR"
    cp -r migasfree_connect pyproject.toml "/tmp/$TAR_DIR/"
    tar czf "$RPM_DIR/SOURCES/migasfree-connect-$VERSION.tar.gz" -C /tmp "$TAR_DIR"
    rm -rf "/tmp/$TAR_DIR"
    
    # Build
    rpmbuild --define "_topdir $PROJECT_ROOT/$RPM_DIR" --define "version $VERSION" -bb $RPM_DIR/SPECS/migasfree-connect.spec
    
    # Copy to dist
    cp $RPM_DIR/RPMS/noarch/*.rpm $DIST_DIR/
else
    echo "rpmbuild not found. Skipping RPM build."
fi

echo "✅ Build complete. Packages in $DIST_DIR/"
ls -l $DIST_DIR/
