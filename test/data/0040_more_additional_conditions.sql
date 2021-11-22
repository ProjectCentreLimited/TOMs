/***
Add these as well

**/

INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (5, 'Suspended on Match Days');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (6, 'Bus parking on Match Days only');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (7, 'except Match Days');

INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (8, 'except taxis');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (9, 'vehicles > 3 tonnes');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (10, 'except vehicles over 55ft (17m) long and/or 9''-6" (2.9m) wide');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (11, 'school term time only');

INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (12, 'Community Hall vehicles only');

SELECT pg_catalog.setval('"toms_lookups"."AdditionalConditionTypes_Code_seq"', 1, false);

INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (13, 'No Stopping 7.00am-7.00pm;Except 7.00am-4.00pm;Loading max 20 min;Disabled max 3 hours');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (14, 'No Stopping 7.00am-7.00pm;Except 7.00am-4.00pm');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (15, 'No Stopping 7.00am-7.00pm;Except 10.00am-7.00pm');

INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (16, 'Resident Doctor and permit holders only');
INSERT INTO "toms_lookups"."AdditionalConditionTypes" ("Code", "Description") VALUES (17, 'except Ambulances');