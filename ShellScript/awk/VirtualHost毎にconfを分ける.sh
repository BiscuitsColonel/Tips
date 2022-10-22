count=0
cat httpd.conf | grep -v -e '^\s*#' -e '^\s*$' | awk '/VirtualHost \*:80/,/\/VirtualHost/' | while IFS= read line; do
  if [ $(echo ${line} | grep '</VirtualHost>') ]; then
    echo "${line}" >> vhost${count}.conf && count=$(( ${count} + 1 ))
  else
    echo "${line}" >> vhost${count}.conf
  fi
done