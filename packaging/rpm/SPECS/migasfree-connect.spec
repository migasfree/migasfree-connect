Name:           migasfree-connect
Version:        %{version}
Release:        1%{?dist}
Summary:        Client for migasfree remote tunnel sessions

License:        GPLv3
URL:            https://github.com/migasfree/migasfree-connect
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3
Requires:       python3-websockets
Requires:       python3-requests
# Test dependencies
#Requires:       python3-pytest
#Requires:       python3-pytest-asyncio

%description
Client script for establishing remote sessions (SSH, VNC, RDP) via migasfree tunnel infrastructure.

%prep
%setup -q

%build
# Nothing to build, it's a python script

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_bindir}
install -d $RPM_BUILD_ROOT%{python3_sitelib}/migasfree_connect
install -m 0755 connect/migasfree-connect $RPM_BUILD_ROOT%{_bindir}/%{name}
cp -r migasfree_connect/* $RPM_BUILD_ROOT%{python3_sitelib}/migasfree_connect/

%files
%{_bindir}/%{name}
%{python3_sitelib}/migasfree_connect/

%changelog
* Sun Dec 14 2025 Alberto Gacías <alberto@migasfree.org> - 1.0-1
- Initial package
