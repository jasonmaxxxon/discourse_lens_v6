import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not service_key:
    raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

# Prove which project we are hitting
host = url.split("//", 1)[-1].split("/", 1)[0]
print(f"[WIPE] SUPABASE_URL host = {host}")
print(f"[WIPE] SERVICE_ROLE_KEY prefix = {service_key[:12]}... (len={len(service_key)})")

sb = create_client(url, service_key)


def count_rows(table: str) -> int:
    # supabase-py supports count via select(..., count="exact")
    res = sb.table(table).select("id", count="exact").limit(1).execute()
    return int(res.count or 0)


def wipe_ops():
    before_items = count_rows("job_items")
    before_jobs = count_rows("job_batches")
    print(f"[WIPE] Before: job_items={before_items}, job_batches={before_jobs}")

    # Delete children first
    print("[WIPE] Deleting job_items...")
    del_items = sb.table("job_items").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print(f"[WIPE] job_items delete returned rows={len(del_items.data) if del_items.data else 0}")

    print("[WIPE] Deleting job_batches...")
    del_jobs = sb.table("job_batches").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print(f"[WIPE] job_batches delete returned rows={len(del_jobs.data) if del_jobs.data else 0}")

    after_items = count_rows("job_items")
    after_jobs = count_rows("job_batches")
    print(f"[WIPE] After: job_items={after_items}, job_batches={after_jobs}")

    print("✅ Ops tables wiped (or proven not wiping).")


if __name__ == "__main__":
    wipe_ops()
