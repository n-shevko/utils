import os
import shlex
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, help='Port number (default 8000)', default=8000)
    parser.add_argument('data', nargs='?', default=os.path.expanduser('~'), help=f"Path to folder that app will see (default {os.path.expanduser('~')})")
    args = parser.parse_args()

    data = shlex.quote(args.data)
    os.system('docker pull nikos123/utils:1.0.0')
    os.system('docker stop -t 0 utils_container')
    os.system('docker rm utils_container')
    user_id = os.getuid()
    group_id = os.getgid()
    os.system(f"docker run --name utils_container -v service_data:/service_data -v {data}:{data} -e USER_DATA={data} -e USER_ID={user_id} -e GROUP_ID={group_id} -p {args.port}:8000 nikos123/utils:1.0.0")


if __name__ == '__main__':
    main()