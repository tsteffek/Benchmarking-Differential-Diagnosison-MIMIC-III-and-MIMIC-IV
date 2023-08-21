SELECT count(distinct subject_id) FROM mimiciv_note.discharge;

SELECT * from mimiciv_hosp.admissions
JOIN (SELECT * from mimiciv_hosp.diagnoses_icd WHERE icd_code LIKE '650%') x
    ON admissions.hadm_id = x.hadm_id
JOIN mimiciv_hosp.patients on admissions.subject_id = patients.subject_id;

select count(counts) from
(SELECT count(*) as counts from mimiciv_note.discharge group by text) dc

select hadm_id
    from mimiciv_note.discharge
group by hadm_id having count(*) > 1