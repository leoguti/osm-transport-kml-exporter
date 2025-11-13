# 🚌 OSM Transport Exporter

Un exportador de rutas de transporte público desde archivos OSM (OpenStreetMap) a formatos KML y Shapefile para visualización en Google Earth, QGIS, ArcGIS y otras aplicaciones de mapas.

## 📋 Descripción

Este proyecto procesa archivos OSM y extrae todas las rutas de transporte público (autobuses, tranvías, metros, trenes, etc.) para exportarlas a dos formatos:

- **KML**: Archivos individuales por ruta para Google Earth y visores de mapas
- **Shapefile**: Un archivo único con todas las rutas y atributos GTFS para análisis SIG

Ambos formatos se empaquetan automáticamente en archivos ZIP para fácil distribución.

## ✨ Características

- ✅ **Validación automática** de archivos OSM
- 🚌 **Soporte múltiples tipos** de transporte: autobús, tranvía, metro, tren, trolleybus, tren ligero
- 🗂️ **Doble formato de salida**:
  - **KML**: Archivos individuales por ruta para Google Earth
  - **Shapefile**: Archivo único con geometrías continuas y atributos GTFS
- 📏 **Cálculo automático** de longitud de rutas en kilómetros
- 🗺️ **Geometrías optimizadas** con unión automática de segmentos de ruta
- 📦 **Empaquetado automático** en archivos ZIP
- 📊 **Informes detallados** del procesamiento
- 🔍 **Logging completo** para seguimiento y debugging
- 🎛️ **Interfaz de línea de comandos** flexible

## 🚀 Instalación

### Prerequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/leoguti/osm-transport-kml-exporter.git
   cd osm-transport-kml-exporter
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Uso

### Uso básico

```bash
cd src
python main.py <archivo.osm> [opciones]
```

### Ejemplos

```bash
# Solo KML (por defecto)
cd src
python main.py ../input/mi_ciudad.osm

# Solo Shapefile
cd src
python main.py ../input/mi_ciudad.osm --format shp

# Ambos formatos
cd src
python main.py ../input/mi_ciudad.osm --format both

# Usando flags individuales
cd src
python main.py ../input/mi_ciudad.osm --kml --shp
```

### Opciones de línea de comandos

```bash
python main.py --help
```

| Opción | Descripción |
|--------|-------------|
| `--format {kml,shp,shapefile,both}` | Formato de salida (default: kml) |
| `--kml` | Exportar a formato KML |
| `--shp` | Exportar a formato Shapefile |
| `--help` | Mostrar ayuda y salir |

### Estructura de directorios

```
osm-transport-kml-exporter/
├── input/           # Coloca aquí tus archivos OSM
├── output/          # Los archivos ZIP se generan aquí
├── src/             # Código fuente
│   ├── main.py          # Script principal
│   ├── validator.py     # Validador de archivos OSM
│   ├── osm_processor.py # Procesador de datos OSM
│   └── kml_exporter.py  # Exportador a KML
└── requirements.txt # Dependencias del proyecto
```

## 📊 Ejemplo de salida

```
============================================================
🚌 OSM Transport Exporter - KML + Shapefile
============================================================

🔍 Validando archivo: input/jilotepec.osm
✅ Archivo OSM válido

🔄 Procesando rutas de transporte público...
✅ Se encontraron 76 rutas válidas

🗂️  Generando archivos KML...
✅ Se generaron 76 archivos KML
📦 Creando archivo ZIP para KML...
✅ Archivo ZIP KML creado exitosamente

🗂️  Generando Shapefile...
✅ Shapefile generado: 76 rutas
📦 Creando archivo ZIP para Shapefile...
✅ Archivo ZIP Shapefile creado exitosamente

============================================================
🎉 EXPORTACIÓN COMPLETADA
============================================================
📄 KML: output/jilotepec_kml.zip
📊 Tamaño: 0.24 MB

📄 Shapefile: output/jilotepec_shp.zip
📊 Tamaño: 0.13 MB

🗺️  Rutas exportadas: 76

📌 Próximos pasos:
  KML: Descomprime el ZIP y abre los .kml en Google Earth
  Shapefile: Descomprime el ZIP y abre en QGIS/ArcGIS
```

