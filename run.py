import sys
import os
import shlex


def main():
    n = len(sys.argv)
    if n == 1:
        data = os.path.expanduser('~')
    else:
        data = sys.argv[1]
    data = shlex.quote(data)
    os.system('docker pull nikos123/utils:1.0.0')
    os.system('docker stop -t 0 utils_container')
    os.system('docker rm utils_container')
    user_id = os.getuid()
    group_id = os.getgid()
    os.system(f"docker run --name utils_container -v service_data:/service_data -v {data}:{data} -e USER_DATA={data} -e USER_ID={user_id} -e GROUP_ID={group_id} -p 8000:8000 nikos123/utils:1.0.0")


if __name__ == '__main__':
    main()