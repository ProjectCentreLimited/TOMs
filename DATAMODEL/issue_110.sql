-- Revision 1 tiles

update toms."MapGrid" set "CurrRevisionNr" = 1 where id = 984;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 984 and "ProposalID" != 0;

-- Revision 2 tiles

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1041;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1041 and "ProposalID" = 3;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1100;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1100 and "ProposalID" = 3;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1923;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1923 and "ProposalID" = 5;

update toms."MapGrid" set "CurrRevisionNr" = 2 where id = 1981;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1981 and "ProposalID" = 5;

-- Revision 3 tiles

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 1277;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1277 and "ProposalID" = 1;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 1290;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1290 and "ProposalID" = 1;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 1627;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1627 and "ProposalID" = 5;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 2039;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2039 and "ProposalID" = 4;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2039 and "ProposalID" = 5;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 3 where "TileNr" = 2039 and "ProposalID" = 6;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 2040;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2040 and "ProposalID" = 4;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2040 and "ProposalID" = 5;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 3 where "TileNr" = 2040 and "ProposalID" = 6;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 2098;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2098 and "ProposalID" = 4;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2098 and "ProposalID" = 5;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 3 where "TileNr" = 2098 and "ProposalID" = 6;

update toms."MapGrid" set "CurrRevisionNr" = 3 where id = 2158;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2158 and "ProposalID" = 4;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2158 and "ProposalID" = 5;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 3 where "TileNr" = 2158 and "ProposalID" = 6;

-- Revision 4 tiles

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 1042;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1042 and "ProposalID" = 3;

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 1215;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1215 and "ProposalID" = 1;

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 1336;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1336 and "ProposalID" = 1;

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 1628;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1628 and "ProposalID" = 5;

update toms."MapGrid" set "CurrRevisionNr" = 4 where id = 2100;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2100 and "ProposalID" = 4;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2100 and "ProposalID" = 5;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 4 where "TileNr" = 2100 and "ProposalID" = 6;

-- Revision 5 tiles

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1275;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1275 and "ProposalID" = 1;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1864;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1864 and "ProposalID" = 5;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 1867;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1867 and "ProposalID" = 1;

update toms."MapGrid" set "CurrRevisionNr" = 5 where id = 2099;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2099 and "ProposalID" = 4;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2099 and "ProposalID" = 5;
update toms."TilesInAcceptedProposals" set "RevisionNr" = 5 where "TileNr" = 2099 and "ProposalID" = 6;

-- Revision 6 tiles

update toms."MapGrid" set "CurrRevisionNr" = 6 where id = 1922;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 1922 and "ProposalID" = 5;

update toms."MapGrid" set "CurrRevisionNr" = 6 where id = 2102;
delete from toms."TilesInAcceptedProposals" where "TileNr" = 2102 and "ProposalID" = 1;

-- Verification

select tiap."TileNr", p."ProposalTitle", tiap."RevisionNr" from toms."TilesInAcceptedProposals" tiap
join toms."Proposals" p on p."ProposalID" = tiap."ProposalID"
where "TileNr" in (
'1922', '1923', '1290', '1041', '1042', '2098', '2099', '2100', '2102', '1336', '1981', '1215', '1864', '1867', '1100', '984', '1627', '1628', '2158', '2039', '2040', '1275', '1277'
)
order by "TileNr", "RevisionNr";
