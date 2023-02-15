-- Revision 0 tiles

drop table if exists zero_rev_tiles;
create table zero_rev_tiles (id int);
insert into zero_rev_tiles values
  (512), (513), (632), (633),
  (661), (692), (735), (845),
  (851), (853), (932), (1015),
  (1023), (1025), (1229), (1244),
  (1320), (1437), (1448), (1480),
  (1660), (1672), (1701), (1702),
  (1719), (1734), (1817), (1823),
  (1876), (1886), (1943), (2056),
  (2271), (2330), (2447), (2448),
  (2504), (2565), (2606), (2628),
  (2629), (2676), (2683), (2688),
  (2735), (2815), (2825), (2939),
  (2988), (3201), (3262), (3319),
  (3378), (3379), (3380), (911),
  (964), (972);

update toms."MapGrid" set "CurrRevisionNr" = 0 where id in (select id from zero_rev_tiles);
delete from toms."TilesInAcceptedProposals" where "TileNr" in (select id from zero_rev_tiles);
drop table zero_rev_tiles;

-- Revision 1 tiles

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 745;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 745 and "ProposalID" != 17;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 745;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 753;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 753 and "ProposalID" != 3;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 753;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 872;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 872 and "ProposalID" != 3;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 872;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 931;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 931 and "ProposalID" != 3;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 931;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 1501;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1501 and "ProposalID" != 91;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 1501;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 1684;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1684 and "ProposalID" != 5;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 1684;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 2568;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2568 and "ProposalID" != 17;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 2568;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 2749;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2749 and "ProposalID" != 79;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 2749;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 2750;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2750 and "ProposalID" != 22;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 1 where "TileNr" = 2750;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 1731;

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 422;

-- Revision 2 tiles

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1450;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1993;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 2385;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 2444;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1992;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1083;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1083 and "ProposalID" = 0;
update toms."TilesInAcceptedProposals" set "RevisionNr" = "RevisionNr" - 1 where "TileNr" = 1083;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1278;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1278 and "ProposalID" = 308;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 2 where "TileNr" = 1278 and "ProposalID" = 309;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1395;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1395 and "ProposalID" = 78;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 2 where "TileNr" = 1395 and "ProposalID" = 308;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 2506;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2506 and "ProposalID" = 0;
update toms."TilesInAcceptedProposals" set "RevisionNr" = "RevisionNr" - 1 where "TileNr" = 2506;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 2742;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2742 and "ProposalID" = 0;
update toms."TilesInAcceptedProposals" set "RevisionNr" = "RevisionNr" - 1 where "TileNr" = 2742;

-- Revision 3 tiles

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 1153;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 1393;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 1518;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 2207;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 2208;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 2153;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2153 and "ProposalID" = 242;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 3 where "TileNr" = 2153 and "ProposalID" = 295;

-- Revision 4 tiles

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 1036;

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 2037;

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 1512;
insert into toms."TilesInAcceptedProposals" ("ProposalID", "TileNr", "RevisionNr") values (309, 1512, 4);

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 1630;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1630 and "ProposalID" = 139;
update toms."TilesInAcceptedProposals" set "RevisionNr" = "RevisionNr" - 1 where "TileNr" = 1630 and "RevisionNr" > 3;

-- Revision 5 tiles

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 987;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 987 and "ProposalID" = 0;
update toms."TilesInAcceptedProposals" set "RevisionNr" = "RevisionNr" - 1 where "TileNr" = 987;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1094;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1223;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1336;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1341;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1341 and "ProposalID" = 308;
update toms."TilesInAcceptedProposals" set "RevisionNr" = "RevisionNr" - 1 where "TileNr" = 1341 and "RevisionNr" > 1;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1628;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1689;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 2160;

-- Revision 7 tiles

update toms."MapGrid" set "CurrRevisionNr" = 7 where id = 1220;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1220 and "ProposalID" = 242;

update toms."MapGrid" set "CurrRevisionNr" = 7 where id = 1222;

update toms."MapGrid" set "CurrRevisionNr" = 7 where id = 1922;

-- Revision 8 tiles

update toms."MapGrid" set "CurrRevisionNr" = 8 where id = 1863;
