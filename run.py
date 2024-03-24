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
    os.system(f"docker run --name utils_container -v service_data:/service_data -v {data}:{data}  -p 8000:8000 utils_img")


if __name__ == '__main__':
    main()