-- DROP SCHEMA decp;

CREATE SCHEMA decp AUTHORIZATION decp_install, decp_appli;

-- decp.s_concession definition

DROP SEQUENCE IF EXISTS decp.s_concession;

CREATE SEQUENCE decp.s_concession
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- decp.s_concession_doublon definition

DROP SEQUENCE IF EXISTS decp.s_concession_doublon;

CREATE SEQUENCE decp.s_concession_doublon
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- decp.s_file definition

DROP SEQUENCE IF EXISTS decp.s_file;

CREATE SEQUENCE decp.s_file
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- decp.s_marche definition

DROP SEQUENCE IF EXISTS decp.s_marche;

CREATE SEQUENCE decp.s_marche
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- decp.s_marche_doublon definition

DROP SEQUENCE IF EXISTS decp.s_marche_doublon;

CREATE SEQUENCE decp.s_marche_doublon
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- decp.s_source definition

DROP SEQUENCE IF EXISTS decp.s_source;

CREATE SEQUENCE decp.s_source
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- decp.s_concession definition

DROP SEQUENCE IF EXISTS decp.s_concession;

CREATE SEQUENCE decp.s_concession
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- decp.s_session definition

DROP SEQUENCE IF EXISTS decp.s_session;

CREATE SEQUENCE decp.s_session
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- decp.concession_doublon definition

-- Drop table

DROP TABLE IF EXISTS decp.concession_doublon;

CREATE TABLE decp.concession_doublon (
	concession_doublon_id int4 DEFAULT nextval('decp.s_concession_doublon'::regclass) NOT NULL,
	concession_id int4 NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NOT NULL,
	id varchar(255) NULL,
	autorite_concedante varchar(255) NOT NULL,
	concessionnaires varchar(255) NOT NULL,
	date_debut_execution date NOT NULL,
	valeur_globale numeric NOT NULL,
	max_date varchar(20) NULL,
	objet varchar(1000) NULL,
	data_in jsonb NOT NULL,
	data_out jsonb NULL,
	data_augmente jsonb NULL,
	est_retenu bool NULL,
	date_creation timestamp,
	CONSTRAINT concession_doublon_pkey PRIMARY KEY (concession_doublon_id)
);


-- decp."source" definition

-- Drop table

-- DROP TABLE decp."source";

CREATE TABLE decp."source" (
	source_id int4 DEFAULT nextval('s_source'::regclass) NOT NULL,
	nom varchar(255) NOT NULL,
	alias varchar(255) NULL,
	dataset_id int4 NULL,
	status varchar(50) NULL,
	actif bool DEFAULT true NOT NULL,
	date_creation timestamp NULL,
	CONSTRAINT source_nom_key UNIQUE (nom),
	CONSTRAINT source_pkey PRIMARY KEY (source_id)
);



-- decp.file definition

-- Drop table

DROP TABLE IF EXISTS decp.file;

CREATE TABLE decp.file (
	file_id int4 DEFAULT nextval('decp.s_file'::regclass) NOT NULL,
	source_id int4 NOT NULL,
	nom varchar(255) NOT NULL,
	nb_marches int4 NULL,
	nb_concessions int4 NULL,
	date_creation timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT file_pkey PRIMARY KEY (file_id),
	CONSTRAINT file_source_id_nom_key UNIQUE (source_id, nom),
	CONSTRAINT file_source_id_fkey FOREIGN KEY (source_id) REFERENCES decp."source"(source_id) ON DELETE CASCADE
);


-- decp.concession definition

-- Drop table

DROP TABLE IF EXISTS decp.concession;

CREATE TABLE decp.concession (
	concession_id int4 DEFAULT nextval('decp.s_concession'::regclass) NOT NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NOT NULL,
	id varchar(255) NULL,
	autorite_concedante varchar(255) NOT NULL,
	concessionnaires varchar(255) NOT NULL,
	date_debut_execution date NOT NULL,
	valeur_globale numeric NOT NULL,
	max_date varchar(20) NULL,
	objet varchar(1000) NULL,
	data_in jsonb NOT NULL,
	data_out jsonb NULL,
	data_augmente jsonb NULL,
	est_retenu bool NULL,
	date_creation timestamp,
	CONSTRAINT concession_pkey PRIMARY KEY (concession_id),
	CONSTRAINT concession_unique__key UNIQUE (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale),
	CONSTRAINT concession_file_id_fkey FOREIGN KEY (file_id) REFERENCES decp.file(file_id) ON DELETE CASCADE,
	CONSTRAINT concession_source_id_fkey FOREIGN KEY (source_id) REFERENCES decp."source"(source_id) ON DELETE CASCADE
);

-- decp.marche definition

-- Drop table

DROP TABLE IF EXISTS decp.marche;

CREATE TABLE decp.marche (
	marche_id int4 DEFAULT nextval('decp.s_marche'::regclass) NOT NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NULL,
	id varchar(255) NOT NULL,
	acheteur varchar(255) NOT NULL,
	titulaires varchar(2048) NOT NULL,
	date_notification date NOT NULL,
	montant numeric NOT NULL,
	max_date varchar(20) NULL,
	objet varchar(1000) NULL,
	data_in jsonb NOT NULL,
	data_out jsonb NULL,
	data_augmente jsonb NULL,
	est_retenu bool NULL,
	date_creation timestamp,
	CONSTRAINT marche_pkey PRIMARY KEY (marche_id),
	CONSTRAINT marche_unique UNIQUE (id, acheteur, titulaires, date_notification, montant),
	CONSTRAINT marche_file_id_fkey FOREIGN KEY (file_id) REFERENCES decp.file(file_id) ON DELETE CASCADE,
	CONSTRAINT marche_source_id_fkey FOREIGN KEY (source_id) REFERENCES decp."source"(source_id) ON DELETE CASCADE
);


-- decp.marche_doublon definition

-- Drop table

DROP TABLE IF EXISTS decp.marche_doublon;

CREATE TABLE decp.marche_doublon (
	marche_doublon_id int4 DEFAULT nextval('decp.s_marche_doublon'::regclass) NOT NULL,
	marche_id int4 NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NULL,
	id varchar(255) NOT NULL,
	acheteur varchar(255) NOT NULL,
	titulaires varchar(2048) NOT NULL,
	date_notification date NOT NULL,
	montant numeric NOT NULL,
	max_date varchar(20) NULL,
	objet varchar(1000) NULL,
	data_in jsonb NOT NULL,
	data_out jsonb NULL,
	data_augmente jsonb NULL,
	est_retenu bool NULL,
	date_creation timestamp,
	CONSTRAINT marche_doublon_pkey PRIMARY KEY (marche_doublon_id),
	CONSTRAINT marche_file_id_fkey FOREIGN KEY (file_id) REFERENCES decp.file(file_id) ON DELETE CASCADE,
	CONSTRAINT marche_source_id_fkey FOREIGN KEY (source_id) REFERENCES decp."source"(source_id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS decp.session;

CREATE TABLE decp.session (
   session_id           INT8                 DEFAULT nextval('decp.s_session'::regclass) NOT NULL,
   name                 VARCHAR(256)         not null,
   message              VARCHAR(256)         null,
   begin_date           TIMESTAMP            not null,
   intermediate_date    TIMESTAMP            null,
   end_date             TIMESTAMP            null,
   CONSTRAINT pk_session primary key (session_id)
);
