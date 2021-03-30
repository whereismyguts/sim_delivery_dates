# создание окружения
sudo-Epython3 -m venv ./

#  установка зависимостей
sudo -E yum install gmp-devel
 
sudo rm -rf /tmp/pip-*
export LD_LIBRARY_PATH="/usr/lib64:$LD_LIBRARY_PATH"

sudo -E yum install python-devel
sudo -E bin/python -m pip install -r requirements.txt

 