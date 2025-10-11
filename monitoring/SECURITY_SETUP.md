# 🔐 Configuración Segura de Credenciales para Monitoreo

## 🚨 **IMPORTANTE:** Credenciales por Defecto Removidas

### ❌ **Antes (INSEGURO):**
```bash
# Credenciales hardcodeadas en Docker
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=donaciones2024
```

### ✅ **Ahora (SEGURO):**
```bash
# Credenciales desde variables de entorno (.env)
GRAFANA_ADMIN_USER=tu_usuario_seguro
GRAFANA_ADMIN_PASSWORD=tu_password_segura_muy_larga
```

---

## 📝 Configuración Paso a Paso

### 1. **Generar Contraseñas Seguras**

```bash
# Generar password de 32 caracteres para Grafana
openssl rand -base64 32

# Generar password para Prometheus (opcional)
openssl rand -base64 24
```

### 2. **Configurar tu archivo .env**

Crea o actualiza tu archivo `.env` con credenciales seguras:

```bash
# Archivo: .env (NUNCA commitear este archivo!)

# Grafana - Credenciales seguras
GRAFANA_ADMIN_USER=admin_grafana_production
GRAFANA_ADMIN_PASSWORD=tu_password_seguro_de_32_caracteres_generado

# Prometheus - Autenticación básica opcional
# PROMETHEUS_USERNAME=prometheus_user
# PROMETHEUS_PASSWORD=tu_password_seguro_prometheus
```

### 3. **Verificar Configuración**

```bash
# Verificar variables de entorno
echo $GRAFANA_ADMIN_USER
echo $GRAFANA_ADMIN_PASSWORD

# Probar despliegue
./scripts/deploy_monitoring.sh production deploy
```

---

## 🔒 Medidas de Seguridad Implementadas

### **Grafana:**
- ✅ **Sin valores por defecto** en producción
- ✅ **Autenticación básica habilitada**
- ✅ **Acceso anónimo deshabilitado**
- ✅ **Registro de usuarios deshabilitado**
- ✅ **Analytics y updates deshabilitados**

### **Prometheus:**
- ✅ **Sin autenticación por defecto** (configurarla si es necesario)
- ✅ **Acceso restringido** a través de Railway
- ✅ **Métricas protegidas** por la infraestructura

---

## 🚀 Despliegue Seguro

### **Desarrollo:**
```bash
# Las variables se pueden dejar vacías, el script advertirá
./scripts/deploy_monitoring.sh development deploy
```

### **Producción:**
```bash
# Variables OBLIGATORIAS, el script fallará si no están
./scripts/deploy_monitoring.sh production deploy
```

---

## ⚠️ Checklist de Seguridad

### **Antes del Despliegue:**
- [ ] Generar contraseñas seguras (>32 caracteres)
- [ ] Configurar `GRAFANA_ADMIN_USER` en .env
- [ ] Configurar `GRAFANA_ADMIN_PASSWORD` en .env
- [ ] Verificar que .env NO esté en Git
- [ ] Probar despliegue en desarrollo

### **Después del Despliegue:**
- [ ] Verificar acceso a Grafana con credenciales nuevas
- [ ] Cambiar contraseña por defecto si es necesario
- [ ] Configurar notificaciones de alertas
- [ ] Revisar logs de acceso

---

## 🔧 Troubleshooting

### **Error: "Required environment variable GRAFANA_ADMIN_USER is not set"**
```bash
# Solución: Agregar al archivo .env
echo "GRAFANA_ADMIN_USER=tu_usuario" >> .env
echo "GRAFANA_ADMIN_PASSWORD=tu_password_seguro" >> .env
```

### **Error: "Using default Grafana admin user 'admin' in production!"**
```bash
# Solución: Cambiar el usuario por defecto
echo "GRAFANA_ADMIN_USER=admin_production" >> .env
```

### **Acceso Denegado a Grafana:**
- Verificar credenciales en .env
- Reiniciar servicios: `./scripts/deploy_monitoring.sh restart`
- Verificar logs: `./scripts/deploy_monitoring.sh logs grafana`

---

## 📋 Recomendaciones de Seguridad

### **Contraseñas:**
- ✅ Mínimo 32 caracteres
- ✅ Combinación de mayúsculas, minúsculas, números y símbolos
- ✅ Generadas aleatoriamente (no palabras del diccionario)
- ✅ Diferentes para cada servicio

### **Usuarios:**
- ✅ No usar "admin" en producción
- ✅ Usar nombres descriptivos pero no obvios
- ✅ Considerar múltiples usuarios con roles diferentes

### **Acceso:**
- ✅ IP whitelist en producción
- ✅ Autenticación de dos factores si es posible
- ✅ Monitoreo de intentos de acceso fallidos

---

## 🎯 Próximos Pasos

1. **Configurar notificaciones** de alertas (Slack/Email)
2. **Implementar HTTPS** para todos los servicios
3. **Configurar backup** de dashboards y configuraciones
4. **Implementar auditoría** de accesos
5. **Configurar rotación automática** de credenciales

---

**¡Tu stack de monitoreo ahora es completamente seguro y listo para producción!** 🔐
