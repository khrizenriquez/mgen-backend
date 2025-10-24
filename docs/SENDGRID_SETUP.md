# SendGrid Email Service Setup

## ⚠️ Problema Identificado

El sistema de emails con SendGrid **NO estaba funcionando** porque faltaban las siguientes variables de entorno en el archivo `.env`:

```bash
SENDGRID_API_KEY      # ❌ No configurada
FROM_EMAIL            # ❌ No configurada  
FROM_NAME             # ❌ No configurada
FRONTEND_URL          # ❌ No configurada
LOG_LEVEL             # ❌ No configurada
```

### Síntomas:
- Warnings en los logs: `SendGrid API key not configured`
- Warnings en los logs: `FRONTEND_URL environment variable not set`
- Emails de recuperación de contraseña no funcionaban
- Emails de verificación no se enviaban

---

## ✅ Solución Implementada

### 1. Agregar variables al archivo `.env`

El archivo `.env` ahora incluye:

```bash
# Email Configuration (SendGrid - for password reset and verification)
# Get your API key from: https://app.sendgrid.com/settings/api_keys
SENDGRID_API_KEY=your-sendgrid-api-key-here
FROM_EMAIL=noreply@donacionesgt.org
FROM_NAME=Sistema de Donaciones

# Frontend & API URLs
FRONTEND_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000

# Logging Configuration
LOG_LEVEL=INFO
```

### 2. Recrear contenedores Docker

**IMPORTANTE:** `docker-compose restart` NO re-lee el archivo `.env`.

Debes usar:

```bash
docker-compose down
docker-compose up -d
```

---

## 🔧 Configuración Paso a Paso

### Paso 1: Obtener API Key de SendGrid

1. Crear cuenta en [SendGrid](https://signup.sendgrid.com/)
2. Ir a **Settings** → **API Keys**
3. Crear un **nuevo API Key** con permisos de **Full Access** o **Mail Send**
4. Copiar el API key (solo se muestra una vez)

### Paso 2: Configurar dominio verificado (Producción)

Para producción, necesitas verificar tu dominio:

1. Ir a **Settings** → **Sender Authentication**
2. Autenticar tu dominio (Ej: `masgenerosidad.org`)
3. Agregar los registros DNS (SPF, DKIM, CNAME)
4. Esperar verificación (puede tardar hasta 48 horas)

**Correos válidos después de verificación:**
- `noreply@masgenerosidad.org`
- `contacto@masgenerosidad.org`
- `donaciones@masgenerosidad.org`

### Paso 3: Actualizar `.env`

Editar el archivo `.env` en la raíz del proyecto backend:

```bash
# Desarrollo
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@donacionesgt.org  # Usar email verificado en producción
FROM_NAME=Sistema de Donaciones
FRONTEND_URL=http://localhost:5173

# Producción
SENDGRID_API_KEY=SG.tu-api-key-de-produccion
FROM_EMAIL=noreply@masgenerosidad.org
FROM_NAME=Más Generosidad Guatemala
FRONTEND_URL=https://app.masgenerosidad.org
```

### Paso 4: Recrear contenedores

```bash
cd mgen-backend
docker-compose down
docker-compose up -d
```

### Paso 5: Verificar configuración

```bash
# Verificar que no hay warnings
docker logs donations-api 2>&1 | grep -i "sendgrid"

# Si no hay output, está configurado correctamente ✅
```

---

## 🧪 Pruebas

### Test 1: Recuperación de contraseña

```bash
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@test.com"
  }'
```

**Respuesta esperada:**
```json
{
  "message": "If the email exists, you will receive password reset instructions"
}
```

**Email esperado:**
- Asunto: "Password Reset Request"
- Contiene link: `http://localhost:5173/reset-password?token=...`

### Test 2: Verificación de email

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "token": "tu-token-de-verificacion"
  }'
