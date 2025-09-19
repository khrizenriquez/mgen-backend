# Database Validation Scripts

Este directorio contiene scripts para validar que tu base de datos, modelos SQLAlchemy y constraints estén correctamente configurados y sincronizados.

## 🚀 Script Principal

### `validate_all.py`
**Script maestro que ejecuta todas las validaciones**

```bash
cd mgen-backend/
python scripts/validate_all.py
```

Este script:
- ✅ Verifica que Docker esté ejecutándose
- ✅ Compara `schema.sql` con modelos SQLAlchemy
- ✅ Valida constraints de unicidad (reference_code, correlation_id)
- ✅ Valida manejo de request_id para logging
- ✅ Prueba prevención de duplicados en BD

## 📋 Scripts Individuales

### `validate_constraints.py`
Valida que las constraints de base de datos funcionen correctamente:

```bash
python scripts/validate_constraints.py
```

**Qué valida:**
- Estructura de tablas vs modelos SQLAlchemy
- Constraints UNIQUE en `reference_code` y `correlation_id`
- Constraints CHECK (ej: `amount_gtq > 0`)
- Foreign keys funcionando
- Prevención real de duplicados

### `compare_schema_models.py`
Compara `schema.sql` con los modelos SQLAlchemy:

```bash
python scripts/compare_schema_models.py
```

**Qué compara:**
- Nombres de tablas
- Nombres de columnas
- Tipos de datos
- Constraints de unicidad
- Campos nullable

### `validate_request_id.py`
Valida el manejo de request_id para logging y tracing:

```bash
python scripts/validate_request_id.py
```

**Qué valida:**
- LoggingMiddleware maneja request_id
- Configuración de logging incluye request_id
- Request IDs son únicos (UUID)
- Diferencia entre request_id (logging) y correlation_id (donaciones)

## 🔧 Prerequisitos

### 1. Docker ejecutándose
```bash
cd mgen-backend/
docker-compose up -d
```

### 2. Base de datos migrada
```bash
docker-compose exec api alembic upgrade head
```

### 3. Python environment
El script usa el entorno Python del proyecto backend.

## 📊 Interpretando Resultados

### ✅ Success
```
🎉 ALL VALIDATIONS PASSED!
✅ Your database schema, models, and constraints are properly configured
```

### ❌ Errors
Los errores se categorizan como:
- **CRITICAL ERRORS**: Deben corregirse (constraints faltantes, tipos incorrectos)
- **WARNINGS**: Deberían revisarse (diferencias menores, recomendaciones)

### Errores Comunes

#### 1. Constraint de Unicidad Faltante
```
❌ Missing UNIQUE constraint on reference_code
```
**Solución**: Agregar `UNIQUE` en schema.sql y modelo SQLAlchemy

#### 2. Tipo de Dato Incorrecto
```
❌ Column amount_gtq type mismatch: schema: NUMERIC, model: INTEGER
```
**Solución**: Corregir tipo en modelo SQLAlchemy

#### 3. Docker No Disponible
```
⚠️ Database container may not be running
💡 Run: docker-compose up -d
```
**Solución**: Iniciar Docker y contenedores

## 🎯 Tus Tareas Específicas

Basado en tus tareas:

### Tarea 298: "Bloquear inserción repetida"
```bash
# Este script valida que los constraints únicos bloqueen duplicados
python scripts/validate_constraints.py
```

### Tarea 297: "Validar request_id en DB"  
```bash
# Este script clarifica que request_id es para logging, no para BD
python scripts/validate_request_id.py
```

## 🔍 Qué Valida Cada Constraint

### Para Donaciones:
- **`reference_code`**: UNIQUE - código de referencia externo
- **`correlation_id`**: UNIQUE - ID de correlación de negocio  
- **`amount_gtq`**: CHECK > 0 - cantidad debe ser positiva
- **`donor_email`**: CHECK contiene '@' - validación básica email
- **`status_id`**: FK a status_catalog - estado válido

### Para Request Tracing:
- **`request_id`**: UUID único por request HTTP (solo logging)
- No se almacena en BD, se usa para tracing y logs

## 🚨 Comandos de Emergencia

### Recrear Base de Datos
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### Ver Logs de Validación
```bash
docker logs donations-api
```

### Verificar Manualmente
```bash
docker-compose exec db psql -U postgres -d donations -c "\d donation"
```

## 📝 Próximos Pasos

1. **Ejecutar validación completa**:
   ```bash
   python scripts/validate_all.py
   ```

2. **Corregir errores encontrados** en schema.sql o modelos

3. **Re-ejecutar validación** hasta que pase

4. **Implementar tests** para constraints en tu suite de pruebas

5. **Agregar validación a CI/CD** para prevenir regresiones

---

💡 **Tip**: Ejecuta `validate_all.py` después de cualquier cambio en schema.sql o modelos para asegurar sincronización.
