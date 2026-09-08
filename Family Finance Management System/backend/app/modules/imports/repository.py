"""导入批次数据访问。"""

from sqlalchemy.orm import Session

from app.modules.imports.models import ImportBatch


class ImportBatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, batch: ImportBatch) -> ImportBatch:
        self.db.add(batch)
        self.db.flush()
        return batch

    def get_by_id(self, batch_id: int) -> ImportBatch | None:
        return self.db.get(ImportBatch, batch_id)