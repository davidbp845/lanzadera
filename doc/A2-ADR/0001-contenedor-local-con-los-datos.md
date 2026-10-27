# 0001 — Repo contenedor solo local con los datos; el código y la documentación, submódulo

## Contexto

home era un único repo con `app.py`, `enlaces.csv` y el registro de proyectos escrito como constante dentro de `app.py`. Los proyectos hermanos (`movimientos`, `namesyncia`, `emailmanage`) separan los datos del código con un contenedor local y un submódulo, y comparten metodología y forma de trabajar. Los datos de home no son sensibles como los de esos proyectos, pero sí personales (qué enlaces se usan, qué proyectos hay y dónde) y cambian por uso, no por desarrollo.

## Decisión

Mismo esqueleto que los hermanos:

```
home/                      ← repo CONTENEDOR, solo local (sin remoto, hook pre-push que bloquea)
├── README.md, CLAUDE.md, .claude/
├── datos/                 # proyectos.toml y enlaces.csv, versionados solo aquí
└── home/                  ← SUBMÓDULO: github.com/davidbp845/home (privado)
    ├── README.md, doc/, app.py, config/, tests/ con datos ficticios
    └── venv/              # fuera de git
```

- El submódulo contiene todo lo publicable. Clonado solo, es un proyecto completo (sin datos): los tests usan `tests/fixtures/`.
- El contenedor versiona `datos/` y el puntero al submódulo. No tiene remoto, y `.git/hooks/pre-push` rechaza cualquier push.
- `config/paths.py:datos()` resuelve la carpeta: `HOME_LAUNCHER_DATOS` si existe y, si no, `../datos` respecto a la raíz del submódulo.
- El `.gitignore` del submódulo ignora `/datos/`, `/enlaces.csv` y `/proyectos.toml` por si acaso.
- El historial anterior se queda en el contenedor; el submódulo empieza de cero.

## Alternativas descartadas

- **Un solo repo con `doc/` y `datos/`**: más simple, pero rompe la simetría con los hermanos (comandos, `CLAUDE.md`, copia de seguridad) y mezcla commits de uso con commits de desarrollo.
- **Datos como submódulo**: un submódulo necesita remoto, y los datos no deben tener ninguno.

## Consecuencias

- El código se commitea y se sube desde `home/home/`. El contenedor registra datos y, cuando interese, el commit del submódulo en uso.
- `home-streamlit.service` apunta ahora a `home/home/` y a su `venv/`.
- La copia de seguridad incluye el contenedor y excluye el submódulo, que está en GitHub.

## Estado

Aceptada (2026-10-23).
