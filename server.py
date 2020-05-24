import os
import signal
import subprocess
import sys
import logging

# cpu_count = multiprocessing.cpu_count()

server_timeout = os.environ.get('MODEL_SERVER_TIMEOUT', 60)
server_workers = int(os.environ.get('MODEL_SERVER_WORKERS', 1))
working_dir = os.getenv("WORKING_DIR", os.getcwd())
nginx_conf_file = os.path.join(working_dir, 'nginx.conf')
gunicorn_conf_file = os.path.join(working_dir, 'gunicorn.conf.py')
num_workers = '1'
host_ip = '0.0.0.0'
port = os.getenv("EXPOSE_PORT", 8050)
logging.basicConfig(level=logging.INFO)


def sigterm_handler(nginx_pid, gunicorn_pid):
    try:
        os.kill(nginx_pid, signal.SIGQUIT)
    except OSError:
        pass
    try:
        os.kill(gunicorn_pid, signal.SIGTERM)
    except OSError:
        pass

    sys.exit(0)


def main():
    logging.info('Starting the server with {} workers.'.format(server_workers))
    nginx = subprocess.Popen(['nginx', '-c', nginx_conf_file])
    gunicorn = subprocess.Popen(['gunicorn',
                                 '-w', num_workers,
                                 '-b', 'unix:/tmp/gunicorn.sock',
                                 'wsgi:server'])
    logging.info(f'Server running on: http://{host_ip}:{port}')

    signal.signal(signal.SIGTERM, lambda a, b: sigterm_handler(nginx.pid, gunicorn.pid))

    # If either subprocess exits, so do we.
    pids = set([nginx.pid, gunicorn.pid])
    while True:
        pid, _ = os.wait()
        if pid in pids:
            break

    sigterm_handler(nginx.pid, gunicorn.pid)  #
    logging.warning('Server exiting.')


if __name__ == '__main__':
    main()
