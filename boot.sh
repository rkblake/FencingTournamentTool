#!/bin/sh
source venv/bin/activate
while true; do
	flask db upgrade
	if [[ "$?" == "0" ]]; then
		break
	fi
	echo "Upgrade command failed, retyring in 5 seconds."
	sleep 5
done
flask db upgrade
exec gunicorn -b :5000 --access-logfile - --error-logfile - fencingtournamenttool:app
