"""
api/services/customer.py

Business logic สำหรับ Customer management
"""


def generate_customer_code(branch_prefix: str, source_code: str, sequence: int) -> str:
    """
    สร้าง customer code ตามรูปแบบ: BranchPrefix-SourceCode#Sequence
    เช่น: BKK-WEB#001

    - branch_prefix: prefix ของ branch เช่น BKK, PTY
    - source_code: รหัสแหล่งที่มา เช่น WEB, IGS, REF
    - sequence: ลำดับ customer ใน branch+source combination
    """
    # format sequence เป็น 3 หลัก เช่น 1 → 001
    seq_str = str(sequence).zfill(3)
    return f"{branch_prefix}-{source_code}#{seq_str}"
