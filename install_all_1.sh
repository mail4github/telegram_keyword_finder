apt-get -y update &&
apt-get -y install sudo &&
apt-get -y install nano &&
apt-get -y install apache2 &&
apt-get -y install ftp &&
apt-get -y install aptitude &&
a2enmod rewrite &&
chmod 777 /var/www/ &&
find /etc/apache2/* -type d -print -exec chown -R root {} \; &&
find /etc/apache2/* -type f -print -exec chown -R root {} \; &&
find /etc/apache2/* -type d -print -exec chmod augo+rwx {} \; &&
find /etc/apache2/* -type f -print -exec chmod augo+rwx {} \; &&
apt-get -y install php &&
apt-get -y install libapache2-mod-php &&
apt-get -y install php-mysql &&
apt-get -y install php-xml &&
apt-get -y install php-gd &&
apt-get -y install php-json &&
apt-get -y install curl &&
apt-get -y install libcurl3-dev &&
apt-get -y install php-curl &&
apt-get -y install php-mbstring &&
apt-get -y install mysql-client &&
apt-get -y install php-zip &&
apt-get -y install libgmp-dev &&
apt-get -y install php-gmp &&
a2enmod rewrite &&
aptitude install -y w3m &&
dpkg-reconfigure tzdata &&
apt-get -y install ntpdate &&
ntpdate -s time.nist.gov &&
apt-get -y install cron &&
apt-get -y install sysstat &&
apt-get -y install rsyslog &&
service rsyslog start
echo -e "\033[32m All done! \033[0m"
echo -e "\033[32m You need to comment row: Alias /javascript /usr/share/javascript/  \033[0m"
echo -e "\033[32m in file: /etc/apache2/conf-available/javascript-common.conf \033[0m"

