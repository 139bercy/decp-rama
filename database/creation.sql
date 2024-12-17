DROP VIEW IF EXISTS decp_report.v_stats_all;
DROP VIEW IF EXISTS decp_report.v_stats_global_by_session;
DROP VIEW IF EXISTS decp_report.v_nb_by_source_session;
DROP VIEW IF EXISTS decp_report.v_nb_by_files;
DROP VIEW IF EXISTS decp_report.v_files_errors;
DROP FUNCTION IF EXISTS decp_report.get_query_stats_global();

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
   content_type_id      INT8                 null,
   id_content           VARCHAR(64)          null,
   content              VARCHAR(4096)        null,
   creation_date        TIMESTAMP            not null,
   CONSTRAINT pk_report PRIMARY KEY (report_id)
);

COMMENT ON COLUMN decp_report.report.report_id IS 'Identifiant interne de l''enregistrement';

COMMENT ON COLUMN decp_report.report.source_id IS 'Flux d''ou provient l''enregistrement';

COMMENT ON COLUMN decp_report.report.exclusion_type_id IS 'Type de message ou d''erreur lie a l''enregistrement';

COMMENT ON COLUMN decp_report.report.file_id IS 'Nom du fichier d''ou provient l''enregistrement';

COMMENT ON COLUMN decp_report.report.path IS 'Chemin logique du noeud où s''est produit l''erreur';

COMMENT ON COLUMN decp_report.report.position IS 'Position de l''enregistrement dans fichier';

COMMENT ON COLUMN decp_report.report.message IS 'Message d''erreur';

COMMENT ON COLUMN decp_report.report.content IS 'Contenu de l''enregistrement';

COMMENT ON COLUMN decp_report.report.creation_date IS 'Date de creation de l''enregistrement ';

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
   code                 VARCHAR(64)          null,
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

