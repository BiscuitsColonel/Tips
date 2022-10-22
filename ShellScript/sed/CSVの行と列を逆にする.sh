for i in $(seq $(( $(sed -n 1p ${CSVFILE} | grep -o -i , | wc -l) + 1 ))); do
  cut -d , -f ${i} ${CSVFILE} | tr '\n' ',' | sed 's/,$/\n/g'
done