%define section free

Name:           jpcsc
Version:        0.8.0
Release:        1
Epoch:          0
Summary:        JNI wrappers for PC/SC

Group:          Development/Libraries/Java
License:        IBM AlphaWorks License
URL:            http://www.linuxnet.com/middle.html
Source0:        http://www.linuxnet.com/middleware/files/jpcsc-0.7.6.zip
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Vendor:         ZRL
Distribution:   ZRL

BuildRequires:  dos2unix,pkgconfig, pcsc-lite-devel

%description
JPCSC provides a simple JNI library to allow for the access of PC/SC
functions from Java. It offers an API to acces most of the Card- and
Context-related functions, i.e. establish a context, list readers,
open a reader connection, and send APDUs to a reader and card.  JPCSC
supports both Windows and Linux, a port to MacOSX should be
easy. JPCSC does not offer any advanced, application- or card-specific
APIs (such as OpenCard), it just provides a resource-efficient and
simple access to the smartcard infrastructure available on most
desktop systems as of today, i.e. PC/SC.

%package        javadoc
Summary:        Javadocs for JPCSC
Group:          Development/Documentation

%description    javadoc
%{summary}.


%prep
%setup -q -n %{name}
#%patch0 -p0
rm -rf apidoc bin 


%build
export JAVA_HOME="%{java_home}"
export CCFLAGS="$RPM_OPT_FLAGS"
%{__make} \
  PCSCDIR=%(pkg-config libpcsclite --variable=prefix 2>/dev/null) \
  JAVADOC="$JAVA_HOME/bin/javadoc -use"


%install
rm -rf $RPM_BUILD_ROOT %{name}/_docs
# jars
install -Dpm 644 build/java/%{name}.jar \
  $RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar
ln -s %{name}-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/%{name}.jar
# native libs
install -Dpm 755 build/linux/lib%{name}.so \
  $RPM_BUILD_ROOT%{_libdir}/lib%{name}.so
# javadocs
install -dm 755 $RPM_BUILD_ROOT%{_javadocdir}
cp -pr build/docs $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name}
# other stuff
install -dm 755 _docs/samples
install -pm 644 src/samples/*.java _docs/samples
install -Dpm 644 build/samples.jar _docs/samples.jar


%clean
rm -rf $RPM_BUILD_ROOT


%post javadoc
rm -f %{_javadocdir}/%{name}
ln -s %{name}-%{version} %{_javadocdir}/%{name}


%files
%defattr(-,root,root,-)
%doc License.html README _docs/samples _docs/samples.jar
%{_libdir}/lib%{name}.so
%{_javadir}/%{name}*.jar

%files javadoc
%defattr(-,root,root,-)
%doc %{_javadocdir}/%{name}-%{version}
%ghost %doc %{_javadocdir}/%{name}


%changelog
* Wed Jul 21 2004 Marcus Oestreicher <oes@zurich.ibm.com> - 0:0.8.0
- Updated for pcsclite >= 1.2.9
* Tue Mar 30 2004 Marcus Oestreicher <oes@zurich.ibm.com> - 0:0.7.6-1
- First build.

