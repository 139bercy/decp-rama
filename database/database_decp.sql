
-- public.s_concession definition

-- DROP SEQUENCE public.s_concession;

CREATE SEQUENCE public.s_concession
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- public.s_concession_doublon definition

-- DROP SEQUENCE public.s_concession_doublon;

CREATE SEQUENCE public.s_concession_doublon
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- public.s_file definition

-- DROP SEQUENCE public.s_file;

CREATE SEQUENCE public.s_file
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- public.s_marche definition

-- DROP SEQUENCE public.s_marche;

CREATE SEQUENCE public.s_marche
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- public.s_marche_doublon definition

-- DROP SEQUENCE public.s_marche_doublon;

CREATE SEQUENCE public.s_marche_doublon
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- public.s_source definition

-- DROP SEQUENCE public.s_source;

CREATE SEQUENCE public.s_source
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;


-- public.concession_doublon definition

-- Drop table

-- DROP TABLE public.concession_doublon;

CREATE TABLE public.concession_doublon (
	concession_doublon_id int4 DEFAULT nextval('s_concession_doublon'::regclass) NOT NULL,
	concession_id int4 NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NOT NULL,
	id varchar(255) NULL,
	autorite_concedante varchar(255) NOT NULL,
	concessionnaires varchar(255) NOT NULL,
	date_debut_execution date NOT NULL,
	valeur_globale numeric NOT NULL,
	max_date varchar(10) NULL,
	objet varchar(1000) NULL,
	data_in json NOT NULL,
	data_out json NULL,
	est_retenu bool NULL,
	CONSTRAINT concession_doublon_pkey PRIMARY KEY (concession_doublon_id)
);


-- public."source" definition

-- Drop table

-- DROP TABLE public."source";

CREATE TABLE public."source" (
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



-- public.file definition

-- Drop table

-- DROP TABLE public.file;

CREATE TABLE public.file (
	file_id int4 DEFAULT nextval('s_file'::regclass) NOT NULL,
	source_id int4 NOT NULL,
	nom varchar(255) NOT NULL,
	nb_marches int4 NULL,
	nb_concessions int4 NULL,
	date_creation timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT file_pkey PRIMARY KEY (file_id),
	CONSTRAINT file_source_id_nom_key UNIQUE (source_id, nom),
	CONSTRAINT file_source_id_fkey FOREIGN KEY (source_id) REFERENCES public."source"(source_id) ON DELETE CASCADE
);


-- public.marche definition

-- Drop table

-- DROP TABLE public.marche;

CREATE TABLE public.marche (
	marche_id int4 DEFAULT nextval('s_marche'::regclass) NOT NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NULL,
	id varchar(255) NOT NULL,
	acheteur varchar(255) NOT NULL,
	titulaires varchar(2048) NOT NULL,
	date_notification date NOT NULL,
	montant numeric NOT NULL,
	max_date varchar(10) NULL,
	objet varchar(1000) NULL,
	data_in json NOT NULL,
	data_out json NULL,
	est_retenu bool NULL,
	CONSTRAINT marche_pkey PRIMARY KEY (marche_id),
	CONSTRAINT marche_unique UNIQUE (id, acheteur, titulaires, date_notification, montant),
	CONSTRAINT marche_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.file(file_id) ON DELETE CASCADE,
	CONSTRAINT marche_source_id_fkey FOREIGN KEY (source_id) REFERENCES public."source"(source_id) ON DELETE CASCADE
);


-- public.marche_doublon definition

-- Drop table

-- DROP TABLE public.marche_doublon;

CREATE TABLE public.marche_doublon (
	marche_doublon_id int4 DEFAULT nextval('s_marche_doublon'::regclass) NOT NULL,
	marche_id int4 NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NULL,
	id varchar(255) NOT NULL,
	acheteur varchar(255) NOT NULL,
	titulaires varchar(2048) NOT NULL,
	date_notification date NOT NULL,
	montant numeric NOT NULL,
	max_date varchar(10) NULL,
	objet varchar(1000) NULL,
	data_in json NOT NULL,
	data_out json NULL,
	est_retenu bool NULL,
	CONSTRAINT marche_doublon_pkey PRIMARY KEY (marche_doublon_id),
	CONSTRAINT marche_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.file(file_id) ON DELETE CASCADE,
	CONSTRAINT marche_source_id_fkey FOREIGN KEY (source_id) REFERENCES public."source"(source_id) ON DELETE CASCADE
);


-- public.concession definition

-- Drop table

-- DROP TABLE public.concession;

CREATE TABLE public.concession (
	concession_id int4 DEFAULT nextval('s_concession'::regclass) NOT NULL,
	source_id int4 NOT NULL,
	file_id int4 NOT NULL,
	indx int4 NOT NULL,
	id varchar(255) NULL,
	autorite_concedante varchar(255) NOT NULL,
	concessionnaires varchar(255) NOT NULL,
	date_debut_execution date NOT NULL,
	valeur_globale numeric NOT NULL,
	max_date varchar(10) NULL,
	objet varchar(1000) NULL,
	data_in json NOT NULL,
	data_out json NULL,
	est_retenu bool NULL,
	CONSTRAINT concession_pkey PRIMARY KEY (concession_id),
	CONSTRAINT concession_unique__key UNIQUE (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale),
	CONSTRAINT concession_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.file(file_id) ON DELETE CASCADE,
	CONSTRAINT concession_source_id_fkey FOREIGN KEY (source_id) REFERENCES public."source"(source_id) ON DELETE CASCADE
);