class SqlQueries:
    
    fact_cases_table_insert = ("""
        SELECT cases.caseid,
               CAST(cases.caseincountry as FLOAT),
               cases.symptoms,
               NVL2(cases.symptonsonsite, to_date(cases.symptonsonsite, 'YYYY-MM-DD'), cases.symptonsonsite),
               NVL2(cases.reportdate, to_date(cases.reportdate, 'YYYY-MM-DD'), cases.reportdate),
               NVL2(cases.hospvisitdate, to_date(cases.hospvisitdate, 'YYYY-MM-DD'), cases.hospvisitdate),
               NVL2(cases.exposurestart, to_date(cases.exposurestart, 'YYYY-MM-DD'), cases.exposurestart),
               NVL2(cases.exposureend, to_date(cases.exposureend, 'YYYY-MM-DD'), cases.exposureend),
               cases.visitingwuhan,
               cases.fromwuhan,
               cases.death,
               cases.recovered,
               cases.summary,
               sources.sourceid
          FROM staging_cases AS cases
          LEFT JOIN dim_sources sources
            ON cases.source = sources.sourcename
         WHERE cases.caseincountry <> ''
         UNION
        SELECT cases.caseid,
               NULL,
               cases.symptoms,
               NVL2(cases.symptonsonsite, to_date(cases.symptonsonsite, 'YYYY-MM-DD'), cases.symptonsonsite),
               NVL2(cases.reportdate, to_date(cases.reportdate, 'YYYY-MM-DD'), cases.reportdate),
               NVL2(cases.hospvisitdate, to_date(cases.hospvisitdate, 'YYYY-MM-DD'), cases.hospvisitdate),
               NVL2(cases.exposurestart, to_date(cases.exposurestart, 'YYYY-MM-DD'), cases.exposurestart),
               NVL2(cases.exposureend, to_date(cases.exposureend, 'YYYY-MM-DD'), cases.exposureend),
               cases.visitingwuhan,
               cases.fromwuhan,
               cases.death,
               cases.recovered,
               cases.summary,
               sources.sourceid
          FROM staging_cases AS cases
          LEFT JOIN dim_sources sources
            ON cases.source = sources.sourcename
         WHERE cases.caseincountry = ''
    """)
    
    fact_data_table_insert = ("""
        SELECT
                datastage.sno,
                TO_DATE(datastage.observationdate, 'DD/MM/YYYY'),
                locations.locationid,
                CAST(TRIM(datastage.confirmednumber) AS FLOAT8),
                CAST(TRIM(datastage.deathnumber) AS FLOAT8),
                CAST(TRIM(datastage.recoverednumber) AS FLOAT8)
        FROM staging_data AS datastage
        LEFT JOIN dim_locations locations
          ON datastage.state = locations.location
         AND datastage.country = locations.country
    """)
    
    patient_info_table_insert = ("""
        SELECT 
              cases.caseid,
              cast(cases.age as float),
              cases.gender,
              locations.locationid
        FROM staging_cases AS cases
        LEFT JOIN dim_locations AS locations
          ON cases.location = locations.location
         AND cases.country = locations.country
        where cases.age <> ''
        UNION
        SELECT 
              cases.caseid,
              NULL,
              cases.gender,
              locations.locationid
        FROM staging_cases AS cases
        LEFT JOIN dim_locations AS locations
          ON cases.location = locations.location
         AND cases.country = locations.country
        where cases.age = ''
    """)

    dim_sources_table_insert = ("""
        SELECT distinct source, link
        FROM staging_cases
    """) 
    
    dim_location_table_insert = ("""
      SELECT DISTINCT * FROM (
        SELECT DISTINCT location, country
        FROM staging_cases
        UNION
        SELECT DISTINCT state, country
        FROM staging_data
        )
    """)

    time_table_insert = ("""
    SELECT DISTINCT * FROM (
        SELECT DISTINCT reportdate, extract(day from reportdate), extract(week from reportdate), 
               extract(month from reportdate), extract(year from reportdate), extract(dayofweek from reportdate)
        FROM fact_cases
        
        UNION
        SELECT DISTINCT hospvisitdate, extract(day from hospvisitdate), extract(week from hospvisitdate), 
               extract(month from hospvisitdate), extract(year from hospvisitdate), extract(dayofweek from hospvisitdate)
        FROM fact_cases
        
        UNION
        SELECT DISTINCT exposurestart, extract(day from exposurestart), extract(week from exposurestart), 
               extract(month from exposurestart), extract(year from exposurestart), extract(dayofweek from exposurestart)
        FROM fact_cases
        
        UNION
        SELECT DISTINCT exposureend, extract(day from exposureend), extract(week from exposureend), 
               extract(month from exposureend), extract(year from exposureend), extract(dayofweek from exposureend)
        FROM fact_cases
        
        UNION
        SELECT DISTINCT observationdate, extract(day from observationdate), extract(week from observationdate), 
               extract(month from observationdate), extract(year from observationdate), extract(dayofweek from observationdate)
        FROM fact_data
        
       ) AS alltimes
    """)