ALTER TABLE decp_report.report
   ADD CONSTRAINT fk_report_exclusion_type FOREIGN KEY (exclusion_type_id)
      REFERENCES decp_report.exclusion_type (exclusion_type_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE decp_report.file
   ADD CONSTRAINT fk_file_source FOREIGN KEY (source_id)
      REFERENCES decp_report.source (source_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE decp_report.account
   ADD CONSTRAINT fk_account_source FOREIGN KEY (source_id)
      REFERENCES decp_report.source (source_id)
      ON DELETE RESTRICT ON UPDATE RESTRICT;

     
-- Vue agrégant le nombre de marchés, de concessions et d'erreurs  par fichier
DROP VIEW IF EXISTS decp_report.v_nb_by_files;

CREATE OR REPLACE VIEW decp_report.v_nb_by_files AS 
SELECT r.source_id,r.session_id,r.file_id,f.name,count(DISTINCT r.position) AS nb_error,f.nb_marches, f.nb_concessions
FROM decp_report.report r
INNER JOIN decp_report.file f 
ON f.file_id = r.file_id 
WHERE r.exclusion_type_id=1
GROUP BY r.source_id,r.session_id,r.file_id,f.name,f.nb_marches,f.nb_concessions
ORDER BY r.session_id;

--SELECT * FROM decp_report.v_nb_by_files; 

DROP VIEW IF EXISTS decp_report.v_files_errors;

CREATE OR REPLACE VIEW decp_report.v_files_errors AS 
SELECT r.source_id,r.session_id,r.file_id,f.name,count(DISTINCT r.position) AS nb_error,f.nb_marches, f.nb_concessions
FROM  decp_report.file f 
LEFT JOIN decp_report.report r
ON f.file_id = r.file_id 
--WHERE r.exclusion_type_id=1 OR r.exclusion_type_id IS NULL 
GROUP BY r.source_id,r.session_id,r.file_id,f.name,f.nb_marches,f.nb_concessions
ORDER BY r.session_id;

--SELECT * FROM decp_report.v_files_errors; 

-- Vue agrégant le nombre de marchés, de concessions et d'erreurs par session et par source
DROP VIEW IF EXISTS decp_report.v_nb_by_source_session;

CREATE OR REPLACE VIEW decp_report.v_nb_by_source_session AS 
SELECT r.source_id,r.session_id,count(DISTINCT file_id) AS nb_files,sum(nb_error) AS nb_errors, sum(nb_duplicate) AS nb_duplicates, sum(nb_marches) + sum(nb_concessions) AS nb_records
FROM (
 	SELECT r.source_id,r.session_id,r.file_id,
 		count(DISTINCT (CASE WHEN r.exclusion_type_id=1 THEN r.POSITION ELSE NULL END)) AS nb_error,
 		count(DISTINCT (CASE WHEN r.exclusion_type_id=2 THEN r.POSITION ELSE NULL END)) AS nb_duplicate,
 		f.nb_marches, f.nb_concessions
 	FROM decp_report.report r
	INNER JOIN decp_report.file f 
	ON f.file_id = r.file_id 
	GROUP BY r.source_id,r.session_id,r.file_id,f.nb_marches,f.nb_concessions
 	ORDER BY r.session_id
) r
GROUP BY r.source_id,r.session_id
ORDER BY r.session_id;

--SELECT * FROM decp_report.v_nb_by_source_session; 

DROP VIEW IF EXISTS decp_report.v_stats_global_by_session;

CREATE OR REPLACE VIEW decp_report.v_stats_global_by_session AS 
 SELECT s.begin_date,s.end_date, src."name", SUM(f.nb_marches) + SUM(f.nb_concessions) AS nb_records, SUM( nb_error) AS nb_errors
 FROM decp_report."session" s 
 INNER JOIN (
 	SELECT r.session_id,r.file_id,count(DISTINCT r.position) AS nb_error,f.nb_marches, f.nb_concessions
 	FROM decp_report.report r
	 INNER JOIN decp_report.file f 
	 ON f.file_id = r.file_id 
	WHERE r.exclusion_type_id=1
 	GROUP BY r.session_id,r.file_id,f.nb_marches ,f.nb_concessions
 ) r
 ON r.session_id = s.session_id 
 INNER JOIN decp_report.file f 
 ON f.file_id = r.file_id 
 INNER JOIN decp_report."source" src 
 ON src.source_id = f.source_id 
 GROUP BY s.session_id,s.name,s.begin_date,s.end_date, src."name";

--SELECT * FROM decp_report.v_stats_global_by_session;
	
DROP VIEW IF EXISTS decp_report.v_stats_all;

CREATE OR REPLACE VIEW decp_report.v_stats_all AS 
SELECT s.name,s.source_id,r.session_id,
	(SELECT end_date FROM decp_report."session" si WHERE si.session_id = r.session_id) AS session_date,
	r.nb_errors,
	r.nb_records--,
	--100 * r.nb_errors / COALESCE(r.nb_records,NULL) AS per_errors
FROM (
	SELECT r.source_id,r.session_id,sum(DISTINCT file_id) AS nb_files,sum(nb_error) AS nb_errors, sum(nb_marches) + sum(nb_concessions) AS nb_records
	FROM (
	 	SELECT r.source_id,r.session_id,r.file_id,
	 		count(DISTINCT (CASE WHEN r.exclusion_type_id=1 THEN r.POSITION ELSE NULL END)) AS nb_error,
	 		count(DISTINCT (CASE WHEN r.exclusion_type_id=2 THEN r.POSITION ELSE NULL END)) AS nb_duplicate,
	 		f.nb_marches, f.nb_concessions
	 	FROM decp_report.report r
		INNER JOIN decp_report.file f 
		ON f.file_id = r.file_id 
		GROUP BY r.source_id,r.session_id,r.file_id,f.nb_marches,f.nb_concessions
	 	ORDER BY r.session_id
	) r
	GROUP BY r.source_id,r.session_id
	ORDER BY r.session_id
) r
INNER JOIN decp_report.source s 
ON s.source_id = r.source_id
ORDER BY name;

--SELECT * FROM decp_report.v_stats_all;

CREATE OR REPLACE FUNCTION update_code_from_name()
RETURNS TRIGGER AS $$
BEGIN
    NEW.code := 
	CASE
        -- Vérifie si la chaîne contient au moins deux '_'
        WHEN POSITION('_' IN NEW.name) <> (LENGTH(NEW.name) - POSITION('_' IN REVERSE(NEW.name)))+1 THEN
            SUBSTRING(NEW.name,POSITION('_' IN NEW.name)+1, (LENGTH(NEW.name) - POSITION('_' IN REVERSE(NEW.name)))-POSITION('_' IN NEW.name))
        -- Vérifie si la chaîne contient au moins un '_'
        WHEN POSITION('_' IN NEW.name) > 0 THEN
            SUBSTRING(NEW.name FROM 1 FOR POSITION('_' IN NEW.name) - 1)
        ELSE
            NEW.name -- Si aucun '_', renvoie la chaîne complète
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER set_code_trigger
BEFORE INSERT OR UPDATE ON decp_report.source
FOR EACH ROW
EXECUTE FUNCTION update_code_from_name();

DROP FUNCTION IF EXISTS decp_report.get_query_stats_global();
CREATE OR REPLACE FUNCTION decp_report.get_query_stats_global()
RETURNS varchar AS $$
DECLARE
    sql_query TEXT;
BEGIN
    SELECT
    'SELECT ' ||
    ' (SELECT end_date FROM decp_report."session" si WHERE si.session_id = r.session_id) AS session_date,' ||
    string_agg(
        'MAX(CASE WHEN s.source_id = ' || s.source_id || ' THEN r.nb_records END) AS "' || s.code || '_nb_records"',
        ', '
    ) ||
    ','||
    string_agg(
        'MAX(CASE WHEN s.source_id = ' || s.source_id || ' THEN r.nb_errors END) AS "' || s.code || '_nb_errors"',
        ', '
    ) ||
    ' FROM decp_report.v_nb_by_source_session r' ||
    ' INNER JOIN decp_report.source s'||
	' ON s.source_id = r.source_id' ||
    ' GROUP BY r.session_id' ||
    ' ORDER BY r.session_id'
    INTO sql_query
	FROM decp_report.source s;

    return sql_query;
END $$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS decp_report.get_query_stats_global_per();
CREATE OR REPLACE FUNCTION decp_report.get_query_stats_global_per()
RETURNS varchar AS $$
DECLARE
    sql_query TEXT;
BEGIN
    SELECT
    'SELECT r.session_id, (SELECT s.message FROM decp_report.session s WHERE s.session_id = r.session_id) as etat,' ||
    ' (SELECT end_date FROM decp_report."session" si WHERE si.session_id = r.session_id) AS session_date,' ||
    string_agg(
        'MAX(CASE WHEN s.source_id = ' || s.source_id || ' THEN r.nb_records END) AS "' || s.code || '_nb_records"',
        ', '
    ) ||
    ','||
    string_agg(
        'MAX(CASE WHEN s.source_id = ' || s.source_id || ' THEN r.nb_errors END) AS "' || s.code || '_nb_errors"',
        ', '
    ) ||
    ','||
    string_agg(
        'MAX(CASE WHEN s.source_id = ' || s.source_id || ' THEN ((100*r.nb_errors) / COALESCE(r.nb_records,NULL)) END) AS "' || s.code || '_per_errors"',
        ', '
    ) ||
    ' FROM decp_report.v_nb_by_source_session r' ||
    ' INNER JOIN decp_report.source s'||
	' ON s.source_id = r.source_id' ||
    ' GROUP BY r.session_id' ||
    ' ORDER BY r.session_id'
    INTO sql_query
	FROM decp_report.source s;

    return sql_query;
END $$ LANGUAGE plpgsql;
