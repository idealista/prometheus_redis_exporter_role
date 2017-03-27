import pytest
import urllib2


@pytest.fixture()
def AnsibleDefaults(Ansible):
    return Ansible("include_vars", "defaults/main.yml")["ansible_facts"]


@pytest.fixture()
def AnsibleVarBinDir(Ansible):
    return Ansible("debug", "msg={{ redis_exporter_bin_path }}")["msg"]


@pytest.fixture()
def AnsibleVars(Ansible):
    return Ansible("include_vars", "tests/group_vars/group01.yml")["ansible_facts"]


@pytest.fixture()
def Hostname(TestinfraBackend):
    return TestinfraBackend.get_hostname()


def test_redis_exporter_user(User, Group, AnsibleDefaults):
    assert User(AnsibleDefaults["redis_exporter_user"]).exists
    assert Group(AnsibleDefaults["redis_exporter_group"]).exists
    assert User(AnsibleDefaults["redis_exporter_user"]).group == AnsibleDefaults["redis_exporter_group"]


def test_redis_exporter_executable(File, Command, AnsibleDefaults, AnsibleVarBinDir):
    redis_exporter = File(AnsibleDefaults["redis_exporter_bin_path"] + "/redis_exporter")
    redis_exporter_link = File("/usr/bin/redis_exporter")
    assert redis_exporter.exists
    assert redis_exporter.is_file
    assert redis_exporter.user == AnsibleDefaults["redis_exporter_user"]
    assert redis_exporter.group == AnsibleDefaults["redis_exporter_group"]
    assert redis_exporter_link.exists
    assert redis_exporter_link.is_symlink
    assert redis_exporter_link.linked_to == AnsibleVarBinDir + "/redis_exporter"
    redis_exporter_version = Command("redis_exporter -version")
    assert redis_exporter_version.rc is 0
    assert "Redis Metrics Exporter v" + AnsibleDefaults["redis_exporter_version"] in redis_exporter_version.stderr


def test_redis_exporter_service(File, Service, Socket, AnsibleVars):
    port = AnsibleVars["redis_exporter_port"]
    assert File("/etc/systemd/system/redis_exporter.service").exists
    assert Service("redis_exporter").is_running
    assert Socket("tcp://" + ":::" + str(port)).is_listening


def test_redis_metrics(AnsibleDefaults, AnsibleVars, Hostname):
    path = AnsibleDefaults["redis_exporter_web_telemetry_path"]
    port = AnsibleVars["redis_exporter_port"]
    response = urllib2.urlopen('http://{0}:{1}/{2}'.format(Hostname, port, path))
    assert 200 == response.getcode()
    assert "# HELP redis_memory_used_bytes" in response.read()
