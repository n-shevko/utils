## What it does
1. Accepts all changes (aka revisions) in document margins of docx file.
   Microsoft Word displays formatting and deletion changes in the margins. 
3. Recovers EndNote (commercial software) citations that were broken inside docx file.

## How to install it
1. Install docker

  Mac https://docs.docker.com/desktop/install/mac-install/

  Windows https://docs.docker.com/desktop/install/windows-install/

  Linux https://docs.docker.com/desktop/install/linux-install/

2. Clone repository
```
git clone https://github.com/n-shevko/utils.git
```

## Usage
```
cd utils
python3 run.py /path/to/folder/that/app/will/see
```
When the following line will be shown
```
Listening on TCP address 0.0.0.0:8000
```
Open web browser and go to http://127.0.0.1:8000/

To stop service just press Control+C

Also you can change port that app will use
```
python3 run.py --port 3000 /path/to/folder/that/app/will/see
```
The app works without Internet.
