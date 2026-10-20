Name:           gsettings-qt6
Version:        1.1.1
Release:        2%{?dist}
Summary:        Qt6 bindings for GSettings
License:        LGPL-3.0-only
URL:            https://gitlab.com/ubports/development/core/gsettings-qt
Source0:       https://gitlab.com/ubports/development/core/gsettings-qt/-/archive/844b0022ad214671dce960be7c3ec3dfb6a8f1f5/gsettings-qt-844b0022ad214671dce960be7c3ec3dfb6a8f1f5.tar.gz
Source1:       sources.sha256
BuildRequires:  cmake gcc-c++ ninja-build pkgconfig(gio-2.0)
BuildRequires:  qt6-qtbase-devel qt6-qtdeclarative-devel
BuildRequires:  cmake(QmlPlugins)

%description
Qt6 library and QML plugin for GSettings.

%package devel
Summary:        Development files for gsettings-qt6
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       qt6-qtbase-devel%{?_isa} pkgconfig(gio-2.0)

%description devel
Headers, linker library and pkg-config metadata for gsettings-qt6.

%prep
(cd %{_sourcedir} && sha256sum -c %{SOURCE1})
%autosetup -n gsettings-qt-844b0022ad214671dce960be7c3ec3dfb6a8f1f5

%build
export PATH=%{_qt6_bindir}:$PATH
%cmake -G Ninja -DENABLE_QT6=ON -DBUILD_TESTING=OFF
%cmake_build

%install
%cmake_install

%files
%license COPYING
%{_libdir}/libgsettings-qt6.so.1*
%{_libdir}/qt6/qml/GSettings/

%files devel
%{_libdir}/libgsettings-qt6.so
%{_libdir}/pkgconfig/gsettings-qt6.pc
%{_includedir}/qt6/QGSettings/
