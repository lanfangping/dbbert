CREATE USER 'dbbert'@'%' IDENTIFIED BY 'dbbert';
GRANT ALL PRIVILEGES ON *.* TO 'dbbert'@'%';
FLUSH PRIVILEGES;