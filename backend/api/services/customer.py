"""
api/services/customer.py

Business logic สำหรับ Customer management
"""
from sqlalchemy.orm import Session


def generate_customer_code(branch_prefix: str, source_code: str, db: Session) -> str:
    """
    สร้าง customer code ตามรูปแบบ: BranchPrefix-SourceCode#Sequence
    เช่น: BPY-MKT001

    ใช้ PostgreSQL upsert (INSERT ... ON CONFLICT DO UPDATE) เพื่อ atomic increment
    รองรับ concurrent requests โดยไม่เกิด race condition
    """
    from api.models.customer import CustomerCodeCounter
    from api.models.branch import Branch
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    branch = db.query(Branch).filter(Branch.prefix == branch_prefix).first()
    branch_id = branch.id if branch else None

    # Atomic upsert: INSERT sequence=1, or UPDATE sequence += 1 on conflict
    stmt = (
        pg_insert(CustomerCodeCounter)
        .values(branch_id=branch_id, source_code=source_code, last_sequence=1)
        .on_conflict_do_update(
            index_elements=["branch_id", "source_code"],
            set_={"last_sequence": CustomerCodeCounter.last_sequence + 1},
        )
        .returning(CustomerCodeCounter.last_sequence)
    )
    result = db.execute(stmt)
    sequence = int(result.scalar())
    db.flush()

    # Format: BPY-MKT001 (ตาม requirement sec 5)
    seq_str = str(sequence).zfill(3)
    return f"{branch_prefix}-{source_code}{seq_str}"
