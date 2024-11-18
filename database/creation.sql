DROP SEQUENCE IF EXISTS decp_report.s_account;
DROP SEQUENCE IF EXISTS decp_report.s_session;
DROP SEQUENCE IF EXISTS decp_report.s_report;
DROP SEQUENCE IF EXISTS decp_report.s_step;
DROP SEQUENCE IF EXISTS decp_report.s_file;
DROP SEQUENCE IF EXISTS decp_report.s_source;
DROP SEQUENCE IF EXISTS decp_report.s_exclusion_type;

CREATE SEQUENCE decp_report.s_session;
CREATE SEQUENCE decp_report.s_account;
CREATE SEQUENCE decp_report.s_report;
CREATE SEQUENCE decp_report.s_step;
CREATE SEQUENCE decp_report.s_file;
CREATE SEQUENCE decp_report.s_source;
CREATE SEQUENCE decp_report.s_exclusion_type;

DROP TABLE IF EXISTS decp_report.report;

CREATE TABLE decp_report.report (
   report_id            INT8                 not null,
   session_id           INT8                 not null,
   step_id              INT8                 not null,
   source_id            INT8                 not null,
   file_id              INT8                 not null,
   exclusion_type_id    INT8                 not null,
   position             INT8                 null,
   message              VARCHAR(256)         not null,
   error                VARCHAR(2048)        null,
   path                 VARCHAR(256)         null,
   content              VARCHAR(4096)        null,
   creation_date        TIMESTAMP            not null,
   CONSTRAINT pk_report PRIMARY KEY (report_id)
);

COMMENT ON COLUMN report.report_id IS 'Identifiant interne de l''enregistrement';

COMMENT ON COLUMN report.source_id IS 'Flux d''ou provient l''enregistrement';

COMMENT ON COLUMN report.exclusion_type_id IS 'Type de message ou d''erreur lie a l''enregistrement';

COMMENT ON COLUMN report.file_id IS 'Nom du fichier d''ou provient l''enregistrement';

COMMENT ON COLUMN report.path IS 'Chemin logique du noeud où s''est produit l''erreur';

COMMENT ON COLUMN report.position IS 'Position de l''enregistrement dans fichier';

COMMENT ON COLUMN report.message IS 'Message d''erreur';

COMMENT ON COLUMN report.content IS 'Contenu de l''enregistrement';

COMMENT ON COLUMN report.creation_date IS 'Date de creation de l''enregistrement ';

CREATE INDEX fk_report_source_id on decp_report.report (source_id);

CREATE INDEX fk_report_file_id on decp_report.report (file_id);

DROP TABLE IF EXISTS decp_report.account;

CREATE TABLE decp_report.account (
   account_id           INT8                 not null,
   user_name            VARCHAR(256)         not null,
   passwd               VARCHAR(256)         null,
   active               BOOL                 null,
   source_id            INT8                 null,
   CONSTRAINT pk_account primary key (account_id)
);

DROP TABLE IF EXISTS decp_report.session;

CREATE TABLE decp_report.session (
   session_id           INT8                 not null,
   name                 VARCHAR(256)         not null,
   message              VARCHAR(256)         null,
   begin_date           TIMESTAMP            not null,
   end_date             TIMESTAMP            null,
   CONSTRAINT pk_session primary key (session_id)
);

DROP TABLE IF EXISTS decp_report.step;

CREATE TABLE decp_report.step (
   step_id              INT8                 not null,
   name                 VARCHAR(64)          null,
   creation_date        TIMESTAMP            null,
   CONSTRAINT pk_step PRIMARY KEY (step_id)
);

DROP TABLE IF EXISTS decp_report.file;

CREATE TABLE decp_report.file (
   file_id              INT8                 not null,
   name                 VARCHAR(64)          null,
   source_id            INT8                 null,
   nb_marches           INT8                 null,
   nb_concessions       INT8                 null,
   creation_date        TIMESTAMP            null,
   CONSTRAINT pk_file PRIMARY KEY (file_id)
);

DROP TABLE IF EXISTS decp_report.exclusion_type;

CREATE TABLE decp_report.exclusion_type (
   exclusion_type_id    INT8                 not null,
   code                 VARCHAR(64)          null,
   name                 VARCHAR(64)          null,
   creation_date        TIMESTAMP            null,
   CONSTRAINT pk_exclusion_type PRIMARY KEY (exclusion_type_id)
);


DROP TABLE IF EXISTS decp_report.source;

CREATE TABLE decp_report.source (
   source_id            INT8                 not null,
   name                 VARCHAR(64)          null,
   creation_date        TIMESTAMP            null,
   CONSTRAINT pk_source PRIMARY KEY (source_id)
);

