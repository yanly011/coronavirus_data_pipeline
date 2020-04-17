CREATE TABLE IF NOT EXISTS public.dim_sources (
	sourceid   INT8 IDENTITY(1, 1),
	sourcename varchar(1024),
	link       varchar(65535)
);

CREATE TABLE IF NOT EXISTS public.dim_times (
	"time" DATE NOT NULL,
	"day" int4,
	week int4,
	"month" varchar(256),
	"year" int4, 
	weekday varchar(256),
	CONSTRAINT time_pkey PRIMARY KEY (time)
);

CREATE TABLE IF NOT EXISTS public.dim_locations (
	locationid      INT8 IDENTITY(1, 1),
	location        varchar(50),
	country         varchar(50)
);

CREATE TABLE IF NOT EXISTS public.patientinfo (
    patientid      varchar(256),
    age            INT4,
	  gender         varchar(20),
	  locationid     INT8
);

CREATE TABLE IF NOT EXISTS public.fact_data (
    sno              varchar(256) NOT NULL,
    observationdate  DATE,
    locationid       INT8,
    confirmednumber  INT8,
    deathnumber      INT8,
    recoverednumber  INT8
);

CREATE TABLE IF NOT EXISTS public.fact_cases (
    caseid         varchar(256) NOT NULL,
    caseincountry  INT8,
	  symptoms       varchar(512),
    symptonsonsite DATE,
    reportdate     DATE,
	  hospvisitdate  DATE,
	  exposurestart  DATE,
    exposureend    DATE,
	  visitingwuhan  varchar(10),
    fromwuhan      varchar(10),
    death          varchar(10),
    recovered      varchar(10),
    summary        varchar(65535),
	  sourceid       varchar(256)
);

CREATE TABLE IF NOT EXISTS public.staging_cases (
	  caseid         varchar(256) NOT NULL,
    caseincountry  varchar(256),
    reportdate     varchar(20),
    summary        varchar(65535),
    location       varchar(512), 
    country        varchar(20),
    gender         varchar(20),
    age            varchar(10),
	  symptonsonsite varchar(50),
	  onsetapproximated varchar(10),
	  hospvisitdate  varchar(20),
	  exposurestart  varchar(20),
    exposureend    varchar(20),
	  visitingwuhan  varchar(10),
    fromwuhan      varchar(10),
    death          varchar(10),
    recovered      varchar(10),
    symptoms       varchar(512),
	  source         varchar(512),
    link           varchar(65535)
);

CREATE TABLE IF NOT EXISTS public.staging_data (
    sno              varchar(256) NOT NULL,
    observationdate  varchar(20),
    state            varchar(50),
    country          varchar(50),
    last_update      varchar(20),
    confirmednumber  varchar(256),
    deathnumber      varchar(256),
    recoverednumber  varchar(256)
)
