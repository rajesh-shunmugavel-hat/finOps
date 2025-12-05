
CREATE TABLE IF NOT EXISTS ebs_burst_balance (
    resource_id TEXT,
    instance_name TEXT,
    metric_name TEXT,
    timestamp TIMESTAMPTZ,
    value DOUBLE PRECISION
);
