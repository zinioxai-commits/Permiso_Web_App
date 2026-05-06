# PERMISOLOGÍA — Sistema de Gestión de Permisos

## Estructura del proyecto

```
permisologia/
├── app.py               ← Aplicación principal Streamlit
├── PERMISOLOGIA.db      ← Base de datos SQLite
├── requirements.txt     ← Dependencias
└── README.md
```

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Desplegar en Streamlit Community Cloud

1. Sube la carpeta a un repositorio GitHub (público o privado).
2. Ve a https://share.streamlit.io y conecta tu cuenta GitHub.
3. Selecciona el repositorio, branch `main` y archivo `app.py`.
4. Haz clic en **Deploy**.

> **Nota importante sobre la base de datos:**  
> SQLite funciona bien en local. En Streamlit Cloud el filesystem es
> efímero (se reinicia con cada deploy). Para producción considera
> migrar a **Supabase** (PostgreSQL gratuito) o usar
> `st.connection("sqlite", type=...)` con un volumen persistente.

## Secciones

| Sección | Tabla SQLite |
|---|---|
| 🏗️ Proyectos | `PROYECTOS` |
| 🌿 Permisos Ambientales | `PERMISOS_AMBIENTALES` |
| 🏺 Permisos Arqueológicos | `PERMISOS_ARQUEOLOGICOS` |
| ⚡ Permisos Eléctricos | `PERMISOS_ELECTRICOS` |
| 🏛️ Permisos Municipales | `PERMISOS_MUNICIPALES` |
| 🛣️ Permisos PROVIAS | `PERMISOS_PROVIAS` |
| 📜 Historial | `HISTORIAL_PERMISOS` |
