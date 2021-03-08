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
```bash
cp sources/credentials.ini.example sources/credentials.ini
vi sources/credentials.ini
```

### Run dashboard ###
```bash
# Either run 
python main.py
# or
python main.py --nocache
# to clear the cache
```