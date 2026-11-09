Name:		maven-jar-plugin
Version:	3.5.1
Release:	1
Summary:	Builds a JAR from compiled classes and resources
Group:		Development/Java
License:	Apache-2.0
URL:		https://maven.apache.org/plugins/maven-jar-plugin/
Source0:	https://github.com/apache/maven-jar-plugin/archive/refs/tags/maven-jar-plugin-%{version}.tar.gz#/maven-jar-plugin-%{version}.tar.gz
# The tag has no license file. This copy is in git, so the build does not
# download it.
Source1:	LICENSE-2.0.txt
BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	maven-components >= 3.10.0
BuildRequires:	java-current-devel
# Generates META-INF/maven/plugin.xml. The separate annotations package
# conflicts with maven-components on the same index file.
BuildRequires:	maven-plugin-tools
BuildRequires:	mvn(org.apache.maven.plugins:maven-plugin-plugin)
BuildRequires:	mvn(org.apache.maven.shared:file-management)
BuildRequires:	maven-file-management >= 1:3.2.0
Requires:	maven-file-management >= 1:3.2.0
BuildRequires:	mvn(org.apache.maven:maven-archiver)
BuildRequires:	maven-archiver >= 3.6.6
Requires:	maven-archiver >= 3.6.6
BuildRequires:	mvn(org.codehaus.plexus:plexus-archiver)
BuildRequires:	plexus-archiver >= 4.15.0
Requires:	plexus-archiver >= 4.15.0
BuildRequires:	mvn(commons-io:commons-io)
BuildRequires:	apache-commons-io >= 1:2.22.0
Requires:	apache-commons-io >= 1:2.22.0
BuildRequires:	mvn(org.slf4j:slf4j-api)
BuildRequires:	mvn(javax.inject:javax.inject)
# javax.inject and jakarta-inject both provide this coordinate.
BuildRequires:	javax.inject >= 1-2
Requires:	javax.inject >= 1-2
BuildRequires:	mvn(org.apache.maven:maven-plugin-api)
BuildRequires:	mvn(org.apache.maven:maven-core)
BuildRequires:	mvn(org.apache.maven:maven-artifact)
BuildRequires:	mvn(org.apache.maven.plugin-tools:maven-plugin-annotations)
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

Obsoletes:	maven2-plugin-jar <= 0:2.0.8
Provides:	maven2-plugin-jar = %{EVRD}
Obsoletes:	maven-jar-plugin-javadoc < %{EVRD}

%description
Builds a JAR from the project's classes and resources, and can attach
a test JAR. 3.5 writes the toolchain JDK into the manifest. 3.5.1
updates plexus-archiver and commons-io. 4.0.0 is still a beta, so
this package stays on 3.5.1. Tests need JUnit Jupiter, so they are
not run.

%prep
%autosetup -n maven-jar-plugin-maven-jar-plugin-%{version}
rm -rf src/test src/it .github src/main/filtered-resources
cp -p %{SOURCE1} LICENSE
python - <<'PY'
import xml.etree.ElementTree as ET
NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def tag(name):
    return "{" + NS + "}" + name

def add(parent, name, text):
    node = ET.SubElement(parent, tag(name))
    node.text = text
    return node

root = ET.Element(tag("project"))
add(root, "modelVersion", "4.0.0")
add(root, "groupId", "org.apache.maven.plugins")
add(root, "artifactId", "maven-jar-plugin")
add(root, "version", "%{version}")
add(root, "packaging", "maven-plugin")
add(root, "name", "Apache Maven JAR Plugin")
props = ET.SubElement(root, tag("properties"))
add(props, "maven.compiler.release", "8")
add(props, "project.build.sourceEncoding", "UTF-8")
deps = ET.SubElement(root, tag("dependencies"))
items = (
    ("org.apache.maven.shared", "file-management", "3.2.0", None),
    ("org.apache.maven", "maven-archiver", "3.6.6", None),
    ("org.codehaus.plexus", "plexus-archiver", "4.15.0", None),
    ("commons-io", "commons-io", "2.22.0", None),
    ("org.slf4j", "slf4j-api", "1.7.36", None),
    ("javax.inject", "javax.inject", "1", None),
    ("org.apache.maven", "maven-plugin-api", "3.10.0", "provided"),
    ("org.apache.maven", "maven-core", "3.10.0", "provided"),
    ("org.apache.maven", "maven-artifact", "3.10.0", "provided"),
    ("org.apache.maven.plugin-tools", "maven-plugin-annotations", "3.15.2", "provided"),
)
for group, artifact, version, scope in items:
    dep = ET.SubElement(deps, tag("dependency"))
    add(dep, "groupId", group)
    add(dep, "artifactId", artifact)
    add(dep, "version", version)
    if scope:
        add(dep, "scope", scope)
build = ET.SubElement(root, tag("build"))
plugins = ET.SubElement(build, tag("plugins"))
plugin = ET.SubElement(plugins, tag("plugin"))
add(plugin, "groupId", "org.apache.maven.plugins")
add(plugin, "artifactId", "maven-plugin-plugin")
# The lifecycle binding asks for 3.15.1. The packaged plugin is 3.16.0.
add(plugin, "version", "3.16.0")
ET.ElementTree(root).write("pom.xml", encoding="utf-8", xml_declaration=True)
PY
# Sisu loads @Named classes from this index. The indexer plugin is not packaged.
python - <<'PY'
import re
from pathlib import Path
root = Path("src/main/java")
names = []
for path in sorted(root.rglob("*.java")):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*?$", "", text, flags=re.M)
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z0-9_]+)", text)
    if not match:
        continue
    if "@Named" not in text[:match.start()]:
        continue
    pkg = re.search(r"(?m)^package\s+([A-Za-z0-9_.]+)\s*;", text)
    if not pkg:
        continue
    names.append(pkg.group(1) + "." + match.group(1))
if names:
    dest = Path("src/main/resources/META-INF/sisu")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "javax.inject.Named").write_text("\n".join(names) + "\n", encoding="utf-8")
PY

%files -f .mfiles
%doc LICENSE README.md
