"""
api/services/customer.py

Business logic สำหรับ Customer management
"""
from sqlalchemy.orm import Session


def generate_customer_code(branch_prefix: str, source_code: str, db: Session) -> str:
    """
    สร้าง customer code ตามรูปแบบ: BranchPrefix-SourceCode#Sequence
    เช่น: BPY-MKT#001

    ใช้ CustomerCodeCounter เพื่อ auto-increment sequence ต่อ branch+source combination
    """
    from api.models.customer import CustomerCodeCounter
    from api.models.branch import Branch

    branch = db.query(Branch).filter(Branch.prefix == branch_prefix).first()
    branch_id = branch.id if branch else 0

    counter = (
        db.query(CustomerCodeCounter)
        .filter_by(source_code=source_code, branch_id=branch_id)
        .with_for_update()
        .first()
    )

    if counter:
        counter.last_sequence += 1
        sequence = counter.last_sequence
    else:
        counter = CustomerCodeCounter(
            branch_id=branch_id,
            source_code=source_code,
            last_sequence=1,
        )
        db.add(counter)
        sequence = 1

    db.flush()

    # Format: BPY-MKT001 (ตาม requirement sec 5)
    seq_str = str(sequence).zfill(3)
    return f"{branch_prefix}-{source_code}{seq_str}"
