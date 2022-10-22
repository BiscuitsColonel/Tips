--2020年4月1日から現在より1ヶ月後まで
select * from unnest(sequence(cast('2020-04-01' as timestamp), cast(now() + interval '1' month as timestamp), interval '1' month)) as t(from_date)