## 🛠️ Dependencias

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `osmium` | ≥3.6.0 | Procesamiento de archivos OSM |
| `simplekml` | ≥1.3.6 | Generación de archivos KML |
| `shapely` | ≥2.0.0 | Operaciones geométricas |
| `geopandas` | ≥0.14.0 | Generación de Shapefiles y análisis espacial |
| `pytest` | ≥7.4.0 | Testing (desarrollo) |

## 🗺️ Tipos de transporte soportados

- 🚌 **Autobús** (`route=bus`)
- 🚋 **Tranvía** (`route=tram`)
- 🚇 **Metro/Subway** (`route=subway`)
- 🚂 **Tren** (`route=train`)
- 🚎 **Trolleybus** (`route=trolleybus`)
- 🚊 **Tren ligero** (`route=light_rail`)

## 📁 Formatos de salida

### 🗂️ KML (Google Earth)
1. **Archivos KML individuales**: Cada ruta se exporta como un archivo `.kml` separado
2. **Archivo ZIP**: Todos los KML se empaquetan en `{archivo}_kml.zip`
3. **Uso**: Ideal para visualización en Google Earth y navegadores web

### 🗺️ Shapefile (SIG)
1. **Archivo único**: Todas las rutas en un shapefile con geometrías continuas
2. **Campos incluidos**:
   - `route_id`: Identificador único de la ruta
   - `route_name`: Nombre de la ruta
   - `ref`: Referencia/número de ruta
   - `route_type`: Tipo de transporte (bus, tram, etc.)
   - `from_stop`: Parada de origen
   - `to_stop`: Parada de destino  
   - `operator`: Operador del servicio
   - `route_long`: Descripción larga de la ruta
   - `length_km`: Longitud calculada en kilómetros
3. **Archivo ZIP**: Shapefile completo en `{archivo}_shp.zip`
4. **Uso**: Análisis espacial en QGIS, ArcGIS, etc.

## 🔧 Arquitectura del código

```
src/
├── main.py              # 🎯 Punto de entrada y orquestador principal
├── validator.py         # ✅ Validación de archivos OSM
├── osm_processor.py     # 🔄 Procesamiento y extracción de datos
├── kml_exporter.py      # 📤 Generación de KML y ZIP
└── shp_exporter.py      # 🗺️ Generación de Shapefile y ZIP
```

### Flujo de procesamiento

1. **Validación** → Verifica que el archivo OSM sea válido y contenga rutas de transporte
2. **Procesamiento** → Extrae relaciones, ways y nodos de transporte público  
3. **Generación de geometrías** → Crea LineStrings para cada way y ruta
4. **Exportación paralela**:
   - **KML**: Convierte cada ruta a archivo KML individual
   - **Shapefile**: Crea geometrías continuas con atributos GTFS
5. **Empaquetado** → Genera archivos ZIP para cada formato

## 🚨 Manejo de errores

El programa incluye validaciones para:

- ❌ **Archivos inexistentes** o con extensión incorrecta
- ❌ **Archivos OSM malformados** o corruptos
- ❌ **Archivos sin rutas de transporte** público válidas
- ❌ **Errores durante el procesamiento** o exportación

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Leonardo Gutiérrez** - [@leoguti](https://github.com/leoguti)

## 🙏 Agradecimientos

- OpenStreetMap community por los datos de transporte público
- Desarrolladores de las librerías osmium, simplekml, shapely y geopandas
- Contribuidores del proyecto

---

**¿Necesitas ayuda?** Abre un [issue](https://github.com/leoguti/osm-transport-kml-exporter/issues) en GitHub.