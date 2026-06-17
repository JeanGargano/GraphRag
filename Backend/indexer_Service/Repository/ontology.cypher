// Creación de Nodos con sus atributos
CREATE (`resolución`:`Resolución` {
    `titulo_resolucion`: "Lorem",
    `estado_actual`: "Lorem",
    `numero`: -60,
    `fecha`: "2014-12-03",
    `nivel`: "pregrado"
}),

(`modalidad`:`Modalidad` {
    `nombre_modalidad`: "Lorem",
    `descripcion`: "Lorem",
    `num_max_estudiantes`: 76,
    `articulo`: "Lorem"
}),

(`requisitos`:`Requisitos` {
    `tipo_requisito`: "general",
    `plan_academico`: "Lorem",
    `descripcion`: "Lorem",
    `valor_minimo`: 0.0
}),

(`procedimiento`:`Procedimiento` {
    `nombre_etapa`: "Lorem",
    `orden`: 44,
    `plataforma_asociada`: "Lorem"
}),

(`unidadapoyo`:`UnidadApoyo` {
    `nombre_rol`: "Lorem",
    `correo_contacto`: "Lorem",
    `tipo_actor`: "Lorem"
}),

(`documentación`:`Documentación` {
    `nombre`: "Lorem",
    `identificador`: "Lorem",
    `tipo`: "resolucion",
    `url`: "Lorem",
    `estado`: "activo"
}),

(`programa`:`Programa` {
    `nombre_programa`: "Lorem",
    `planes_vigentes`: "Lorem"
}),

(`facultad`:`Facultad` {
    `nombre_facultad`: "Lorem"
}),

(`tiempo`:`Tiempo` {
    `descripcion`: "Lorem",
    `fechaLimite`: "2014-12-03"
}),

// --- RELACIONES CORREGIDAS ---

// Procedimiento requiere aprobación (Cambiado de Resolución a Procedimiento)
(`procedimiento`)-[:`REQUIERE_APROBACION_DE` {
    `tipo_aprobacion`: "Lorem",
    `tiempo_respuesta`: "Lorem",
    `nota_requerida`: "Lorem"
}]->(`unidadapoyo`),

(`resolución`)-[:`SOPORTADO_EN` {}]->(`documentación`),

(`modalidad`)-[:`TIENE_REQUISITOS` {
    `momento_exigencia`: "Lorem",
    `condicion_especial`: "Lorem",
    `es_obligatorio`: true
}]->(`requisitos`),

(`modalidad`)-[:`APLICA_A` {
    `fecha_inscripcion`: "2014-12-03",
    `estado_solicitud`: "Lorem"
}]->(`resolución`),

(`modalidad`)-[:`CONSTA_DE_ETAPA` {
    `orden_etapa`: 8
}]->(`procedimiento`),

(`requisitos`)-[:`ASOCIADO_A` {}]->(`procedimiento`),

(`procedimiento`)-[:`REQUIERE_DE` {
    `articulo_aplicable`: "Lorem",
    `tipo_documento`: "Lorem"
}]->(`documentación`),

(`procedimiento`)-[:`ES_PRERREQUISITO_DE` {
    `tiempo_maximo_etapa`: "Lorem"
}]->(`procedimiento`),

(`procedimiento`)-[:`DEBE_CUMPLIR` {}]->(`tiempo`),

(`documentación`)-[:`DEBE_CUMPLIR` {}]->(`resolución`),

(`programa`)-[:`OFRECE` {
    `aplica_plan_estudio`: "Lorem"
}]->(`modalidad`),

(`programa`)-[:`TIENE_COMO_APOYO` {
    `nivel_resolucion`: "Lorem"
}]->(`unidadapoyo`),

(`programa`)-[:`SE_RIGE_POR` {
    `periodo_academico`: "Lorem"
}]->(`resolución`),

(`facultad`)-[:`ADMINISTRA` {
    `resolucion_aprobacion`: "Lorem"
}]->(`programa`),

(`tiempo`)-[:`VINCULADO_A` {}]->(`unidadapoyo`)

RETURN `resolución`,`modalidad`,`requisitos`,`procedimiento`,`unidadapoyo`,`documentación`,`programa`,`facultad`,`tiempo`;
