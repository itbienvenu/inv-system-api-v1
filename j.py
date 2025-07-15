from sqlalchemy import text
from database.database import SessionLocal  # or your DB session

db = SessionLocal()
try:
    db.execute(text("UPDATE sales SET payment_method = LOWER(payment_method);"))
    db.execute(text("UPDATE sales SET status = LOWER(status);"))
    db.commit()
    print("Enum fields normalized to lowercase.")
except Exception as e:
    db.rollback()
    print("Error:", e)
finally:
    db.close()
