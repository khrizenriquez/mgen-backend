# 🚂 Railway Database Configuration

## Problema Actual
El healthcheck falla porque faltan las variables de conexión a PostgreSQL.

## Solución: Opción 1 - Usar PostgreSQL de Railway (Recomendado)

### Paso 1: Agregar PostgreSQL al proyecto
1. Ve a tu proyecto en Railway
2. Click en **"New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway creará automáticamente estas variables:
   - `DATABASE_URL`
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`

### Paso 2: Conectar la base de datos al servicio
1. Ve a tu servicio API
2. En la pestaña **"Variables"**
3. Click en **"Reference"**
4. Selecciona el servicio PostgreSQL
5. Selecciona `DATABASE_URL` y las demás variables

### Paso 3: Re-deployar
El servicio se re-deployer automáticamente con las nuevas variables.

---

## Solución: Opción 2 - Usar PostgreSQL Externo

Si ya tienes una base de datos PostgreSQL externa (como en otro servidor), agrega estas variables manualmente en Railway:

### Variables Requeridas:

```bash
# Opción A: Usar DATABASE_URL (formato completo)
DATABASE_URL=postgresql://usuario:password@host:puerto/nombre_db

# Opción B: Usar variables individuales
PGHOST=tu-host-postgresql.com
PGPORT=5432
PGUSER=tu_usuario
PGPASSWORD=tu_password_seguro
PGDATABASE=donations_db

# Variables adicionales de PostgreSQL para la app
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_password_seguro
POSTGRES_DB=donations_db
```

### Cómo agregar en Railway:
1. Ve a tu servicio en Railway
2. Click en **"Variables"** tab
3. Click en **"New Variable"**
4. Agrega cada variable con su valor
5. Click en **"Deploy"**

---

## Verificación

Una vez configuradas las variables, el healthcheck `/health` debería responder correctamente.

### Probar localmente (simulando Railway):
```bash
export DATABASE_URL="postgresql://usuario:password@host:puerto/nombre_db"
export ENVIRONMENT="production"
python scripts/start_production.py
```

### Verificar en Railway:
```bash
curl https://tu-app.railway.app/health
```

Debería retornar:
```json
{
  "status": "healthy",
  "service": "donations-api",
  "version": "1.0.0"
}
```

---

## Troubleshooting

### Si el healthcheck sigue fallando:

1. **Verifica las variables están configuradas:**
   ```bash
   # En Railway, ve a Variables y verifica que estén todas
   ```

2. **Verifica la conexión a la base de datos:**
   - El host debe ser accesible desde Railway
   - El puerto debe estar abierto (usualmente 5432)
   - Las credenciales deben ser correctas

3. **Revisa los logs en Railway:**
   - Ve a la pestaña "Deployments"
   - Click en el deployment fallido
   - Revisa los logs para ver errores específicos

4. **Aumenta el healthcheck timeout:**
   En `railway.toml`:
   ```toml
   [deploy]
   healthcheckTimeout = 600  # Aumentar a 10 minutos
   ```

---

## Configuración Recomendada para Producción

```bash
# Base de datos
DATABASE_URL=postgresql://usuario:password@host:puerto/donations_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Seguridad
JWT_SECRET_KEY=tu_clave_secreta_muy_segura_aqui
CSRF_SECRET_KEY=otra_clave_secreta_para_csrf

# Frontend
FRONTEND_URL=https://sistemawebdonaciones.netlify.app
ALLOWED_ORIGINS=https://sistemawebdonaciones.netlify.app

# Email (Mailjet)
MAILJET_API_KEY=tu_api_key
MAILJET_API_SECRET=tu_api_secret
FROM_EMAIL=noreply@tu-dominio.com
FROM_NAME=Sistema de Donaciones

# Aplicación
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SERVICE_NAME=donations-api
VERSION=1.0.0
```

---

## Notas Importantes

⚠️ **NUNCA** commitees credenciales reales al repositorio
⚠️ Usa variables de entorno en Railway para todos los secrets
⚠️ La base de datos debe estar en la misma región que tu servicio para mejor latencia
✅ Railway PostgreSQL incluye backups automáticos
✅ Railway maneja automáticamente SSL/TLS para conexiones de BD

