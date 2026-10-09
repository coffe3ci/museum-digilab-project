from database.database import get_connection


class ObjectManager:

    def get_all_objects(self):
        # Haalt alle objecten op uit de database
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, titel, beschrijving, afbeelding FROM objects ORDER BY id"
        ).fetchall()
        conn.close()
        return rows

    def add_object(self, titel, beschrijving, afbeelding=None):
        # Voegt een nieuw object toe aan de database
        conn = get_connection()
        conn.execute(
            "INSERT INTO objects (titel, beschrijving, afbeelding) VALUES (?, ?, ?)",
            (titel, beschrijving, afbeelding),
        )
        conn.commit()
        conn.close()

    def get_object(self, obj_id):
        # Haalt één specifiek object op basis van ID op
        conn = get_connection()
        row = conn.execute(
            "SELECT id, titel, beschrijving, afbeelding FROM objects WHERE id = ?",
            (obj_id,),
        ).fetchone()
        conn.close()
        return row

    def update_object(self, obj_id, titel, beschrijving, afbeelding=None):
        # Werkt een bestaand object bij in de database
        conn = get_connection()
        conn.execute(
            "UPDATE objects SET titel = ?, beschrijving = ?, afbeelding = ? WHERE id = ?",
            (titel, beschrijving, afbeelding, obj_id),
        )
        conn.commit()
        conn.close()

    def delete_object(self, obj_id):
        # Verwijdert een object uit de database
        conn = get_connection()
        conn.execute("DELETE FROM objects WHERE id = ?", (obj_id,))
        conn.commit()
        conn.close()