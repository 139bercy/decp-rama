drop table decp_report.report;

create table decp_report.report (
   report_id            INT8                 not null,
   step_id              INT8                 not null,
   source_id            INT8                 not null,
   file_id              INT8                 not null,
   exclusion_type_id    INT8                 not null,
   position             INT8                 null,
   message              VARCHAR(256)         null,
   error                VARCHAR(256)         null,
   path                 VARCHAR(256)         null,
   position             VARCHAR(256)         null,
   content              bytea                null,
   creation_date        TIMESTAMP            null,
   constraint pk_report primary key (report_id)
);

comment on column report.report_id is
'Identifiant interne de l''enregistrement';

comment on column report.source_id is
'Flux d''ou provient l''enregistrement';

comment on column report.exclusion_type_id is
'Type d''erreur lie a l''enregistrement';

comment on column report.file_id is
'Nom du fichier d''ou provient l''enregistrement';

comment on column report.path is
'Chemin logique du noeud où s''est produit l''erreur';

comment on column report.position is
'Position de l''enregistrement dans fichier';

comment on column report.message is
'Message d''erreur';

comment on column report.content is
'Contenu de l''enregistrement';

comment on column report.creation_date is
'Date de creation de l''enregistrement ';

create index fk_report_source_id on decp_report.report (source_id);

create index fk_report_file_id on decp_report.report (file_id);

create table decp_report.source (
   source_id            INT8                 not null,
   name                 VARCHAR(64)          null,
   creation_date        TIMESTAMP            null,
   constraint PK_ARTICLE_SOURCE primary key (source_id)
);

create table decp_report.step (
   step_id              INT8                 not null,
   name                 VARCHAR(64)          null,
   creation_date        TIMESTAMP            null,
   constraint PK_STEP_SOURCE primary key (step_id)
);

create table decp_report.file (
   file_id              INT8                 not null,
   name                 VARCHAR(64)          null,
   source_id            INT8                 null,
   creation_date        TIMESTAMP            null,
   constraint PK_FILE_SOURCE primary key (file_id)
);

create table decp_report.exclusion_type (
   exclusion_type_id    INT8                 not null,
   code                 VARCHAR(64)          null,
   name                 VARCHAR(64)          null,
   creation_date        TIMESTAMP            null,
   constraint PK_ORGANISATION primary key (exclusion_type_id)
);

alter table decp_report.report
   add constraint fk_report_source foreign key (source_id)
      references decp_report.source (source_id)
      on delete restrict on update restrict;

alter table decp_report.report
   add constraint fk_report_step foreign key (step_id)
      references decp_report.step (step_id)
      on delete restrict on update restrict;

alter table decp_report.report
   add constraint fk_report_file foreign key (file_id)
      references decp_report.file (file_id)
      on delete restrict on update restrict;

CREATE SEQUENCE decp_report.s_report;
CREATE SEQUENCE decp_report.s_step;
CREATE SEQUENCE decp_report.s_file;
CREATE SEQUENCE decp_report.s_source;
CREATE SEQUENCE decp_report.s_exclusion_type;