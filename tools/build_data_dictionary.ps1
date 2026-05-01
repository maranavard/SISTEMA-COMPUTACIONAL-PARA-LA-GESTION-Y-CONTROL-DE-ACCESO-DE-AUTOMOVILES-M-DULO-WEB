$ErrorActionPreference = 'Stop'

Set-Location "$PSScriptRoot\.."
$schema = Get-Content "docs\diccionario_schema_actual.json" -Raw | ConvertFrom-Json
$outPath = "docs\diccionario-datos-actualizado.md"

$desc = @{
  "asignaciones_log" = "Almacena el historial de asignaciones de espacio de parqueo (manuales o automaticas)."
  "autorizaciones_visitante" = "Almacena las decisiones de aprobacion/rechazo de visitantes y su trazabilidad."
  "conductores" = "Almacena informacion de los conductores registrados en el sistema."
  "config_areas_destino" = "Catalogo de areas de destino habilitadas para visitantes."
  "config_festivos_universidad" = "Define fechas festivas para reglas operativas de acceso."
  "config_horario_universidad" = "Define franjas horarias y dias activos de operacion institucional."
  "control_hardware_estado" = "Almacena el estado actual de dispositivos de hardware integrados."
  "control_hardware_eventos" = "Almacena eventos recibidos desde hardware para auditoria tecnica."
  "documentos_vehiculo" = "Almacena documentos asociados a vehiculos para validacion."
  "espacio" = "Almacena la informacion de los espacios/cupos de parqueo y su estado."
  "novedad" = "Almacena eventos de ingreso, salida y novedades operativas del control vehicular."
  "novedades_audit" = "Almacena la auditoria de cambios de estado sobre las novedades."
  "predicciones" = "Almacena resultados del modelo predictivo de ocupacion del parqueadero."
  "roles" = "Almacena los roles del sistema para control de permisos."
  "sync_eventos_web" = "Almacena eventos sincronizados desde la web."
  "sync_pendientes" = "Almacena eventos pendientes por sincronizar."
  "tipo_doc" = "Almacena tipos de documento heredados para compatibilidad historica."
  "tipo_documento" = "Almacena el catalogo normalizado de tipos de documento del modulo web."
  "tipo_vehiculo" = "Almacena los tipos de vehiculo registrados en el sistema."
  "usuarios" = "Almacena la informacion de autenticacion y perfil de usuarios del sistema."
  "vehiculos" = "Almacena la informacion de los vehiculos registrados para control de acceso."
  "visitantes" = "Almacena los registros de visitantes y su trazabilidad de autorizacion."
}

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Diccionario de Datos Actualizado') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('Fecha: 2026-04-28') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Tablas vigentes (22)') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('| Nombre | Descripcion |') | Out-Null
$lines.Add('|---|---|') | Out-Null
foreach ($t in $schema.tables) {
  $lines.Add("| $($t.ToUpper()) | $($desc[$t]) |") | Out-Null
}

$idx = 1
foreach ($t in $schema.tables) {
  $tableObj = $schema.schema.PSObject.Properties[$t].Value
  $lines.Add('') | Out-Null
  $lines.Add("## TABLA ${idx}: $($t.ToUpper())") | Out-Null
  $lines.Add($desc[$t]) | Out-Null
  $lines.Add('') | Out-Null
  $lines.Add('| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |') | Out-Null
  $lines.Add('|---|---|---:|:---:|---|:---:|') | Out-Null

  $fkMap = @{}
  foreach ($fk in $tableObj.fks) {
    $k = [string]$fk.column
    $v = "FK -> $($fk.ref_table.ToUpper()).$($fk.ref_column)"
    if ($fkMap.ContainsKey($k)) {
      if ($fkMap[$k] -notlike "*$v*") {
        $fkMap[$k] = "$($fkMap[$k]); $v"
      }
    } else {
      $fkMap[$k] = $v
    }
  }

  foreach ($c in $tableObj.columns) {
    $colName = [string]$c.name
    $colName = $colName -replace 'Ã¡','a' -replace 'Ã©','e' -replace 'Ã­','i' -replace 'Ã³','o' -replace 'Ãº','u'
    $colName = $colName -replace 'á','a' -replace 'é','e' -replace 'í','i' -replace 'ó','o' -replace 'ú','u' -replace 'ñ','n'

    $tipo = [string]$c.data_type
    if ($tipo -eq 'ARRAY') { $tipo = 'array' }

    $tam = '-'
    if ($null -ne $c.char_len) {
      $tam = [string]$c.char_len
    } elseif ($null -ne $c.num_precision) {
      $tam = [string]$c.num_precision
    }

    $pk = if (($tableObj.pk | Where-Object { $_ -eq $c.name }).Count -gt 0) { 'PK' } else { '' }
    $fk = if ($fkMap.ContainsKey([string]$c.name)) { $fkMap[[string]$c.name] } else { '' }
    $nul = if ($c.nullable -eq 'YES') { 'SI' } else { 'NO' }

    $lines.Add("| $colName | $tipo | $tam | $pk | $fk | $nul |") | Out-Null
  }

  $idx++
}

$lines.Add('') | Out-Null
$lines.Add('## Equivalencias con nombres legacy') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('| Nombre anterior | Nombre actual | Estado |') | Out-Null
$lines.Add('|---|---|---|') | Out-Null
$lines.Add('| CONDUCTORS | CONDUCTORES | Renombrada en el diccionario |') | Out-Null
$lines.Add('| DOCUMENTOS | DOCUMENTOS_VEHICULO | Reemplazada por modelo normalizado |') | Out-Null
$lines.Add('| REGISTRO_VISITANTES | VISITANTES | Reemplazada por tabla vigente |') | Out-Null
$lines.Add('| SYNC_PENDIENTES_LOCAL | SYNC_PENDIENTES | Reemplazada por tabla vigente |') | Out-Null
$lines.Add('| TEST_CONEXION | (sin uso actual) | No existe en el esquema vigente |') | Out-Null

Set-Content -Path $outPath -Value $lines -Encoding UTF8
Write-Output "WROTE $outPath"
Write-Output ((Get-Item $outPath).Length)
