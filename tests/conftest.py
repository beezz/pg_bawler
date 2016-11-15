
import uuid
import time
import pytest
import psycopg2
from docker import Client as DockerClient


@pytest.fixture(scope='session')
def session_id():
    return str(uuid.uuid4())


@pytest.fixture(scope='session')
def docker():
    return DockerClient(version='auto')


@pytest.yield_fixture(scope='session')
def pg_server(docker, session_id):
    pg_tag = '9.6'
    docker.pull('postgres:{}'.format(pg_tag))
    container = docker.create_container(
        image='postgres:{}'.format(pg_tag),
        name='bawler-test-server-{}-{}'.format(pg_tag, session_id),
        detach=True,
    )
    docker.start(container=container['Id'])
    inspection = docker.inspect_container(container['Id'])
    host = inspection['NetworkSettings']['IPAddress']
    pg_params = dict(
        dbname='postgres',
        user='postgres',
        password='',
        host=host)

    delay = 0.001
    for i in range(100):
        try:
            conn = psycopg2.connect(**pg_params)
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.close()
            conn.close()
            break
        except psycopg2.Error as exc:
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail("Cannot start postgres server")

    container['host'] = host
    container['pg_params'] = pg_params

    yield container

    docker.kill(container=container['Id'])
    docker.remove_container(container['Id'])
