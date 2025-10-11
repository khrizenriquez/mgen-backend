# 🏗️ Donations Guatemala - Monitoring Stack

Stack completo de monitoreo y observabilidad para el sistema de donaciones de Guatemala usando **Prometheus**, **Grafana**, **Loki** y **Promtail**.

## 🎯 ¿Qué Soluciona?

### ❌ **Problemas Anteriores:**
- ❌ **Logs no centralizados** - Dificultad para interpretar logs de producción
- ❌ **Sin métricas de negocio** - Falta visibilidad de KPIs importantes
- ❌ **No hay dashboards** - Dificultad para monitorear el sistema
- ❌ **Sin alertas automáticas** - Problemas no detectados proactivamente

### ✅ **Soluciones Implementadas:**
- ✅ **Logs centralizados** con Loki + Promtail
- ✅ **Métricas técnicas y de negocio** con Prometheus
- ✅ **Dashboards pre-configurados** en Grafana
- ✅ **Alertas automáticas** para problemas críticos
- ✅ **Funciona en desarrollo y producción**

---

## 🚀 Inicio Rápido

### Opción 1: Despliegue Automático (Recomendado)

```bash
# Para desarrollo
./scripts/deploy_monitoring.sh development deploy

# Para producción
./scripts/deploy_monitoring.sh production deploy
```

### Opción 2: Docker Compose Manual

```bash
# Desarrolllo
docker-compose -f docker-compose.railway.yml up -d

# Producción
docker-compose -f docker-compose.railway.yml up -d --build
```

---

## 📊 Servicios Incluidos

| Servicio | Puerto | Descripción | Estado |
|----------|--------|-------------|---------|
| **Grafana** | `3000` | Dashboards y visualización | ✅ Listo |
| **Prometheus** | `9090` | Recolección de métricas | ✅ Listo |
| **Loki** | `3100` | Almacenamiento de logs | ✅ Listo |
| **Promtail** | - | Recolección de logs | ✅ Listo |

---

## 🔐 Credenciales de Acceso

### Desarrollo:
```
Grafana: http://localhost:3000
Usuario: Configurado en .env (o admin por defecto)
Contraseña: Configurada en .env (o donaciones2024 por defecto)
```

### Producción:
```
Grafana: [URL-de-Railway]:3000
Usuario: $GRAFANA_ADMIN_USER (OBLIGATORIO)
Contraseña: $GRAFANA_ADMIN_PASSWORD (OBLIGATORIO)
```

---

## 📈 Dashboards Disponibles

### 1. **Donaciones Guatemala - Overview** ⭐
**Métricas principales del sistema:**
- 📊 **Requests Rate** - Tasa de requests por endpoint
- 📈 **HTTP Status Codes** - Distribución de códigos de respuesta
- ⏱️ **Response Time (95th percentile)** - Latencia del 95%
- 🚨 **Error Rate** - Tasa de errores (>5% dispara alerta)
- 💾 **Database Connections** - Conexiones activas a BD
- 💰 **Donations Statistics** - Estadísticas de donaciones
- ⚡ **System Resources** - CPU y memoria

### 2. **System Metrics**
- Métricas del sistema operativo
- Uso de recursos
- Rendimiento de contenedores

### 3. **API Performance**
- Latencia por endpoint
- Throughput
- Error rates específicos

---

## 📊 Métricas Disponibles

### Métricas Técnicas (cada 15s):
```prometheus
# HTTP Metrics
donations_requests_total{method, endpoint, status_code}
donations_request_duration_seconds{method, endpoint}

# System Metrics
cpu_usage_percent
memory_usage_bytes
database_connections_active

# Business Metrics (cada 5min)
donation_total_amount
donation_count_total
donations_by_status{status}
```

### Endpoint de Métricas:
- **Técnicas:** `GET /metrics`
- **Negocio:** `GET /metrics/business`

---

## 🚨 Alertas Configuradas

### Alertas Críticas:
- 🔴 **High Error Rate** (>10% en 5min)
- 🔴 **Service Down** (API no responde)
- 🔴 **Database Issues** (sin conexiones activas)

### Alertas de Advertencia:
- 🟡 **High Latency** (>5s en 95th percentile)
- 🟡 **Failed Login Attempts** (>10 por minuto)

---

## 🔐 Configuración de Seguridad

### **IMPORTANTE:** Configurar Credenciales Seguras

**ANTES de desplegar, lee:** [`SECURITY_SETUP.md`](SECURITY_SETUP.md)

#### **Configuración Obligatoria en .env:**
```bash
# Producción - OBLIGATORIO
GRAFANA_ADMIN_USER=tu_usuario_seguro
GRAFANA_ADMIN_PASSWORD=tu_password_muy_seguro_32_chars

# Desarrollo - Opcional (tiene defaults)
# GRAFANA_ADMIN_USER=admin
# GRAFANA_ADMIN_PASSWORD=tu_password_seguro
```

#### **Generar Contraseñas Seguras:**
```bash
# Generar password segura de 32 caracteres
openssl rand -base64 32
```

---

## 🔧 Configuración por Entorno

