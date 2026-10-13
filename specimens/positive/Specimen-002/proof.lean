-- Specimen-002: positive control fixture (declared build exit=0, NOT locally built)
-- P0 状态脚本标本：编译通过与零未竟占位由 specimen.yaml machine 声明；
-- SchanuelAt 为白名单 known_domain 公理（HYPOTHESIS 层硬墙，对应 GAP-001）。
axiom SchanuelAt : True

theorem pi_pow_pi_transcendental : True := SchanuelAt
