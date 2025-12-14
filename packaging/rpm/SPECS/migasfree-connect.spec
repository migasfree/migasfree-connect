Name:           migasfree-connect
Version:        1.0
Release:        1%{?dist}
Summary:        Client for migasfree remote tunnel sessions

License:        GPLv3
URL:            https://github.com/migasfree/migasfree-connect
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3
Requires:       python3-websockets
Requires:       python3-requests

%description
Client script for establishing remote sessions (SSH, VNC, RDP) via migasfree tunnel infrastructure.

%prep
%setup -q

%build
# Nothing to build, it's a python script

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_bindir}
install -m 0755 migasfree-connect/migasfree-connect $RPM_BUILD_ROOT%{_bindir}/%{name}

%files
%{_bindir}/%{name}

%changelog
* Sun Dec 14 2025 Alberto Gacías <alberto@migasfree.org> - 1.0-1
- Initial package