```

---

## 📊 Funcionalidades de Email

El sistema envía emails en los siguientes casos:

| Evento | Endpoint | Descripción |
|--------|----------|-------------|
| **Recuperación de contraseña** | `POST /api/v1/auth/forgot-password` | Envía link para resetear contraseña |
| **Verificación de email** | `POST /api/v1/auth/verify-email` | Confirma email del usuario |
| **Bienvenida** | Automático tras registro | Email de bienvenida |
| **Donación completada** | Automático tras pago | Recibo de donación |

---

## 🔍 Troubleshooting

### Problema: "SendGrid API key not configured"

**Causa:** Variable `SENDGRID_API_KEY` no está en `.env` o está vacía

**Solución:**
1. Agregar API key al `.env`
2. Recrear contenedores: `docker-compose down && docker-compose up -d`

### Problema: "FRONTEND_URL environment variable not set"

**Causa:** Variable `FRONTEND_URL` no está en `.env`

**Solución:**
1. Agregar `FRONTEND_URL=http://localhost:5173` al `.env`
2. Recrear contenedores

### Problema: "Unauthorized" en SendGrid

**Causa:** API key inválida o expirada

**Solución:**
1. Verificar que el API key esté activo en SendGrid dashboard
2. Crear un nuevo API key si es necesario
3. Actualizar `.env` con el nuevo key
4. Recrear contenedores

### Problema: Emails no llegan

**Causas posibles:**
1. **Dominio no verificado** (producción)
   - Verificar dominio en SendGrid dashboard
   
2. **Email en spam**
   - Configurar registros SPF/DKIM
   - Usar dominio verificado
   
3. **Rate limiting**
   - Plan gratuito: 100 emails/día
   - Upgrade a plan paid si es necesario

### Problema: Links en emails no funcionan

**Causa:** `FRONTEND_URL` incorrecta o no corresponde al ambiente

**Solución:**
```bash
# Desarrollo
FRONTEND_URL=http://localhost:5173

# Producción
FRONTEND_URL=https://app.masgenerosidad.org
```

---

## 🚀 Deployment

### Variables de Entorno en Railway/Producción

En Railway/Render/Heroku, configurar las siguientes variables:

```bash
SENDGRID_API_KEY=SG.tu-api-key-de-produccion
FROM_EMAIL=noreply@masgenerosidad.org
FROM_NAME=Más Generosidad Guatemala
FRONTEND_URL=https://app.masgenerosidad.org
LOG_LEVEL=INFO
```

### Verificación en producción

```bash
# Verificar logs
railway logs

# Buscar errores de SendGrid
railway logs | grep -i sendgrid

# Si no hay warnings, está configurado ✅
```

---

## 📝 Notas Importantes

1. **Nunca commitear el API key real al repositorio**
   - El archivo `.env` está en `.gitignore`
   - Usar variables de entorno en producción
   
2. **Usar email verificado en producción**
   - SendGrid requiere dominio verificado para emails transaccionales
   - Configurar SPF/DKIM para evitar spam
   
3. **Monitorear cuota de emails**
   - Plan gratuito: 100 emails/día
   - Upgrade según necesidad
   
4. **Recrear contenedores después de cambiar `.env`**
   - `docker-compose restart` NO re-lee `.env`
   - Usar `docker-compose down && docker-compose up -d`

---

## 📚 Referencias

- [SendGrid Documentation](https://docs.sendgrid.com/)
- [SendGrid API Keys](https://app.sendgrid.com/settings/api_keys)
- [Domain Authentication](https://docs.sendgrid.com/ui/account-and-settings/how-to-set-up-domain-authentication)
- [Email Service Implementation](../app/infrastructure/external/email_service.py)

---

## ✅ Checklist de Configuración

- [ ] Crear cuenta en SendGrid
- [ ] Obtener API Key
- [ ] Agregar `SENDGRID_API_KEY` al `.env`
- [ ] Agregar `FROM_EMAIL` al `.env`
- [ ] Agregar `FROM_NAME` al `.env`
- [ ] Agregar `FRONTEND_URL` al `.env`
- [ ] Agregar `LOG_LEVEL=INFO` al `.env`
- [ ] Recrear contenedores: `docker-compose down && docker-compose up -d`
- [ ] Verificar logs: Sin warnings de SendGrid ✅
- [ ] Probar recuperación de contraseña
- [ ] Verificar que email llega correctamente
- [ ] (Producción) Verificar dominio en SendGrid
- [ ] (Producción) Configurar registros DNS (SPF/DKIM)

---

**Estado actual:** ✅ Variables agregadas al `.env`, contenedores recreados, no hay warnings de SendGrid.

**Pendiente:** Configurar API key real de SendGrid para habilitar envío de emails.

