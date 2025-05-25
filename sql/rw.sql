CREATE SOURCE pg_source WITH (
    connector='postgres-cdc',
    hostname='postgres-vendor-0',
    port='5432',
    username='postgres',
    password='postgres',
    database.name='postgres',
    schema.name='public',
    slot.name = 'rising_wave',
    publication.name ='rw_publication'
);

CREATE TABLE receipt_headers (
	id int primary key,
	"businessName" varchar ,
	"date" varchar ,
	total float8 ,
	tax float8 
) FROM pg_source TABLE 'public.receipt_headers';

CREATE TABLE receipt_items (
	id int primary key  ,
	header_id int4 ,
	"name" varchar ,
	price float8 
) FROM pg_source TABLE 'public.receipt_items';


create materialized view summary_receipt as
select 
	a.id,
	a."businessName",
	a."date",
	a.total,
	a.tax,
	b."name",
	b.price
from receipt_headers a
join receipt_items b on a.id = b.header_id;

CREATE SINK sink_summary_receipt FROM summary_receipt
WITH (
    connector = 'iceberg',
    type = 'append-only',
    force_append_only = true,
    s3.endpoint = 'http://minio:9000',
    s3.region = 'us-east-1',
    s3.access.key = 'admin',
    s3.secret.key = 'password',
    s3.path.style.access = 'true',
    catalog.type = 'rest',
    catalog.uri = 'http://amoro:1630/api/iceberg/rest',
    catalag.name = 'icelake',
    warehouse.path = 'icelake',
    database.name = 'warehouse',
    table.name = 'summary_receipt',
    create_table_if_not_exists = TRUE
);

