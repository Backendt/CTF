ssh tristan@mailroom.htb "tail -n 2 /var/mail/tristan" | grep -o "[a-z0-9]*$"