ALTER TABLE decp_report.report
   ADD CONSTRAINT fk_report_source FOREIGN KEY (source_id)
      REFERENCES decp_report.source (source_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE decp_report.report
   add constraint fk_report_step FOREIGN KEY (step_id)
      REFERENCES decp_report.step (step_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE decp_report.report
   ADD CONSTRAINT fk_report_file FOREIGN KEY (file_id)
      REFERENCES decp_report.file (file_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE decp_report.report
   ADD CONSTRAINT fk_report_session FOREIGN KEY (session_id)
      REFERENCES decp_report.session (session_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE decp_report.file
   ADD CONSTRAINT fk_file_source FOREIGN KEY (source_id)
      REFERENCES decp_report.source (source_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE decp_report.account
   ADD CONSTRAINT fk_account_source FOREIGN KEY (source_id)
      REFERENCES decp_report.source (source_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

DROP VIEW decp_report.v_stats_global_by_session;

CREATE OR REPLACE VIEW decp_report.v_stats_global_by_session AS 
 SELECT s.begin_date,s.end_date, src."name", SUM(f.nb_marches) + SUM(f.nb_concessions) AS nb_records, SUM( nb_error) AS nb_errors
 FROM decp_report."session" s 
 INNER JOIN (
 	SELECT r.session_id,r.file_id,count(DISTINCT r.position) AS nb_error,f.nb_marches, f.nb_concessions
 	FROM decp_report.report r
	 INNER JOIN decp_report.file f 
	 ON f.file_id = r.file_id 
 	GROUP BY r.session_id,r.file_id,f.nb_marches ,f.nb_concessions
 ) r
 ON r.session_id = s.session_id 
 INNER JOIN decp_report.file f 
 ON f.file_id = r.file_id 
 INNER JOIN decp_report."source" src 
 ON src.source_id = f.source_id 
 GROUP BY s.session_id,s.name,s.begin_date,s.end_date, src."name";
 
DROP VIEW decp_report.v_stats_all;

CREATE OR REPLACE VIEW decp_report.v_stats_all AS 
SELECT s.name,s.source_id,r.session_id,
	(SELECT end_date FROM decp_report."session" si WHERE si.session_id = r.session_id) AS session_date,
	r.nb_errors,
	r.nb_records,
	100 * r.nb_errors / COALESCE(r.nb_records,NULL) AS per_errors
FROM (
	SELECT r.source_id,r.session_id,sum(DISTINCT file_id) AS nb_files,sum(nb_error) AS nb_errors, sum(nb_marches) + sum(nb_concessions) AS nb_records
	FROM (
	 	SELECT r.source_id,r.session_id,r.file_id,count(DISTINCT r.position) AS nb_error,f.nb_marches, f.nb_concessions
	 	FROM decp_report.report r
		INNER JOIN decp_report.file f 
		ON f.file_id = r.file_id 
		WHERE r.exclusion_type_id=3
	 	GROUP BY r.source_id,r.session_id,r.file_id,f.nb_marches,f.nb_concessions
	 	ORDER BY r.session_id
	) r
	GROUP BY r.source_id,r.session_id
	ORDER BY r.session_id
) r
INNER JOIN decp_report.source s 
ON s.source_id = r.source_id
ORDER BY name;

SELECT * FROM decp_report.v_stats_all;

DROP VIEW decp_report.v_stats_global;

CREATE OR REPLACE VIEW decp_report.v_stats_global AS
SELECT session_id,
	(SELECT end_date FROM decp_report."session" si WHERE si.session_id = r.session_id) AS session_date,
	SUM(CASE WHEN source_id=1 THEN nb_records ELSE NULL END) AS nb_records_dematis,
	SUM(CASE WHEN source_id=1 THEN nb_errors ELSE NULL END) AS nb_errors_dematis,
	100 * SUM(CASE WHEN source_id=1 THEN nb_errors ELSE NULL END) /
	COALESCE (SUM(CASE WHEN source_id=1 THEN nb_records ELSE NULL END),NULL) AS per_errors_dematis,
	SUM(CASE WHEN source_id=310 THEN nb_records ELSE NULL END) AS nb_records_pes,
	SUM(CASE WHEN source_id=310 THEN nb_errors ELSE NULL END) AS nb_errors_pes,
	100 * SUM(CASE WHEN source_id=310 THEN nb_errors ELSE NULL END) / 
	COALESCE (SUM(CASE WHEN source_id=310 THEN nb_records ELSE NULL END),NULL) AS per_errors_pes
FROM (
	SELECT s.name,s.source_id,r.session_id,r.nb_errors,r.nb_records
	FROM (
		SELECT r.source_id,r.session_id,sum(DISTINCT file_id) AS nb_files,sum(nb_error) AS nb_errors, sum(nb_marches) + sum(nb_concessions) AS nb_records
		FROM (
		 	SELECT r.source_id,r.session_id,r.file_id,count(DISTINCT r.position) AS nb_error,f.nb_marches, f.nb_concessions
		 	FROM decp_report.report r
			INNER JOIN decp_report.file f 
			ON f.file_id = r.file_id 
			WHERE r.exclusion_type_id=3
		 	GROUP BY r.source_id,r.session_id,r.file_id,f.nb_marches,f.nb_concessions
		 	ORDER BY r.session_id
		) r
		GROUP BY r.source_id,r.session_id
		ORDER BY r.session_id
	) r
	INNER JOIN decp_report.source s 
	ON s.source_id = r.source_id
	ORDER BY name
) r
GROUP BY session_id,session_date
ORDER BY session_date;

SELECT * FROM decp_report.v_stats_global;

