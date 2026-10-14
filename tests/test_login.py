"""Cinco reglas que deben fallar hasta corregir los cinco errores del ejercicio."""

import tempfile
import unittest
from pathlib import Path

import app


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        app.init_db(self.db_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_email_no_distingue_mayusculas(self):
        user = app.authenticate("ANA@DEMO.LOCAL", "AnaDemo123!", self.db_path)
        self.assertIsNotNone(user)

    def test_password_incorrecta_es_rechazada(self):
        user = app.authenticate("ana@demo.local", "incorrecta", self.db_path)
        self.assertIsNone(user)

    def test_perfil_conserva_rol_admin(self):
        user = app.authenticate("ana@demo.local", "AnaDemo123!", self.db_path)
        token = app.create_session(user["id"], self.db_path)
        self.assertEqual(app.get_profile(token, self.db_path)["role"], "admin")

    def test_logout_invalida_sesion(self):
        user = app.authenticate("luis@demo.local", "LuisDemo123!", self.db_path)
        token = app.create_session(user["id"], self.db_path)
        app.logout(token, self.db_path)
        self.assertIsNone(app.get_profile(token, self.db_path))

    def test_sesion_expirada_es_rechazada(self):
        user = app.authenticate("luis@demo.local", "LuisDemo123!", self.db_path)
        token = app.create_session(user["id"], self.db_path)
        db = app.connect(self.db_path)
        try:
            with db:
                db.execute("UPDATE sessions SET expires_at = 1 WHERE token = ?", (token,))
        finally:
            db.close()
        self.assertIsNone(app.get_profile(token, self.db_path))
