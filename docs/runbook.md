## Too Many Rows!

We currently have a tablerow limit of 10k across all tables. We will get a warning and a grace period if we go over (notified via email).

To fix this usually we just need to clear the django session table.

```
heroku psql

-- get the offending tables
chipy-mentorship::DATABASE=> WITH tbl AS
  (SELECT table_schema, TABLE_NAME
   FROM information_schema.tables
   WHERE TABLE_NAME not like 'pg_%' AND table_schema in ('public'))
SELECT table_schema, TABLE_NAME
 , (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, TABLE_NAME), FALSE, TRUE, '')))[1]::text::int AS rows_n
FROM tbl
ORDER BY rows_n DESC;

 table_schema |          table_name           | rows_n
--------------+-------------------------------+--------
 public       | django_session                |   7921
 public       | buddy_mentorship_experience   |   1028
...
(19 rows)

-- Django Session looks high, right? Let's nuke

truncate table django_session;

-- Rerun command
 table_schema |          table_name           | rows_n
--------------+-------------------------------+--------
 public       | buddy_mentorship_experience   |   1028
...
 public       | django_session                |   0
(19 rows)
```
