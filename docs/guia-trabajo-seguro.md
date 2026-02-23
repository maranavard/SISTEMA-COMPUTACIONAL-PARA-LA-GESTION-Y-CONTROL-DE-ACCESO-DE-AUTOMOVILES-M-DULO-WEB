# Guía de trabajo seguro (VS Code + GitHub)

## 1) Regla principal

Guardar archivo no es respaldo en la nube. El respaldo real ocurre cuando haces `commit` y `push` a GitHub.

## 2) Configurar Auto Save en VS Code

1. Menú `File` → activar `Auto Save`.
2. En configuración, usar `files.autoSave: afterDelay`.


## 3) Flujo diario recomendado (siempre igual)

Al iniciar:

1. `git pull`
2. Revisar estado: `git status`

Durante el trabajo (cada bloque pequeño terminado):

1. `git add .`
2. `git commit -m "módulo: descripción corta del avance"`

Al cerrar sesión:

1. `git push`
2. Verificar en GitHub que el commit aparece.

## 4) Convención de mensajes de commit

- `feat(auth): login y recuperación de contraseña`
- `feat(espacios): estado disponible/ocupado/inhabilitado`
- `fix(novedades): corrige validación de placa`
- `docs(requisitos): actualiza backlog MVP`

## 5) Cuándo crear ramas

- Proyecto individual: puedes trabajar en `main` con commits frecuentes.
- Proyecto con más personas: usar `main` estable + rama `dev` + ramas de feature.

## 6) Qué enviarme para avanzar bien

- Requerimientos nuevos/ajustes en texto.
- Capturas de Figma cuando entremos a frontend.
- Errores de terminal completos cuando algo falle.

## 7) Checklist de cierre de sesión

- [ ] Archivos guardados.
- [ ] `git status` limpio.
- [ ] Commit realizado.
- [ ] Push a GitHub.
- [ ] Nota corta de “qué sigue” en README o issue.