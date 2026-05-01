# 1.7. Marcos de Referencia

## 1.7.1 Marco teorico

El Sistema Computacional para la Gestion y Control de Acceso de Automoviles se fundamenta en un modelo mixto de operacion, conformado por reglas deterministicas de negocio y un componente de apoyo analitico-predictivo. El componente deterministico garantiza la ejecucion controlada de procesos criticos, como autenticacion, autorizacion, validacion documental, registro de ingreso y salida, y asignacion de espacios. El componente analitico aporta capacidad de anticipacion para fortalecer la toma de decisiones operativas.

Desde la perspectiva de ingenieria de software, la solucion se implementa con arquitectura web modular cliente-servidor, separando capa de presentacion, capa de negocio y capa de datos. Esta organizacion favorece mantenibilidad, escalabilidad y evolucion incremental del sistema durante su ciclo de vida.

En materia de seguridad funcional, se aplica el enfoque de control de acceso basado en roles (RBAC), mediante el cual los permisos se asignan por perfil funcional y no por usuario individual. Este criterio reduce errores de privilegios, mejora la gobernanza del acceso y simplifica la administracion institucional.

En trazabilidad, la arquitectura incorpora registro de novedades, auditoria de cambios de estado, eventos de sincronizacion y eventos de hardware, permitiendo observabilidad y control operativo. Este enfoque resulta coherente con sistemas de acceso institucional que requieren evidencia digital verificable.

El componente predictivo se integra como soporte complementario y no como sustituto de las reglas de negocio. En consecuencia, el modelo mixto combina robustez transaccional en tiempo real con capacidad de pronostico para optimizar asignacion y disponibilidad de cupos. Asimismo, la incorporacion de colas de sincronizacion fortalece la continuidad operativa en escenarios de intermitencia.

## 1.7.2 Marco legal

El proyecto se enmarca en la normativa colombiana sobre proteccion de datos personales, validez de mensajes de datos, seguridad de la informacion y propiedad intelectual de software.

1. Derecho a la intimidad y habeas data.

El articulo 15 de la Constitucion Politica de Colombia reconoce el derecho a la intimidad, al buen nombre y al habeas data, base juridica para el tratamiento responsable de informacion personal en sistemas institucionales (Constitucion Politica de Colombia, 1991, art. 15).

2. Regimen general de proteccion de datos personales.

La Ley 1581 de 2012 establece principios y deberes para el tratamiento de datos personales, entre ellos legalidad, finalidad, libertad, seguridad y confidencialidad, aplicables a datos de usuarios, conductores y visitantes administrados por el sistema (Congreso de Colombia, 2012).

3. Reglamentacion del tratamiento de datos.

El Decreto 1377 de 2013 reglamento parcialmente la Ley 1581 y fue compilado en el Decreto Unico Reglamentario 1074 de 2015, norma de consulta vigente para implementacion de politicas de tratamiento y deberes del responsable (Ministerio de Comercio, Industria y Turismo, 2013, 2015).

4. Delitos informaticos.

La Ley 1273 de 2009 incorpora al ordenamiento penal conductas relacionadas con acceso abusivo, dano informatico y uso indebido de datos, lo que respalda la necesidad de controles de autenticacion, autorizacion y trazabilidad en el sistema (Congreso de Colombia, 2009).

5. Validez juridica de registros y mensajes de datos.

La Ley 527 de 1999 reconoce efectos juridicos de los mensajes de datos bajo criterios de integridad y disponibilidad, fundamento aplicable a registros de eventos y bitacoras electronicas del sistema (Congreso de Colombia, 1999).

6. Transparencia y acceso a informacion publica (cuando aplique).

La Ley 1712 de 2014 define lineamientos de transparencia y acceso a informacion publica, relevante para politicas institucionales de publicacion, reserva y gestion documental en entornos TIC (Congreso de Colombia, 2014).

7. Propiedad intelectual del software y la documentacion.

La Ley 23 de 1982, la Decision Andina 351 de 1993 y la Ley 1915 de 2018 constituyen el marco de proteccion del derecho de autor sobre codigo fuente, documentacion tecnica y demas productos intelectuales del proyecto (Comunidad Andina, 1993; Congreso de Colombia, 1982, 2018).

## Referencias (APA 7)

Comunidad Andina. (1993). Decision 351 de 1993: Regimen comun sobre derecho de autor y derechos conexos. https://www.comunidadandina.org

Congreso de Colombia. (1982). Ley 23 de 1982, sobre derechos de autor. https://www.suin-juriscol.gov.co

Congreso de Colombia. (1999). Ley 527 de 1999, por medio de la cual se define y reglamenta el acceso y uso de los mensajes de datos, del comercio electronico y de las firmas digitales. https://www.suin-juriscol.gov.co

Congreso de Colombia. (2009). Ley 1273 de 2009, por medio de la cual se modifica el Codigo Penal y se crea un nuevo bien juridico tutelado denominado de la proteccion de la informacion y de los datos. https://www.suin-juriscol.gov.co

Congreso de Colombia. (2012). Ley 1581 de 2012, por la cual se dictan disposiciones generales para la proteccion de datos personales. https://www.suin-juriscol.gov.co

Congreso de Colombia. (2014). Ley 1712 de 2014, por medio de la cual se crea la Ley de Transparencia y del Derecho de Acceso a la Informacion Publica Nacional. https://www.suin-juriscol.gov.co

Congreso de Colombia. (2018). Ley 1915 de 2018, por la cual se modifica la Ley 23 de 1982 y se establecen otras disposiciones en materia de derecho de autor y derechos conexos. https://www.suin-juriscol.gov.co

Constitucion Politica de Colombia. (1991). Articulo 15. https://www.secretariasenado.gov.co

Ministerio de Comercio, Industria y Turismo. (2013). Decreto 1377 de 2013, por el cual se reglamenta parcialmente la Ley 1581 de 2012. https://www.suin-juriscol.gov.co

Ministerio de Comercio, Industria y Turismo. (2015). Decreto 1074 de 2015, Decreto Unico Reglamentario del Sector Comercio, Industria y Turismo. https://www.suin-juriscol.gov.co
