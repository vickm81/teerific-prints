from app import db
from app.models import User

admin = User(username="admin")
admin.set_password("shopthemute")
db.session.add(admin)
db.session.commit()

