import argparse
import asyncio

from app.db import SessionLocal
from app.models import AuditLog, CloudAccount
from sqlalchemy import delete, select


async def purge(apply: bool) -> int:
    async with SessionLocal() as session:
        accounts = list(
            (
                await session.scalars(
                    select(CloudAccount).where(CloudAccount.validation_mode == "local_mock")
                )
            ).all()
        )
        if not accounts:
            print("No local_mock cloud-account records found.")
            return 0
        account_ids = [account.id for account in accounts]
        if not apply:
            print(
                f"Found {len(account_ids)} local_mock account(s); "
                "no data was deleted."
            )
            print(
                "Re-run with --apply to permanently remove those account records "
                "and dependent scans/findings."
            )
            return len(account_ids)

        audit_logs = list(
            (
                await session.scalars(
                    select(AuditLog).where(AuditLog.event_type == "cloud_account.onboarded")
                )
            ).all()
        )
        for log in audit_logs:
            if log.details.get("account_id") in account_ids:
                await session.delete(log)
        await session.execute(delete(CloudAccount).where(CloudAccount.id.in_(account_ids)))
        await session.commit()
        print(
            f"Deleted {len(account_ids)} local_mock account(s), dependent scans/findings, "
            "and onboarding audit records."
        )
        print("No AWS API or AWS account was contacted.")
        return len(account_ids)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove CloudGuard's obsolete local simulator records from PostgreSQL."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Permanently delete local_mock rows. Without this flag, only report count.",
    )
    args = parser.parse_args()
    asyncio.run(purge(args.apply))


if __name__ == "__main__":
    main()