### Desarrollo (`docker-compose.railway.yml`):
```yaml
# Servicios locales con configuración de desarrollo
- Prometheus: localhost:9090 (sin autenticación)
- Grafana: localhost:3000 (credenciales desde .env o defaults)
- Loki: localhost:3100 (sin autenticación)
```

### Producción (Railway):
```toml
# railway.toml - Múltiples servicios con credenciales seguras
[services.prometheus]
build = { dockerfilePath = "Dockerfile.monitoring" }

[services.grafana]
build = { dockerfilePath = "Dockerfile.monitoring" }
# Credenciales validadas desde variables de entorno

[services.loki]
build = { dockerfilePath = "Dockerfile.monitoring" }
```

---

## 🛠️ Gestión del Stack

### Comandos del Script de Despliegue:

```bash
# Desplegar
./scripts/deploy_monitoring.sh development deploy
./scripts/deploy_monitoring.sh production deploy

# Estado
./scripts/deploy_monitoring.sh status

# Logs
./scripts/deploy_monitoring.sh logs grafana
./scripts/deploy_monitoring.sh logs prometheus

# Reiniciar
./scripts/deploy_monitoring.sh restart

# Detener
./scripts/deploy_monitoring.sh stop
```

### Comandos Manuales:

```bash
# Ver logs de todos los servicios
docker-compose -f docker-compose.railway.yml logs -f

# Reiniciar un servicio específico
docker-compose -f docker-compose.railway.yml restart grafana

# Ver estado de servicios
docker-compose -f docker-compose.railway.yml ps

# Detener stack
docker-compose -f docker-compose.railway.yml down
```

---

## 📋 Logs y Monitoreo

### Recolección de Logs:
1. **Promtail** recolecta logs de contenedores marcados con `logging=promtail`
2. **Loki** almacena los logs de forma eficiente
3. **Grafana** permite explorar logs con queries

### Explorar Logs en Grafana:
1. Ir a **Explore** → **Loki**
2. Usar queries como:
   ```loki
   {service="donations-api"} |= "ERROR"
   {service="donations-api"} |= "user_id"
   ```

### Métricas en Prometheus:
- **Targets:** `http://localhost:9090/targets`
- **Query:** `http://localhost:9090/graph`
- **Status:** `http://localhost:9090/status`

---

## 🔧 Configuración Avanzada

### Personalizar Dashboards:
1. Editar archivos en `monitoring/grafana/dashboards/donations/`
2. El dashboard se recarga automáticamente cada 30s

### Agregar Nuevas Alertas:
1. Editar `monitoring/prometheus/alert_rules.yml`
2. Reiniciar Prometheus

### Configurar Nuevas Métricas:
1. Agregar métricas en `app/infrastructure/monitoring/metrics.py`
2. Usarlas en el código con `METRIC_NAME.labels(...).inc()`

---

## 🚀 Despliegue en Producción

### Variables de Entorno Requeridas:
```bash
# Grafana
GRAFANA_ADMIN_USER=tu_usuario
GRAFANA_ADMIN_PASSWORD=tu_password_segura

# Base de datos (Railway las proporciona)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### Proceso de Despliegue:
1. **Configurar variables** en Railway
2. **Ejecutar script:** `./scripts/deploy_monitoring.sh production deploy`
3. **Verificar servicios** con el script de status
4. **Acceder a Grafana** con las credenciales configuradas

---

## 📚 Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Donations     │    │   Prometheus    │    │    Grafana      │
│     API         │───▶│   (Metrics)     │───▶│  (Dashboards)   │
│                 │    │                 │    │                 │
│ /metrics        │    └─────────────────┘    │ - Overview      │
│ /metrics/business│                           │ - System        │
└─────────────────┘                            │ - API Perf      │
         │                                     └─────────────────┘
         ▼
┌─────────────────┐    ┌─────────────────┐
│   Promtail      │    │     Loki        │
│ (Log Collector) │───▶│  (Log Storage)  │
└─────────────────┘    └─────────────────┘
```

---

## 🎯 Beneficios Implementados

### ✅ **Centralización de Logs:**
- Todos los logs de aplicación en un solo lugar
- Búsqueda eficiente con queries de Loki
- Retención configurable

### ✅ **Métricas Completas:**
- **Técnicas:** Latencia, throughput, errores
- **Negocio:** Donaciones, conversiones, KPIs
- **Sistema:** CPU, memoria, conexiones

### ✅ **Alertas Proactivas:**
- Detección automática de problemas
- Notificaciones configurables
- Umbrales personalizables

### ✅ **Dashboards Listos:**
- No requiere configuración adicional
- Métricas críticas visibles inmediatamente
- Personalizable según necesidades

### ✅ **Multi-entorno:**
- **Desarrollo:** Configuración local completa
- **Producción:** Despliegue en Railway con múltiples servicios

---

## 🔍 Próximos Pasos

1. **Configurar notificaciones** (Slack, email) para alertas
2. **Agregar más dashboards** específicos por módulo
3. **Implementar métricas custom** para funcionalidades específicas
4. **Configurar retention policies** para logs y métricas
5. **Agregar distributed tracing** (OpenTelemetry)

---

**¡El stack de monitoreo está completamente funcional y listo para producción!** 🎉

