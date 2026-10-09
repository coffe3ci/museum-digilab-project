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

    def get_object(self, obj_id):
        conn = get_connection()
        row = conn.execute(
            "SELECT id, title, description, image_path FROM objects WHERE id = ?",
            (obj_id,)
        ).fetchone()
        conn.close()
        return row

    def update_object(self, obj_id, title, description):
        conn = get_connection()
        conn.execute(
            "UPDATE objects SET title = ?, description = ? WHERE id = ?",
            (title, description, obj_id)
        )
        conn.commit()
        conn.close()

    def delete_object(self, obj_id):
        conn = get_connection()
        conn.execute("DELETE FROM objects WHERE id = ?", (obj_id,))
        conn.commit()
        conn.close()
