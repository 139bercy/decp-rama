import requests
import hashlib
import logging
import json

# Script de test pour reordonner les resources un dataset 
# Renseigner le dataset_id et la liste des resource_id
# Note: utiliser le dcript api_call_get to get the resources list

dataset_id = "5cd57bf68b4c4179299eb0e9"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

data = [
        {
            "checksum": {
                "type": "sha1",
                "value": "ced9b3ec911270462f7fd6aa641a7737e8e80610"
            },
            "created_at": "2025-11-17T15:12:43.091000+00:00",
            "description": "Fichier des donn\u00e9es essentielles de la commande publique au format 2022 pour toutes les ann\u00e9es apr\u00e8s d\u00e9doublonnage ",
            "extras": {
                "analysis:check_id": 36718355,
                "analysis:last-modified-at": "2025-11-17T15:12:42+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "check:available": True,
                "check:date": "2025-11-17T15:12:47.649000",
                "check:headers:content-type": "application/json",
                "check:id": 36718355,
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 754169962,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "bd33e98f-f8e3-49ba-9f26-51c95fe57234",
            "internal": {
                "created_at_internal": "2025-11-17T15:12:43.091000+00:00",
                "last_modified_internal": "2025-11-17T15:18:38.714000+00:00"
            },
            "last_modified": "2025-11-17T15:18:38.714000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/bd33e98f-f8e3-49ba-9f26-51c95fe57234",
            "metrics": {
                "views": 100
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-global.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251117-151156/decp-global.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "77a9f8c2179112c28e85a15cb8932387ceb9efb1"
            },
            "created_at": "2025-06-17T11:57:46.244000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour l'ann\u00e9e 2025",
            "extras": {
                "analysis:check_id": 36528951,
                "analysis:error": "File too large to download",
                "analysis:last-modified-at": "2025-11-15T15:13:46+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "check:available": True,
                "check:date": "2025-06-17T12:01:10.555722+00:00",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 560096960,
            "filetype": "remote",
            "format": "json",
            "harvest": None,
            "id": "d00a6a5a-beef-442e-8aee-5867f47a87d0",
            "internal": {
                "created_at_internal": "2025-06-17T11:57:46.244000+00:00",
                "last_modified_internal": "2025-11-30T21:44:32.130000+00:00"
            },
            "last_modified": "2025-11-15T15:13:46+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/d00a6a5a-beef-442e-8aee-5867f47a87d0",
            "metrics": {
                "views": 864
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-204403/decp-2025.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "19f9294834b060906dffca3b3ec7b5746f50869b"
            },
            "created_at": "2025-11-10T23:38:24.137000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour novembre 2025 ",
            "extras": {
                "analysis:check_id": 36527704,
                "analysis:checksum": "cc6c5695d48b1d96e4c3807180edb2e7f1aa64af",
                "analysis:content-length": 28273499,
                "analysis:last-modified-at": "2025-11-15T14:48:59+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-11-10T23:38:26.146000",
                "check:headers:content-type": "application/json",
                "check:id": 36276871,
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 62215224,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "e0c3eb36-dd4f-4aa3-a0ec-b2736a903cd9",
            "internal": {
                "created_at_internal": "2025-11-10T23:38:24.137000+00:00",
                "last_modified_internal": "2025-11-30T20:18:15.169000+00:00"
            },
            "last_modified": "2025-11-30T20:18:15.169000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/e0c3eb36-dd4f-4aa3-a0ec-b2736a903cd9",
            "metrics": {
                "views": 299
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-11.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191811/decp-2025-11.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "2eea00a26eb44d35a314f1e5cbeec4087eb09a21"
            },
            "created_at": "2025-10-07T11:25:42.706000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour octobre 2025 ",
            "extras": {
                "analysis:check_id": 36527687,
                "analysis:checksum": "34a4c6ae79b584a4746a7d492bcc68a3f89a5443",
                "analysis:content-length": 74781596,
                "analysis:last-modified-at": "2025-11-15T14:48:43+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-10-07T11:25:45.472000",
                "check:headers:content-type": "application/json",
                "check:id": 34400920,
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 68103392,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "c21e27fd-2a01-4e0e-ac42-8468d5429ad7",
            "internal": {
                "created_at_internal": "2025-10-07T11:25:42.706000+00:00",
                "last_modified_internal": "2025-11-30T20:17:55.313000+00:00"
            },
            "last_modified": "2025-11-30T20:17:55.313000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/c21e27fd-2a01-4e0e-ac42-8468d5429ad7",
            "metrics": {
                "views": 591
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-10.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191751/decp-2025-10.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "43d7dbd0f5dca553f53113a12235884a5a881c13"
            },
            "created_at": "2025-09-01T08:17:52.186000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour septembre 2025 ",
            "extras": {
                "analysis:check_id": 36527674,
                "analysis:checksum": "63ff6d9bc873a8497ffe4118962b99312fe63eea",
                "analysis:content-length": 53987432,
                "analysis:last-modified-at": "2025-11-15T14:48:21+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-09-01T08:17:54.324000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 45126024,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "a5599c0b-e97e-4cbf-b4e5-8fe246816c59",
            "internal": {
                "created_at_internal": "2025-09-01T08:17:52.186000+00:00",
                "last_modified_internal": "2025-11-30T20:17:30.221000+00:00"
            },
            "last_modified": "2025-11-30T20:17:30.221000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/a5599c0b-e97e-4cbf-b4e5-8fe246816c59",
            "metrics": {
                "views": 359
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-09.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191727/decp-2025-09.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "7e58334db807d632143cf634171afd6b1a17dfb0"
            },
            "created_at": "2025-08-04T11:47:02.854000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour ao\u00fbt 2025 ",
            "extras": {
                "analysis:check_id": 36527658,
                "analysis:checksum": "2debc7f24276f3e31c8115bf920f8e0850eb7843",
                "analysis:content-length": 43451775,
                "analysis:last-modified-at": "2025-11-15T14:48:03+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-08-04T11:47:06.998000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 40832561,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "393f8099-0e3c-41b4-9f40-59ec3914807c",
            "internal": {
                "created_at_internal": "2025-08-04T11:47:02.854000+00:00",
                "last_modified_internal": "2025-11-30T20:17:03.049000+00:00"
            },
            "last_modified": "2025-11-30T20:17:03.049000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/393f8099-0e3c-41b4-9f40-59ec3914807c",
            "metrics": {
                "views": 456
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-08.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191700/decp-2025-08.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "fe9d67532ca791e978f50a34bb9fb30c1fec351e"
            },
            "created_at": "2025-07-01T09:31:11.608000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour juillet 2025 ",
            "extras": {
                "analysis:check_id": 36527642,
                "analysis:checksum": "21e3b09962e1e7529c9ba341c74dd29956a3c27f",
                "analysis:content-length": 57751364,
                "analysis:last-modified-at": "2025-11-15T14:47:45+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-07-01T09:31:18.260000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 92242350,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "bb90091c-f0cb-4a59-ad41-b0ab929aad93",
            "internal": {
                "created_at_internal": "2025-07-01T09:31:11.608000+00:00",
                "last_modified_internal": "2025-11-30T20:16:44.397000+00:00"
            },
            "last_modified": "2025-11-30T20:16:44.397000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/bb90091c-f0cb-4a59-ad41-b0ab929aad93",
            "metrics": {
                "views": 485
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-07.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191639/decp-2025-07.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "3be9b9f21922a1ab8048a387032e125d4b468e5c"
            },
            "created_at": "2025-06-02T08:38:40.107000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour juin 2025 ",
            "extras": {
                "analysis:check_id": 36527625,
                "analysis:checksum": "32542192e78993f41e20b63fd8a9476e3fa7de55",
                "analysis:content-length": 51235764,
                "analysis:last-modified-at": "2025-11-15T14:47:26+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-06-26T13:49:55.759000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 139944144,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "6e5f9e37-196c-4584-985d-a83dc212fca2",
            "internal": {
                "created_at_internal": "2025-06-02T08:38:40.107000+00:00",
                "last_modified_internal": "2025-11-30T20:16:08.053000+00:00"
            },
            "last_modified": "2025-11-30T20:16:08.053000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/6e5f9e37-196c-4584-985d-a83dc212fca2",
            "metrics": {
                "views": 834
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-06.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191601/decp-2025-06.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "b3aa6452f9c97832146aa96ebb05aefca9e051b0"
            },
            "created_at": "2025-05-05T07:41:20.702000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour mai 2025 ",
            "extras": {
                "analysis:check_id": 36527612,
                "analysis:checksum": "36b352b4eadc3d12f5feb9af7478bb8ada86e75c",
                "analysis:content-length": 38626952,
                "analysis:last-modified-at": "2025-11-15T14:47:08+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-06-26T13:48:56.869000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 57518803,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "50549a78-188d-42f4-b2fb-d099a0bb7faf",
            "internal": {
                "created_at_internal": "2025-05-05T07:41:20.702000+00:00",
                "last_modified_internal": "2025-11-30T20:15:15.813000+00:00"
            },
            "last_modified": "2025-11-30T20:15:15.813000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/50549a78-188d-42f4-b2fb-d099a0bb7faf",
            "metrics": {
                "views": 774
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-05.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191512/decp-2025-05.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "ab89ab992a9f99f838ba2ad11365847439cab505"
            },
            "created_at": "2025-04-01T10:50:48.096000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour avril 2025 ",
            "extras": {
                "analysis:check_id": 36527589,
                "analysis:checksum": "0eafd4e8ddebf3afac64f8c1f7a4c23d8432023e",
                "analysis:content-length": 48552396,
                "analysis:last-modified-at": "2025-11-15T14:46:49+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-06-26T13:48:50.267000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 121781915,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "2a81ee65-9533-4dc8-941e-47df1fb38fbb",
            "internal": {
                "created_at_internal": "2025-04-01T10:50:48.096000+00:00",
                "last_modified_internal": "2025-11-30T20:14:51.720000+00:00"
            },
            "last_modified": "2025-11-30T20:14:51.720000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/2a81ee65-9533-4dc8-941e-47df1fb38fbb",
            "metrics": {
                "views": 1004
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-04.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191445/decp-2025-04.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "fd10f141192b8346fdaa1a322d8ac94f73d142bc"
            },
            "created_at": "2025-03-03T17:45:49.540000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour mars 2025 ",
            "extras": {
                "analysis:check_id": 36527566,
                "analysis:checksum": "7fae64ad67ce4888774e532736bb421769abe11b",
                "analysis:content-length": 41102705,
                "analysis:last-modified-at": "2025-11-15T14:46:31+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-06-26T13:48:15.184000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 44842529,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "907fd525-a293-418a-b88f-df945236cf90",
            "internal": {
                "created_at_internal": "2025-03-03T17:45:49.540000+00:00",
                "last_modified_internal": "2025-11-30T20:14:01.452000+00:00"
            },
            "last_modified": "2025-11-30T20:14:01.452000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/907fd525-a293-418a-b88f-df945236cf90",
            "metrics": {
                "views": 1259
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-03.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191359/decp-2025-03.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "dd999c13bf89e40f41eaf241efeb2b1eec98bf5e"
            },
            "created_at": "2025-02-25T16:09:18.108000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour f\u00e9vrier 2025 ",
            "extras": {
                "analysis:check_id": 36527549,
                "analysis:checksum": "a21689dd1bc9738282362347d5bb5f13c0520a94",
                "analysis:content-length": 38126654,
                "analysis:last-modified-at": "2025-11-15T14:46:15+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": False,
                "check:date": "2025-11-16T00:11:19.490768+00:00",
                "check:error": "0, message='', url='https://www.data.gouv.fr/api/1/datasets/r/9a6f717c-4353-4435-a9f6-3b5a577ee9b4'",
                "check:id": 36544810,
                "check:status": 0,
                "check:timeout": False
            },
            "filesize": 41298591,
            "filetype": "remote",
            "format": "json",
            "harvest": None,
            "id": "9a6f717c-4353-4435-a9f6-3b5a577ee9b4",
            "internal": {
                "created_at_internal": "2025-02-25T16:09:18.108000+00:00",
                "last_modified_internal": "2025-11-30T20:13:40.228000+00:00"
            },
            "last_modified": "2025-11-15T14:46:15+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/9a6f717c-4353-4435-a9f6-3b5a577ee9b4",
            "metrics": {
                "views": 2026
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-02.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191338/decp-2025-02.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "ebf883401a0adea78208d342386e60714906c245"
            },
            "created_at": "2025-01-06T13:09:50.182000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour janvier 2025 ",
            "extras": {
                "analysis:check_id": 36527536,
                "analysis:checksum": "ed1bc70631a64af1e04011087e47f1e92eb69895",
                "analysis:content-length": 40933098,
                "analysis:last-modified-at": "2025-11-15T14:45:56+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-06-26T13:47:32.206000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 54295544,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "07478a30-2741-4d89-85bc-f47d72ad49bc",
            "internal": {
                "created_at_internal": "2025-01-06T13:09:50.182000+00:00",
                "last_modified_internal": "2025-11-30T20:13:23.080000+00:00"
            },
            "last_modified": "2025-11-30T20:13:23.080000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/07478a30-2741-4d89-85bc-f47d72ad49bc",
            "metrics": {
                "views": 1937
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2025-01.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191320/decp-2025-01.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "a2208293d9bf502be016bd6d611280c74df50368"
            },
            "created_at": "2024-11-15T16:11:40.079000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour l'ann\u00e9e 2024",
            "extras": {
                "analysis:check_id": 36527781,
                "analysis:error": "File too large to download",
                "analysis:last-modified-at": "2025-11-15T14:50:27+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "check:available": True,
                "check:date": "2024-11-15T16:15:36.360434+00:00",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 265003764,
            "filetype": "remote",
            "format": "json",
            "harvest": None,
            "id": "4fafdaff-b697-4494-9523-e9f56916fea8",
            "internal": {
                "created_at_internal": "2024-11-15T16:11:40.079000+00:00",
                "last_modified_internal": "2025-11-30T21:40:41.741000+00:00"
            },
            "last_modified": "2025-11-15T14:50:27+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/4fafdaff-b697-4494-9523-e9f56916fea8",
            "metrics": {
                "views": 2200
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-204028/decp-2024.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "2ea3e6b4432da76d8819a4338d48344ca3081bf4"
            },
            "created_at": "2024-12-02T17:34:03.985000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour d\u00e9cembre 2024 ",
            "extras": {
                "analysis:check_id": 36527516,
                "analysis:checksum": "99d7310055a22187148141d434b40381af9358f3",
                "analysis:content-length": 58756698,
                "analysis:last-modified-at": "2025-11-15T14:45:34+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2024-12-04T15:44:13.476000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 26363770,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "67614c69-f8b7-4df3-adf5-2b29c16643b1",
            "internal": {
                "created_at_internal": "2024-12-02T17:34:03.985000+00:00",
                "last_modified_internal": "2025-11-30T20:13:02.028000+00:00"
            },
            "last_modified": "2025-11-30T20:13:02.028000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/67614c69-f8b7-4df3-adf5-2b29c16643b1",
            "metrics": {
                "views": 1389
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-12.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191300/decp-2024-12.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "9c4f96c9b4384c284c64912f3cbf5c0c874ea349"
            },
            "created_at": "2024-11-06T17:00:10.479000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour novembre 2024 ",
            "extras": {
                "analysis:check_id": 36527500,
                "analysis:checksum": "91e0f97ca283e5e28ab40665f07af221912cf513",
                "analysis:content-length": 54522762,
                "analysis:last-modified-at": "2025-11-15T14:45:15+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2024-11-06T17:00:13.576000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 38942532,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "398e075e-5dc2-4797-86d7-21d04e39111f",
            "internal": {
                "created_at_internal": "2024-11-06T17:00:10.479000+00:00",
                "last_modified_internal": "2025-11-30T20:12:46.856000+00:00"
            },
            "last_modified": "2025-11-30T20:12:46.856000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/398e075e-5dc2-4797-86d7-21d04e39111f",
            "metrics": {
                "views": 1189
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-11.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191244/decp-2024-11.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "f1aa9532f8c4115dfddb99c26b9978b715f050f6"
            },
            "created_at": "2024-10-18T16:30:02.009000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour octobre 2024 ",
            "extras": {
                "analysis:check_id": 36527481,
                "analysis:checksum": "771aaaeeb4c08c246627ea267d94df481a863ecc",
                "analysis:content-length": 53207452,
                "analysis:last-modified-at": "2025-11-15T14:44:44+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2024-10-18T16:30:08.465000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 61628595,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "eddb0aaf-e0cb-4dd2-abb4-9971fa84106c",
            "internal": {
                "created_at_internal": "2024-10-18T16:30:02.009000+00:00",
                "last_modified_internal": "2025-11-30T20:12:27.876000+00:00"
            },
            "last_modified": "2025-11-30T20:12:27.876000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/eddb0aaf-e0cb-4dd2-abb4-9971fa84106c",
            "metrics": {
                "views": 1292
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-10.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191224/decp-2024-10.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "ca890f2d2af36d36e327d9899eef7f162f60cf7c"
            },
            "created_at": "2024-10-03T07:31:44.620000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour septembre 2024 ",
            "extras": {
                "analysis:check_id": 36527464,
                "analysis:checksum": "0bdd5f6b87ad4916dea71475410567e73c9209e6",
                "analysis:content-length": 40535558,
                "analysis:last-modified-at": "2025-11-15T14:44:25+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2024-10-03T07:31:49.178000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 194099831,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "700c7c9a-93f9-4ba1-a29d-830473ba78df",
            "internal": {
                "created_at_internal": "2024-10-03T07:31:44.620000+00:00",
                "last_modified_internal": "2025-11-30T20:12:07.852000+00:00"
            },
            "last_modified": "2025-11-30T20:12:07.852000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/700c7c9a-93f9-4ba1-a29d-830473ba78df",
            "metrics": {
                "views": 1247
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-09.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191157/decp-2024-09.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "aca61871fe733d5ffc2e5ed524c342e706f11f86"
            },
            "created_at": "2024-10-03T07:23:52.162000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour ao\u00fbt 2024 ",
            "extras": {
                "analysis:check_id": 36527449,
                "analysis:checksum": "01984fb18d7fd4250749a545a18c4050fec0bf91",
                "analysis:content-length": 48178893,
                "analysis:last-modified-at": "2025-11-15T14:44:09+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2024-10-03T07:23:56.101000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 2698596,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "766fd1b9-9d26-4b5f-bdaf-661e9cb7ef18",
            "internal": {
                "created_at_internal": "2024-10-03T07:23:52.162000+00:00",
                "last_modified_internal": "2025-11-30T20:11:20.016000+00:00"
            },
            "last_modified": "2025-11-30T20:11:20.016000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/766fd1b9-9d26-4b5f-bdaf-661e9cb7ef18",
            "metrics": {
                "views": 1189
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-08.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191119/decp-2024-08.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "2df1c76cbb7b6adb2270ebbc9a5172bc88cd705b"
            },
            "created_at": "2025-05-06T11:24:49.831000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour juillet 2024 ",
            "extras": {
                "analysis:check_id": 36527435,
                "analysis:checksum": "d71ff15e653bb26b3ef9db540f997f20d7175b11",
                "analysis:content-length": 46909768,
                "analysis:last-modified-at": "2025-11-15T14:43:50+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-05-06T11:24:51.677000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 3819585,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "0fbe30e6-b771-44c9-b7ca-8664d4b9ac63",
            "internal": {
                "created_at_internal": "2025-05-06T11:24:49.831000+00:00",
                "last_modified_internal": "2025-11-30T20:11:08.764000+00:00"
            },
            "last_modified": "2025-11-30T20:11:08.764000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/0fbe30e6-b771-44c9-b7ca-8664d4b9ac63",
            "metrics": {
                "views": 833
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-07.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191108/decp-2024-07.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "e0a11d1e8fa96d685621437103104a0c51c445d5"
            },
            "created_at": "2025-05-06T11:24:47.951000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour juin 2024 ",
            "extras": {
                "analysis:check_id": 36527414,
                "analysis:checksum": "9d0421bdb9dc862e00cd541bb5fc04f10027d4eb",
                "analysis:content-length": 35780686,
                "analysis:last-modified-at": "2025-11-15T14:43:25+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-05-06T11:24:51.660000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 239859,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "35dadd03-ef90-465f-bb0c-191bdffa3784",
            "internal": {
                "created_at_internal": "2025-05-06T11:24:47.951000+00:00",
                "last_modified_internal": "2025-11-30T20:10:41.484000+00:00"
            },
            "last_modified": "2025-11-30T20:10:41.484000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/35dadd03-ef90-465f-bb0c-191bdffa3784",
            "metrics": {
                "views": 633
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-06.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191041/decp-2024-06.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "b0df1046ecd943e9f5b1d27117109e43ec04029b"
            },
            "created_at": "2025-05-06T11:24:46.708000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour mai 2024 ",
            "extras": {
                "analysis:check_id": 36527400,
                "analysis:checksum": "e925f2211e66b52243efa20015864696813a95f3",
                "analysis:content-length": 27209379,
                "analysis:last-modified-at": "2025-11-15T14:43:09+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-05-06T11:24:51.657000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 205814,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "ec7265fe-a4b0-4fce-8137-0560f2ffddd9",
            "internal": {
                "created_at_internal": "2025-05-06T11:24:46.708000+00:00",
                "last_modified_internal": "2025-11-30T20:10:11.191000+00:00"
            },
            "last_modified": "2025-11-30T20:10:11.191000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/ec7265fe-a4b0-4fce-8137-0560f2ffddd9",
            "metrics": {
                "views": 635
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-05.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191011/decp-2024-05.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "248d31b8d846b837fb863f2de75579b4fee8a40f"
            },
            "created_at": "2025-05-06T11:24:45.079000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour avril 2024 ",
            "extras": {
                "analysis:check_id": 36527380,
                "analysis:checksum": "f3e20a596c9d34b18482d760e5bd4e9b40a0394b",
                "analysis:content-length": 29988287,
                "analysis:last-modified-at": "2025-11-15T14:42:54+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-05-06T11:24:47.410000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 255600,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "7c796b66-b80b-447b-9cf9-94009ff43e2d",
            "internal": {
                "created_at_internal": "2025-05-06T11:24:45.079000+00:00",
                "last_modified_internal": "2025-11-30T20:10:00.343000+00:00"
            },
            "last_modified": "2025-11-30T20:10:00.343000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/7c796b66-b80b-447b-9cf9-94009ff43e2d",
            "metrics": {
                "views": 668
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-04.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-191000/decp-2024-04.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "ae020babda636b75a3aa60aea3e7d6548748840b"
            },
            "created_at": "2025-05-06T11:24:43.328000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour mars 2024 ",
            "extras": {
                "analysis:check_id": 36527360,
                "analysis:checksum": "863310d175cceb2eec5133d36d5d9ce3efa4da5f",
                "analysis:content-length": 28073637,
                "analysis:last-modified-at": "2025-11-15T14:42:38+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-05-06T11:24:47.389000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 357825,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "68900ba2-2e8b-4644-96fa-b9c9e962f234",
            "internal": {
                "created_at_internal": "2025-05-06T11:24:43.328000+00:00",
                "last_modified_internal": "2025-11-30T20:09:38.475000+00:00"
            },
            "last_modified": "2025-11-30T20:09:38.475000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/68900ba2-2e8b-4644-96fa-b9c9e962f234",
            "metrics": {
                "views": 653
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-03.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-190938/decp-2024-03.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "536a7998f1d748fcd4328c03b39c009101bd6f11"
            },
            "created_at": "2025-05-06T11:24:41.572000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour f\u00e9vrier 2024 ",
            "extras": {
                "analysis:check_id": 36527341,
                "analysis:checksum": "2493df0a913381c2e48fa3720390ad6fd2bdb74c",
                "analysis:content-length": 26761006,
                "analysis:last-modified-at": "2025-11-15T14:42:23+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-05-06T11:24:43.336000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 501585,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "167b26c6-32d9-4da7-b8b3-8bcaf6d0ba28",
            "internal": {
                "created_at_internal": "2025-05-06T11:24:41.572000+00:00",
                "last_modified_internal": "2025-11-30T20:09:27.355000+00:00"
            },
            "last_modified": "2025-11-30T20:09:27.355000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/167b26c6-32d9-4da7-b8b3-8bcaf6d0ba28",
            "metrics": {
                "views": 639
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-02.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-190927/decp-2024-02.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "975f9ad157552034813bcab93e0cf076fbf90788"
            },
            "created_at": "2025-05-06T11:24:39.718000+00:00",
            "description": "Fichier cumulatif des donn\u00e9es essentielles de la commande publique pour janvier 2024 ",
            "extras": {
                "analysis:check_id": 36527328,
                "analysis:checksum": "68c76beb5efb24c72ca8ccfc52e15dfc4a56499e",
                "analysis:content-length": 19755593,
                "analysis:last-modified-at": "2025-11-15T14:42:08+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:date": "2025-05-06T11:24:43.326000",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 145015,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "7288bb31-5034-402c-b0b8-72030a9857aa",
            "internal": {
                "created_at_internal": "2025-05-06T11:24:39.718000+00:00",
                "last_modified_internal": "2025-11-30T20:09:16.239000+00:00"
            },
            "last_modified": "2025-11-30T20:09:16.239000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/7288bb31-5034-402c-b0b8-72030a9857aa",
            "metrics": {
                "views": 660
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2024-01.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-190916/decp-2024-01.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "499d2c42dd4279e2bc79c775b5fe6faa133280fd"
            },
            "created_at": "2024-08-05T13:09:00.622000+00:00",
            "description": None,
            "extras": {
                "analysis:checksum": "499d2c42dd4279e2bc79c775b5fe6faa133280fd",
                "analysis:content-length": 20595096,
                "analysis:error": "File too large to download",
                "analysis:last-modified-at": "2024-11-14T00:00:14+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "analysis:mime-type": "text/plain",
                "check:available": True,
                "check:count-availability": 2,
                "check:date": "2024-08-06T09:18:39.714000",
                "check:headers:content-type": "application/json",
                "check:status": 204,
                "check:timeout": False
            },
            "filesize": 20595096,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "59ba0edb-cf94-4bf1-a546-61f561553917",
            "internal": {
                "created_at_internal": "2024-08-05T13:09:00.622000+00:00",
                "last_modified_internal": "2024-11-14T01:00:14.380000+00:00"
            },
            "last_modified": "2024-11-14T01:00:14.380000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/59ba0edb-cf94-4bf1-a546-61f561553917",
            "metrics": {
                "views": 1352
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": None,
            "title": "decp-2022.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20241114-000009/decp-2022.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "d68dfada2d1baa80671ca4850c925f44e8348c56"
            },
            "created_at": "2019-05-10T17:08:00.244000+00:00",
            "description": "Ce fichier est mis \u00e0 jour quotidiennement.",
            "extras": {
                "analysis:check_id": 37103690,
                "analysis:error": "File too large to download",
                "analysis:last-modified-at": "2025-11-27T03:36:12+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "check:available": True,
                "check:count-availability": 2,
                "check:date": "2024-09-26T02:25:04.995527+00:00",
                "check:headers:content-type": "application/json",
                "check:status": 200,
                "check:timeout": False
            },
            "filesize": 943748598,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "16962018-5c31-4296-9454-5998585496d2",
            "internal": {
                "created_at_internal": "2019-05-10T17:08:00.244000+00:00",
                "last_modified_internal": "2025-11-30T04:31:44.471000+00:00"
            },
            "last_modified": "2025-11-30T04:31:44.471000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/16962018-5c31-4296-9454-5998585496d2",
            "metrics": {
                "views": 2422
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": {
                "name": None,
                "url": None,
                "version": None
            },
            "title": "decp-2019.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20251130-033053/decp-2019.json"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "15971e35880f50b1917cdcd77882348a507fdfa0"
            },
            "created_at": "2019-05-11T00:54:34.517000+00:00",
            "description": "Ce fichier est mis \u00e0 jour quotidiennement.",
            "extras": {
                "analysis:last-modified-at": "2023-02-07T04:36:54+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "check:available": True,
                "check:count-availability": 2,
                "check:date": "2023-12-19T09:31:12.362000",
                "check:headers:content-type": "text/xml",
                "check:status": 204,
                "check:timeout": False
            },
            "filesize": 646381097,
            "filetype": "file",
            "format": "xml",
            "harvest": None,
            "id": "17046b18-8921-486a-bc31-c9196d5c3e9c",
            "internal": {
                "created_at_internal": "2019-05-11T00:54:34.517000+00:00",
                "last_modified_internal": "2023-02-07T05:36:54.741000+00:00"
            },
            "last_modified": "2023-02-07T05:36:54.741000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/17046b18-8921-486a-bc31-c9196d5c3e9c",
            "metrics": {
                "views": 5223
            },
            "mime": "application/xml",
            "preview_url": None,
            "schema": {
                "name": None,
                "url": None,
                "version": None
            },
            "title": "decp.xml",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20230207-053545/decp.xml"
        },
        {
            "checksum": {
                "type": "sha1",
                "value": "20c4d8f66dc02111038a7c28df7899db3304ac9a"
            },
            "created_at": "2019-10-07T17:34:05.241000+00:00",
            "description": "Donn\u00e9es essentielles des march\u00e9s publics au format OCDS (https://standard.open-contracting.org/latest/fr/). Seules les donn\u00e9es d'attribution initiales sont pr\u00e9sentes dans ce fichier, pas les donn\u00e9es des attributions suite \u00e0 une modification. Moins d'1% des march\u00e9s publi\u00e9s a re\u00e7u une modification.\n\n### English\n\nEssential award data, in OCDS format (https://standard.open-contracting.org/latest/en/). Only initial award data is included in this file, it doesn't include award updates. Less than 1% of all published award have got an update.\n\nSince October 1st 2018, all French procuring entities must publish their award data on a procurement portal for contracts above 25k\u20ac (40k\u20ac since 2020).\n\nThis data has been collected on these portals and aggregated. Some portals are not harvested yet, the data is consequently not exhaustive.\n\nThis file is updated with new published awards every day.",
            "extras": {
                "analysis:last-modified-at": "2023-02-07T04:39:24+00:00",
                "analysis:last-modified-detection": "last-modified-header",
                "check:available": True,
                "check:count-availability": 2,
                "check:date": "2023-12-19T09:31:12.368000",
                "check:headers:content-type": "application/json",
                "check:status": 204,
                "check:timeout": False
            },
            "filesize": 1042362622,
            "filetype": "file",
            "format": "json",
            "harvest": None,
            "id": "68bd2001-3420-4d94-bc49-c90878df322c",
            "internal": {
                "created_at_internal": "2019-10-07T17:34:05.241000+00:00",
                "last_modified_internal": "2023-02-07T05:39:24.566000+00:00"
            },
            "last_modified": "2023-02-07T05:39:24.566000+00:00",
            "latest": "https://www.data.gouv.fr/api/1/datasets/r/68bd2001-3420-4d94-bc49-c90878df322c",
            "metrics": {
                "views": 3639
            },
            "mime": "application/json",
            "preview_url": None,
            "schema": {
                "name": None,
                "url": None,
                "version": None
            },
            "title": "decp.ocds.json",
            "type": "main",
            "url": "https://static.data.gouv.fr/resources/donnees-essentielles-de-la-commande-publique-fichiers-consolides/20230207-053829/decp.ocds.json"
        }
    ]

api_host = "https://www.data.gouv.fr/api/1"
url = f"{api_host}/datasets/{dataset_id}/resources/"

response = requests.put(url,headers=headers,json=data)

print(f"Statut de la requête : {response.status_code}")
#print("Réponse : ", response.json())