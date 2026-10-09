from database.database import get_connection


class ObjectManager:

    def get_all_objects(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, title, description, image_path FROM objects ORDER BY id"
        ).fetchall()
        conn.close()
        return rows

    def add_object(self, title, description, image_path=None):
        conn = get_connection()
        conn.execute(
            "INSERT INTO objects (title, description, image_path) VALUES (?, ?, ?)",
            (title, description, image_path)
        )
        conn.commit()
        conn.close()
