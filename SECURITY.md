# 🔐 GUÍA DE SEGURIDAD - Sistema de Donaciones

## ⚠️ PROBLEMAS CRÍTICOS ENCONTRADOS

### 🚨 Credenciales Hardcodeadas en `docker-compose.yml`

**RIESGO: CRÍTICO** - Las siguientes credenciales están expuestas en el código:

```yaml
# ❌ INSEGURO - Cambiar inmediatamente
environment:
  POSTGRES_PASSWORD: postgres
  DATABASE_URL: postgresql://postgres:postgres@db:5432/donations_db
  RABBITMQ_DEFAULT_PASS: guest
  GF_SECURITY_ADMIN_PASSWORD: admin
```

## 🛡️ CORRECCIONES IMPLEMENTADAS

### ✅ Archivos `.gitignore` Completos

Se crearon archivos `.gitignore` comprehensivos para:
- **Backend**: Python, Docker, bases de datos, logs, certificados
- **Frontend**: Node.js, builds, variables de entorno, caches

### ✅ Archivos de Ejemplo de Variables de Entorno

- `mgen-backend/env.example`
- `mgen-frontend/env.example`

## 🔧 PASOS PARA ASEGURAR EL SISTEMA

### 1. Variables de Entorno Seguras

**Backend:**
```bash
cd mgen-backend
cp env.example .env
# Editar .env con valores reales y seguros
```

**Frontend:**
```bash
cd mgen-frontend  
cp env.example .env
# Editar .env con valores reales
```

### 2. Actualizar `docker-compose.yml`

Reemplazar credenciales hardcodeadas:

```yaml
# ✅ SEGURO
services:
  db:
    environment:
      POSTGRES_USER: \${POSTGRES_USER}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
      POSTGRES_DB: \${POSTGRES_DB}
  
  grafana:
    environment:
      - GF_SECURITY_ADMIN_USER=\${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=\${GRAFANA_ADMIN_PASSWORD}
```

### 3. Generar Contraseñas Seguras

```bash
# Generar contraseñas aleatorias
openssl rand -base64 32  # Para POSTGRES_PASSWORD
openssl rand -base64 32  # Para JWT_SECRET_KEY
openssl rand -base64 32  # Para SECRET_KEY
```

### 4. Configurar Variables de Entorno

**Desarrollo:**
```bash
# .env (nunca commitear)
POSTGRES_PASSWORD=tu_password_super_seguro_aqui
GRAFANA_ADMIN_PASSWORD=otro_password_seguro
SECRET_KEY=llave_secreta_de_32_caracteres_min
```

**Producción:**
- Usar variables de entorno del sistema
- Herramientas como HashiCorp Vault, AWS Secrets Manager
- Railway, Heroku Config Vars, etc.

## 📋 CHECKLIST DE SEGURIDAD

### ✅ Archivos y Configuración
- [x] `.gitignore` completo en ambos repos
- [x] `env.example` como plantilla
- [ ] Variables de entorno para `docker-compose.yml`
- [ ] Contraseñas por defecto cambiadas
- [ ] Secretos en variables de entorno

### ✅ Base de Datos
- [ ] Usuario diferente a `postgres`
- [ ] Contraseña fuerte (mín. 16 caracteres)
- [ ] Acceso restringido por IP
- [ ] Backups encriptados

### ✅ Aplicación
- [ ] JWT secret key seguro
- [ ] HTTPS en producción
- [ ] CORS configurado correctamente
- [ ] Rate limiting habilitado
- [ ] Logs sin información sensible

### ✅ Infraestructura
- [ ] Puertos no necesarios cerrados
- [ ] Firewall configurado
- [ ] Actualizaciones de seguridad aplicadas
- [ ] Monitoreo de accesos

## 🛠️ COMANDOS ÚTILES

### Revisar archivos sensibles
```bash
# Buscar posibles credenciales
grep -r -i "password\|secret\|key" --exclude-dir=node_modules .

# Verificar .gitignore
git status --ignored

# Ver archivos trackeados que no deberían estarlo
git ls-files | grep -E "\\.env|\\.key|\\.pem"
```

### Limpiar historial de Git (si es necesario)
```bash
# Solo si ya commiteaste secretos
git filter-branch --force --index-filter \\
  'git rm --cached --ignore-unmatch docker-compose.yml' \\
  --prune-empty --tag-name-filter cat -- --all
```

## 🔍 MONITOREO Y AUDITORÍA

### Herramientas Recomendadas
- **git-secrets**: Prevenir commits de secretos
- **truffleHog**: Buscar secretos en el historial
- **GitGuardian**: Escaneo automático de repositorios

### Configurar git-secrets
```bash
git secrets --install
git secrets --register-aws
git secrets --add '(password|secret|key).*=.*[\\'""]'
```

## 📞 CONTACTO DE SEGURIDAD

Si encuentras vulnerabilidades adicionales:
- 📧 Email: security@yomeuno.gt
- 🔐 Reporte confidencial por GitHub Security Advisories

## 🔄 ACTUALIZACIONES

**Última revisión:** $(date)
**Próxima auditoría:** En 3 meses

---

**⚠️ IMPORTANTE:** Implementar estas correcciones antes de desplegar a producción.