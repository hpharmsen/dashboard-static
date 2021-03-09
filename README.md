# Oberon dashboard

### The right Python installation
```bash
brew update
brew upgrade
brew uninstall --ignore-dependencies python

brew install python
brew link --overwrite python
brew install direnv
brew install mysql

pip3 install --upgrade pip
pip3 install virtualenv
pip3 install black

rm /usr/local/bin/python
ln /usr/local/bin/python3 /usr/local/bin/python
```
### Get the Dashboard source code
```bash
git clone https://github.com/hpharmsen/dashboard.git
cd dashboard
```

### Create a Python virtual environment
```bash
rm -Rf venv
python -m venv venv
source venv/bin/activate
echo 'source venv/bin/activate' > .envrc
echo 'unset PS1' >> .envrc
direnv allow
python -m pip install --upgrade pip
python -m pip install -r requirements.in
```

### Fill in the credentials 
Now you need two files with all the credentials to login into Google, Simplicate, extranet, Yuki etc.

These are
```bash
credentials.ini
oauth_key.json
```
Both go in the sources folder. 

In credentials.ini set the output folder to your liking:
```ini
[output]
folder = /Users/hp/Google Drive/MT/Dashboard
```

### Run dashboard ###
```bash
# Either run 
python main.py
# or
python main.py --nocache
# to clear the cache
```
_This might take a long time at the first run._