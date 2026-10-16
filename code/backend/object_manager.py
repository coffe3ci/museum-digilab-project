from database.database import get_connection


class ObjectManager:
    # Het id van een object is ook zijn nummer op de objectenwand (1, 2, 3, ...).
    # Daarom houden we de id's altijd netjes op volgorde, zonder gaten.

    def _verbind(self):
        # Maakt verbinding met de database en zorgt dat de id's op orde zijn
        conn = get_connection()
        self._zet_om_naar_id(conn)
        return conn

    def _zet_om_naar_id(self, conn):
        # Eenmalige omzetting: had de tabel nog een aparte kolom "nummer",
        # dan worden de id's in die volgorde gezet en verdwijnt de kolom.
        kolommen = [rij["name"] for rij in conn.execute("PRAGMA table_info(objects)")]
        if "nummer" in kolommen:
            self._hernummer(conn, "nummer, id")
            conn.execute("ALTER TABLE objects DROP COLUMN nummer")
            conn.commit()
            return

        # Zitten er gaten in de id's (bv. 2, 3, 4), dan worden ze 1, 2, 3
        aantal, hoogste = conn.execute("SELECT COUNT(*), MAX(id) FROM objects").fetchone()
        if (hoogste or 0) != aantal:
            self._hernummer(conn)
            conn.commit()

    def _verander_id(self, conn, oud_id, nieuw_id):
        # Geeft een object een ander id (ook in de tabel met extra afbeeldingen)
        conn.execute("UPDATE objects SET id = ? WHERE id = ?", (nieuw_id, oud_id))
        conn.execute(
            "UPDATE object_afbeeldingen SET object_id = ? WHERE object_id = ?",
            (nieuw_id, oud_id),
        )

    def _hernummer(self, conn, volgorde="id"):
        # Geeft alle objecten opnieuw de id's 1, 2, 3, ... zodat er geen gaten zijn
        ids = [rij["id"] for rij in conn.execute(f"SELECT id FROM objects ORDER BY {volgorde}")]

        # Eerst tijdelijk negatief maken, zodat twee objecten nooit hetzelfde id hebben
        for obj_id in ids:
            self._verander_id(conn, obj_id, -obj_id)
        for nr, obj_id in enumerate(ids, start=1):
            self._verander_id(conn, -obj_id, nr)

        # Zorgt dat een nieuw object het eerstvolgende id krijgt (aantal + 1)
        conn.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'objects'", (len(ids),))

    def get_all_objects(self):
        # Haalt alle objecten op uit de database, gesorteerd op id (= nummer)
        conn = self._verbind()
        rows = conn.execute(
            "SELECT id, titel, beschrijving, afbeelding FROM objects ORDER BY id"
        ).fetchall()
        conn.close()
        return rows

    def add_object(self, titel, beschrijving, afbeelding=None):
        # Voegt een nieuw object toe aan de database (achteraan) en geeft het nieuwe id terug
        conn = self._verbind()
        cursor = conn.execute(
            "INSERT INTO objects (titel, beschrijving, afbeelding) VALUES (?, ?, ?)",
            (titel, beschrijving, afbeelding),
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid

    def get_object(self, obj_id):
        # Haalt één specifiek object op basis van ID op
        conn = self._verbind()
        row = conn.execute(
            "SELECT id, titel, beschrijving, afbeelding FROM objects WHERE id = ?",
            (obj_id,),
        ).fetchone()
        conn.close()
        return row

    def update_object(self, obj_id, titel, beschrijving, afbeelding=None):
        # Werkt een bestaand object bij in de database
        conn = self._verbind()
        conn.execute(
            "UPDATE objects SET titel = ?, beschrijving = ?, afbeelding = ? WHERE id = ?",
            (titel, beschrijving, afbeelding, obj_id),
        )
        conn.commit()
        conn.close()

    def verander_nummer(self, obj_id, nieuw_nummer):
        # Geeft een object een nieuw id. Het object dat dat id had,
        # krijgt het oude id van dit object (de twee ruilen van plek).
        conn = self._verbind()
        aantal = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
        nieuw_nummer = max(1, min(nieuw_nummer, aantal))  # Tussen 1 en het aantal objecten

        if nieuw_nummer != obj_id:
            self._verander_id(conn, obj_id, -1)            # Tijdelijk opzij zetten
            self._verander_id(conn, nieuw_nummer, obj_id)  # Ander object krijgt het oude id
            self._verander_id(conn, -1, nieuw_nummer)      # Dit object krijgt het nieuwe id
            conn.commit()
        conn.close()

    def delete_object(self, obj_id):
        # Verwijdert een object uit de database en nummert de rest opnieuw
        conn = self._verbind()
        conn.execute("DELETE FROM object_afbeeldingen WHERE object_id = ?", (obj_id,))
        conn.execute("DELETE FROM objects WHERE id = ?", (obj_id,))
        self._hernummer(conn)
        conn.commit()
        conn.close()
