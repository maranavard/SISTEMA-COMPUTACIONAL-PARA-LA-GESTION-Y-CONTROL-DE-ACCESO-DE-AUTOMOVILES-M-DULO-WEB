# Mapa mental actualizado (alineado a implementacion real)

Este mapa resume los elementos, funcionalidades y objetivos **segun el estado actual del sistema**.

```mermaid
mindmap
  root((Sistema de Control de Acceso Vehicular\nU. de Cundinamarca))
    Problema que atiende
      Control de acceso y parqueo con alta carga operativa
      Trazabilidad manual limitada en procesos criticos
      Tiempos variables en ingreso/salida vehicular
      Riesgo por validaciones documentales no centralizadas

    Solucion implementada
      Sistema web por roles
      Validacion operativa de ingreso/salida
      Gestion digital de parqueo y cupos
      Reportes operativos con filtros
      Integracion con hardware
        Control manual de talanquera y semaforos
        Ingesta de eventos por API JSON con token
        Ingesta por carpeta compartida (admin)

    Objetivo general
      Optimizar el control de acceso vehicular
      Mejorar seguridad, trazabilidad y continuidad operativa

    Objetivos especificos
      Reducir tiempos de atencion en porteria
      Fortalecer validacion operativa de acceso
      Incrementar trazabilidad de novedades y eventos
      Facilitar consulta y seguimiento por placa
      Soportar contingencias con operacion manual de hardware
      Apoyar decisiones con prediccion de ocupacion

    Actores reales
      Administrador
      Vigilante / Seguridad
      Estudiante
      Docente
      Funcionario
      Visitante externo (sin cuenta)
      Integracion tecnica de hardware (token)

    Modulos del sistema
      Autenticacion y sesion
      Usuarios y roles (admin)
      Control de accesos y autorizaciones
      Espacios de parqueo y asignacion automatica
      Novedades
      Consulta por placa
      Conductores
      Vehiculos
      Visitantes
      Reportes
      Areas destino (admin)
      Horarios y festivos (admin)
      Control de hardware

    Permisos clave actuales
      Vigilante
        Opera acceso vehicular
        Opera espacios y asignacion automatica
        Opera control manual de hardware
        Consulta reportes solo del dia (sin exportar)
        No procesa archivos hardware ni audita eventos
      Administrador
        Acceso completo a configuracion y auditoria

    Componente inteligente
      Modelo LSTM para prediccion de ocupacion
      Prediccion operativa a 40 minutos
      Alerta de alta demanda por ocupacion proyectada
      Base historica para analisis

    Tecnologia
      Flask y Jinja2
      PostgreSQL (funciones y triggers)
      Python (ETL y entrenamiento LSTM)
      API JSON con token para hardware
      Carpeta compartida para eventos hardware

    Proyeccion
      Consulta externa de estado de solicitud (CU19) pendiente
      Reconocimiento automatico de placas pendiente
      Escalabilidad a otras sedes
```

## Ajustes clave frente al mapa anterior

- Se corrige el listado de actores a: Administrador, Vigilante/Seguridad, Estudiante, Docente, Funcionario y Visitante externo (sin cuenta).
- Se elimina la duplicidad de la rama "Tecnologia" y se consolida en una sola.
- Se agregan funcionalidades que ya existen y no estaban en el mapa: Areas destino, Horarios/Festivos y Control de hardware.
- Se especifica la realidad de permisos: exportacion de reportes solo admin; auditoria/procesamiento de eventos hardware solo admin; operacion manual de hardware habilitada para vigilante.
- Se mantiene el componente inteligente LSTM, ajustado a su alcance actual (prediccion de ocupacion y alerta operativa).
- Se marca como pendiente lo que aun no esta implementado en produccion funcional: CU19 y reconocimiento automatico de placas.
