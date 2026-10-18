-- Blog 22 — One Lakehouse, Three Clouds: The Multi-Cloud Finale
-- Exercise 2: the game-day replica check.
-- Requires: You can't rehearse three clouds from one Free Edition workspace — and this finale won't pretend otherwise. These exercises simulate the multi-cloud patterns with catalog naming and synthetic storage p

-- a replica you can't trust isn't a failover
SELECT table_name,
       primary_log_version, dr_log_version,
       (primary_log_version - dr_log_version) AS version_gap,
       heartbeat_age_min
FROM ops.replica_health
WHERE dr_log_version < primary_log_version OR heartbeat_age_min > 60;
-- Expected: exactly one row — gold.claims, version_gap 40. That's the drill finding the bug.
