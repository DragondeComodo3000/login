# Demo de login, perfil y hook previo al push

Aplicación local con frontend HTML/CSS/JavaScript, backend HTTP en Python y base de datos SQLite. Se crea automáticamente con dos usuarios iniciales. No requiere instalar paquetes.

## Ejecutar

```bash
python app.py
```

Abre `http://127.0.0.1:8000`.

| Usuario | Correo | Contraseña |
| --- | --- | --- |
| Ana García | `ana@demo.local` | `AnaDemo123!` |
| Luis Moreno | `luis@demo.local` | `LuisDemo123!` |

La base de datos se guarda en `data/login.sqlite3` y no se incluye en Git. Puedes cambiar la ruta con `LOGIN_DB` y el puerto con `PORT`.

## Ejercicio de depuración

El código contiene **cinco errores intencionales**. Las cinco pruebas están diseñadas para fallar inicialmente, una por cada regla incumplida. Ejecuta:

```bash
python -B -m unittest discover -s tests -v
```

Corrige `app.py` hasta obtener cinco pruebas aprobadas. No modifiques `tests/test_login.py` para resolverlas. Las pruebas cubren autenticación, perfil y sesiones.

GitHub Actions también ejecuta las cinco pruebas en cada push y pull request mediante `.github/workflows/tests.yml`. El workflow aparece en rojo inicialmente porque los cinco fallos son parte del ejercicio.

El archivo `hooks/pre-push` ejecuta esas pruebas y bloquea un `git push` cuando fallan. Puedes probarlo directamente con `python hooks/pre-push`. Si este directorio forma parte de un repositorio Git, actívalo desde `login` en Git Bash con:

```bash
git config core.hooksPath "$(pwd)/hooks"
```

En Windows, con Git Bash, este hook usa `python3` del entorno. Si Python solo está disponible como `python`, ajusta el intérprete de la primera línea antes de activarlo. Este hook pertenece a este proyecto; los hooks de `hooksLocal` verifican el proyecto `proyecto-demo` de ese otro directorio.

**Uso:** esta demo incluye credenciales públicas y fallos deliberados. Úsala solo en local para el ejercicio.
