# Mapa Web del Sistema (Manual Tecnico)

Fecha: 2026-04-28

## 1. Que es un Mapa Web

El Mapa Web (o sitemap funcional) es un diagrama que muestra:
- Que pantallas existen en la aplicacion.
- Como navega el usuario entre pantallas.
- Que rutas son publicas y cuales requieren autenticacion/rol.

No es un diagrama de base de datos ni de clases. Es un mapa de navegacion del front web con sus endpoints principales.

## 2. Alcance del mapa en este proyecto

Este mapa se construyo con base en las rutas reales de Flask (blueprints), por lo tanto refleja el sistema implementado.

## 3. Estructura general de navegacion

```mermaid
flowchart TD
  A[Inicio /] --> B[/auth/login]
  B --> C[/dashboard]
  C --> D[/mi-cuenta]

  C --> U[/usuarios]
  C --> CO[/conductores]
  C --> V[/vehiculos]
  C --> VI[/visitantes]
  C --> E[/espacios]
  C --> N[/novedades/gestion]
  C --> CA[/control-accesos]
  C --> R[/reportes]
  C --> Q[/consultas]
  C --> H[/horarios]
  C --> AR[/areas]
  C --> CH[/control-hardware]

  B --> FP[/auth/forgot-password]
  FP --> RP[/auth/reset-password/<token>]

  CH --> API1[/control-hardware/api/estado]
  CH --> API2[/control-hardware/api/comando]
  CH --> API3[/control-hardware/api/evento]
```

## 4. Mapa por modulo (rutas base)

| Modulo | Prefijo de ruta | Pantalla principal | Tipo |
|---|---|---|---|
| Main | / | /dashboard | Publica en /, protegida en /dashboard |
| Auth | /auth | /auth/login, /auth/register, /auth/forgot-password | Publico |
| Usuarios | /usuarios | /usuarios | Protegido (admin) |
| Conductores | /conductores | /conductores | Protegido |
| Vehiculos | /vehiculos | /vehiculos, /vehiculos/consultar | Protegido |
| Visitantes | /visitantes | /visitantes | Protegido |
| Espacios | /espacios | /espacios | Protegido |
| Novedades | /novedades | /novedades/gestion | Protegido |
| Control de accesos | /control-accesos | /control-accesos, /control-accesos/historial, /control-accesos/autorizacion | Protegido |
| Reportes | /reportes | /reportes, /reportes/modulo/<module_key> | Protegido |
| Consultas | /consultas | /consultas | Protegido |
| Horarios | /horarios | /horarios | Protegido (admin) |
| Areas destino | /areas | /areas | Protegido (admin) |
| Control hardware | /control-hardware | /control-hardware | Protegido + API token |

## 5. Criterios de seguridad visibles en el mapa

- Pantallas publicas: autenticacion y recuperacion de clave.
- Pantallas protegidas: dashboard y todos los modulos funcionales.
- Restriccion por rol: modulos de administracion (usuarios, horarios, areas) y acciones sensibles.
- API de hardware con token dedicado (X-Hardware-Token).

## 6. Texto sugerido para pegar en el manual tecnico

El Mapa Web del sistema representa la arquitectura de navegacion de la aplicacion Flask y su organizacion por modulos funcionales. La ruta de entrada es el inicio de sesion, desde donde el usuario autenticado accede al panel principal y a los modulos de operacion (usuarios, conductores, vehiculos, visitantes, espacios, novedades, control de accesos, reportes y consultas). Adicionalmente, el sistema incluye modulos administrativos de configuracion (horarios y areas) y un modulo de integracion con hardware que combina interfaz web y endpoints API protegidos por token.

Este mapa permite verificar cobertura funcional, separacion de responsabilidades y controles de acceso por autenticacion y rol, cumpliendo con el objetivo del manual tecnico de documentar la estructura de navegacion y operacion del aplicativo.

## 7. Fuente tecnica usada

Rutas extraidas desde:
- python/webapp/app/__init__.py
- python/webapp/app/main/routes.py
- python/webapp/app/auth/routes.py
- python/webapp/app/users/routes.py
- python/webapp/app/conductores/routes.py
- python/webapp/app/vehiculos/routes.py
- python/webapp/app/visitantes/routes.py
- python/webapp/app/espacios/routes.py
- python/webapp/app/novedades/routes.py
- python/webapp/app/control_accesos/routes.py
- python/webapp/app/reportes/routes.py
- python/webapp/app/consultas/routes.py
- python/webapp/app/horarios/routes.py
- python/webapp/app/areas/routes.py
- python/webapp/app/control_hardware/routes.py
