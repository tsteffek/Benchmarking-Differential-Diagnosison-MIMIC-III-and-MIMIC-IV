SELECT *
FROM (SELECT hadm_id, count(distinct icd_version) as ct
      FROM mimiciv_hosp.diagnoses_icd
      GROUP BY hadm_id) t
         JOIN mimiciv_hosp.diagnoses_icd m ON m.hadm_id = t.hadm_id
         JOIN mimiciv_hosp.d_icd_diagnoses did on m.icd_code = did.icd_code
WHERE t.ct > 1;

-- Count hadm_id one

SELECT count(distinct hadm_id)
FROM mimiciv_hosp.procedures_icd;

-- Count hadm_id both

SELECT count(distinct x.hadm_id)
FROM (SELECT hadm_id
      FROM procedures_icd pro
      UNION ALL
      SELECT hadm_id
      from diagnoses_icd) x;

-- Count hadm_id icd version 9&10

SELECT distinct t.hadm_id
FROM (SELECT hadm_id, count(distinct icd_version) as ct
      FROM (SELECT hadm_id, icd_version
            FROM procedures_icd
            UNION ALL
            SELECT hadm_id, icd_version
            from diagnoses_icd) x
      GROUP BY hadm_id) t
WHERE t.ct > 1;

-- Count ICD Versions per admission

SELECT icd_version, count(distinct hadm_id) as ct
FROM (SELECT hadm_id, icd_version
      FROM procedures_icd
      UNION ALL
      SELECT hadm_id, icd_version
      from diagnoses_icd) x
GROUP BY icd_version;

-- Count ICD Versions

SELECT icd_version, count(icd_version) as ct
FROM (SELECT icd_version
      FROM procedures_icd
      UNION ALL
      SELECT icd_version
      from diagnoses_icd) x
GROUP BY icd_version;

-- Overlap between Procedures and Diagnoses
SELECT *
from d_icd_procedures dip
         inner join d_icd_diagnoses did
                    on dip.icd_version = did.icd_version and dip.icd_code = did.icd_code
WHERE did.icd_version = 10;

-- Count Anchor Year Group Patients
select anchor_year_group, count(anchor_year_group)
from patients
GROUP BY anchor_year_group;

--

SELECT *
FROM patients
LIMIT 50;

-- Difference first admission to last discharge per patient
SELECT x.hospital_time, count(x.hospital_time)
FROM (SELECT date_part('year', AGE(max(dischtime), min(admittime))) as hospital_time
      FROM admissions
      GROUP BY subject_id) x
GROUP BY x.hospital_time
ORDER BY x.hospital_time;

-- ICD Versions per Year Group
with admissions_year as (select *, date_part('year', admittime) - year_offset as approximate_year
from admissions ads
         join (SELECT patients.subject_id, anchor_year - "left"(anchor_year_group, 4)::int as year_offset from patients) pats
              on pats.subject_id = ads.subject_id)

select approximate_year, icd_version, count(icd_version)
from procedures_icd
join admissions_year on admissions_year.hadm_id = procedures_icd.hadm_id
GROUP BY approximate_year, icd_version
order by icd_version, approximate_year;

--
