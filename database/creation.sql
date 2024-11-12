DROP SEQUENCE IF EXISTS decp_report.s_session;
DROP SEQUENCE IF EXISTS decp_report.s_report;
DROP SEQUENCE IF EXISTS decp_report.s_step;
DROP SEQUENCE IF EXISTS decp_report.s_file;
DROP SEQUENCE IF EXISTS decp_report.s_source;
DROP SEQUENCE IF EXISTS decp_report.s_exclusion_type;

CREATE SEQUENCE decp_report.s_session;
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
   error                VARCHAR(256)         null,
   path                 VARCHAR(256)         null,
   content              bytea                null,
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

