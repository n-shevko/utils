import sys
import os


def main():
    n = len(sys.argv)
    if n == 1:
        data = os.path.expanduser('~')
    else:
        data = sys.argv[1]
    os.system('docker build -t utils_img .')
    os.system('docker stop -t 0 utils_container')
    os.system('docker rm utils_container')
    user_id = os.getuid()
    group_id = os.getgid()
    os.system(f"docker run --name utils_container -v service_data:/service_data -v {data}:{data} -e USER_DATA={data} -e USER_ID={user_id} -e GROUP_ID={group_id} -p 8000:8000 utils_img")


if __name__ == '__main__':
    main()