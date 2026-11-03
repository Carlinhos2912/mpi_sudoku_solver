# Tarea 3: combinar tableros y ramas

Implementa una versión MPI en esta carpeta. Reparte los IDs entre grupos de procesos y permite que los procesos de cada grupo exploren ramas distintas del tablero asignado.

Registra el tiempo total de los 30 IDs y explica cómo elegiste el tamaño de los grupos. Añade aquí el comando para ejecutar tu implementación con el contenedor. Incluye `--allow-run-as-root --use-hwthread-cpus --oversubscribe` en `mpiexec`, como en la calibración.

## Solución:
Se eligió el tamaño de grupo como el valor mínimo entre el número de trabajadores (11 procesadores) y la cantidad de semillas seleccionadas (30).

Desde la raíz del proyecto ejecuta:

```powershell
docker run --rm -v "%cd%:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 11 python /app/mpi_hibrido.py --id 7
docker run --rm -v "%cd%:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 11 python /app/mpi_hibrido.py --all
```

Reemplazando `N` por el específico del equipo.
