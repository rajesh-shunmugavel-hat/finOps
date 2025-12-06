import boto3
import os
from datetime import datetime, timedelta

PROFILE_NAME = "finops"
REGION = "us-east-1"

EXPORT_DIR = "export_sql"
os.makedirs(EXPORT_DIR, exist_ok=True)

EC2_METRICS = {
    "CPUUtilization": "ec2_cpu_utilization",
    "NetworkIn": "ec2_network_in",
    "NetworkOut": "ec2_network_out",
    "DiskReadBytes": "ec2_disk_read_bytes",
    "DiskWriteBytes": "ec2_disk_write_bytes",
    "DiskReadOps": "ec2_disk_read_ops",
    "DiskWriteOps": "ec2_disk_write_ops"
}

EBS_METRICS = {
    "VolumeReadBytes": "ebs_read_bytes",
    "VolumeWriteBytes": "ebs_write_bytes",
    "VolumeReadOps": "ebs_read_ops",
    "VolumeWriteOps": "ebs_write_ops",
    "VolumeIdleTime": "ebs_idle_time",
    "VolumeQueueLength": "ebs_queue_length",
    "BurstBalance": "ebs_burst_balance"
}

session = boto3.Session(profile_name=PROFILE_NAME)
ec2 = session.client("ec2", region_name=REGION)
cw = session.client("cloudwatch", region_name=REGION)

end = datetime.utcnow()
start = end - timedelta(days=60)

def init_sql_file(table):
    file = os.path.join(EXPORT_DIR, f"{table}.sql")
    with open(file, 'w') as f:
        f.write(f"""
CREATE TABLE IF NOT EXISTS {table} (
    resource_id TEXT,
    instance_name TEXT,
    metric_name TEXT,
    timestamp TIMESTAMPTZ,
    value DOUBLE PRECISION
);
""")
    return file

sql_files = {table: init_sql_file(table) for table in (list(EC2_METRICS.values()) + list(EBS_METRICS.values()))}

def append_sql(table, record):
    file = sql_files[table]
    with open(file, 'a') as f:
        f.write(f"INSERT INTO {table} VALUES {record};\n")

def get_instance_name(tags):
    if not tags:
        return None
    for t in tags:
        if t["Key"] == "Name":
            return t["Value"]
    return None

instances = ec2.describe_instances()

for reservation in instances["Reservations"]:
    for inst in reservation["Instances"]:
        instance_id = inst["InstanceId"]
        name = get_instance_name(inst.get("Tags"))
        print(f"\n➡ EC2 {name} ({instance_id})")

        # EC2 metrics
        for metric, table in EC2_METRICS.items():
            res = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName=metric,
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start,
                EndTime=end,
                Period=3600,
                Statistics=["Average"]
            )
            for dp in res["Datapoints"]:
                rec = (instance_id, name, metric, dp["Timestamp"].isoformat(), dp["Average"])
                append_sql(table, rec)

        # EBS per attached volumes
        for mapping in inst.get("BlockDeviceMappings", []):
            volume_id = mapping["Ebs"]["VolumeId"]
            print(f"  📦 Volume {volume_id}")

            for metric, table in EBS_METRICS.items():
                res = cw.get_metric_statistics(
                    Namespace="AWS/EBS",
                    MetricName=metric,
                    Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                    StartTime=start,
                    EndTime=end,
                    Period=3600,
                    Statistics=["Average"]
                )
                for dp in res["Datapoints"]:
                    rec = (volume_id, name, metric, dp["Timestamp"].isoformat(), dp["Average"])
                    append_sql(table, rec)

print("\n🎯 Metric Export Complete ✔")
print(f"📁 SQL Files Created in: {EXPORT_DIR}/")
