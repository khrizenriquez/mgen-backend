# Windows Setup Guide 🪟

Este documento contiene instrucciones específicas y soluciones para usuarios de Windows.

## 🚀 Configuración Inicial

### Prerrequisitos para Windows

1. **Docker Desktop** - Descargar e instalar desde [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Git for Windows** - Configurar line endings:
   ```bash
   git config --global core.autocrlf false
   git config --global core.eol lf
   ```
3. **Windows Subsystem for Linux (WSL2)** - Recomendado para mejor rendimiento
4. **Visual Studio Code** con extensiones:
   - Remote - WSL
   - Docker
   - Remote - Containers

## ⚠️ Problemas Conocidos y Soluciones

### 1. Line Endings (CRLF vs LF)

**Problema**: Windows usa CRLF, Linux usa LF

**Solución**: 
- Los archivos `.gitattributes` ya están configurados
- Clonar el repositorio DESPUÉS de configurar git:
  ```bash
  git clone <repo-url>
  ```

### 2. Rutas de Archivos

**Problema**: Windows usa `\` en lugar de `/`

**Solución**: Docker maneja esto automáticamente, pero en PowerShell usa:
```powershell
# En lugar de ./
docker-compose up -d

# Usar rutas completas si hay problemas
docker-compose -f ${PWD}/docker-compose.yml up -d
```

### 3. Rendimiento de Docker

**Problema**: Volumes montados son lentos en Windows

**Soluciones implementadas**:
- ✅ `init: true` en servicios para mejor manejo de procesos
- ✅ Volume exclusions para `node_modules`
- ✅ Health checks mejorados

**Recomendaciones adicionales**:
```bash
# Usar WSL2 en lugar de Hyper-V
# Configurar en Docker Desktop > Settings > General > "Use WSL 2 based engine"

# Clonar y trabajar desde WSL2
wsl
cd ~
git clone <repo-url>
```

### 4. Permisos de Archivos

**Problema**: Permisos diferentes entre Windows y contenedores Linux

**Solución**: Usar WSL2 o configurar Docker Desktop:
```bash
# En Docker Desktop > Settings > Resources > File Sharing
# Agregar las carpetas del proyecto
```

## 🛠️ Comandos Específicos para Windows

### PowerShell
```powershell
# Variables de entorno
$env:COMPOSE_CONVERT_WINDOWS_PATHS = 1

# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Detener servicios
docker-compose down
```

### Command Prompt
```cmd
# Variables de entorno
set COMPOSE_CONVERT_WINDOWS_PATHS=1

# Resto de comandos igual que PowerShell
```

### WSL2 (Recomendado)
```bash
# Comandos normales de Linux funcionan perfectamente
docker-compose up -d
docker-compose logs -f
```

## 🐛 Solución de Problemas

### Error: "standard_init_linux.go: exec user process caused: no such file or directory"

**Causa**: Line endings incorrectos (CRLF en lugar de LF)

**Solución**:
```bash
# Reconvertir line endings
git add --renormalize .
git commit -m "fix: normalize line endings"

# O reclonar después de configurar git
```

### Error: "docker: invalid reference format"

**Causa**: Espacios o caracteres especiales en rutas

**Solución**:
```powershell
# Mover proyecto a ruta sin espacios
# Ejemplo: C:\Users\usuario\Documents\proyectos\
```

### Error: Volume mount failed

**Causa**: Permisos o ruta no compartida

**Solución**:
1. Docker Desktop > Settings > Resources > File Sharing
2. Agregar carpeta del proyecto
3. Reiniciar Docker Desktop

## 📋 Checklist de Configuración

- [ ] Docker Desktop instalado y funcionando
- [ ] WSL2 habilitado (recomendado)
- [ ] Git configurado con line endings LF
- [ ] Carpeta del proyecto compartida en Docker Desktop
- [ ] Variables de entorno configuradas
- [ ] Repositorio clonado con configuración correcta

## 🔗 Enlaces Útiles

- [Docker Desktop para Windows](https://docs.docker.com/desktop/windows/)
- [WSL2 Installation Guide](https://docs.microsoft.com/en-us/windows/wsl/install)
- [Git Line Endings](https://docs.github.com/en/get-started/getting-started-with-git/configuring-git-to-handle-line-endings)

## 💡 Consejos de Productividad

1. **Usar WSL2**: Mejor rendimiento y compatibilidad completa
2. **VS Code + Remote WSL**: Desarrollo nativo en Linux desde Windows
3. **PowerShell Core**: Mejor que Command Prompt para desarrollo
4. **Docker Desktop Dashboard**: Interfaz gráfica para gestionar contenedores

---

Si encuentras otros problemas específicos de Windows, por favor documéntalos aquí.
