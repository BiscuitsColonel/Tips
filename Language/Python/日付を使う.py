import datetime
from dateutil.relativedelta import relativedelta

# 今日# => 2020-04-02
today = datetime.date.today()

# 年を取得# => 2020
today.year

# 月を取得# => 4
today.month

# 日を取得# => 2
today.day

# 曜日を取得# => 3
# 0:月,1:火,2:水,3:木,4:金,5:土,6:日
today.weekday()

# 昨日# => 2020-04-01
yesterday = today + relativedelta(days=-1)

# 明日# => 2020-04-03
tommorow = today + relativedelta(days=+1)

# 1週間前# => 2020-03-26
one_week_ago = today + relativedelta(weeks=-1)

# 1週間後# => 2020-04-09
one_week_later = today + relativedelta(weeks=+1)

# 1ヶ月前# => 2020-03-02
one_month_ago = today + relativedelta(months=-1)

# 1ヶ月後# => 2020-05-02
one_month_later = today + relativedelta(months=+1)

# 1年前# => 2019-04-02
one_year_ago = today + relativedelta(years=-1)

# 1年後# => 2021-04-02
one_year_later = today + relativedelta(years=+1)

# 月初(今月の1日にする)# => 2020-04-01
beginning_of_the_month = today + relativedelta(day=1)

# 月末 (来月の1日に合わせて1日分戻る)# => 2020-04-30
end_of_month = today + relativedelta(months=+1,day=1,days=-1)

# 先月初(1月分戻して、1日にする)# => 2020-03-01
beginning_of_the_last_month = today + relativedelta(months=-1,day=1)

# 先月末 (今月の1日から1日分戻る)# => 2020-03-31
end_of_the_last_month = today + relativedelta(day=1,days=-1)

# 翌月初(1月分進めて、1日にする)# => 2020-05-01
beginning_of_the_next_month = today + relativedelta(months=+1,day=1)

# 翌月末 (翌々月初[2ヶ月後の1日]から1日分戻す)# => 2020-05-31
end_of_the_next_month = today + relativedelta(months=+2,day=1,days=-1)