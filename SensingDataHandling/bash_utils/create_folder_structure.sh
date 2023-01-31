#!/usr/bin/expect -f

spawn ssh pi@vhive.local
expect "password:"
sleep 1
send "mobots\r"

month="$1"
day="$2"
mkdir -p "/cron_test/structure/$month/$day/"

