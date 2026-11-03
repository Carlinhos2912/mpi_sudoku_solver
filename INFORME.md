# Informe de resultados

Completa este informe después de implementar las tres tareas MPI. Ejecuta las comparaciones con el mismo archivo `seeds.txt`, en el mismo equipo y con el contenedor del taller.

## Entorno

- Equipo: Ryzen 5 5500U (6 núcleos, 12 hilos)
- Versión del contenedor: slim-mpi:2
- Cantidad de repeticiones por medición: 3
- Valor común de `N` elegido: 11

## Comparación final con el mismo `N`

Repite tres veces cada ejecución y registra la mediana. Mantén fijo el `N` elegido en todas las filas MPI. Incluye `--allow-run-as-root --use-hwthread-cpus --oversubscribe` en `mpiexec`, igual que en la calibración, para permitir valores de `N` mayores que los slots detectados.

| Implementación | Caso | Procesos | Mediana del tiempo total (s) | Aceleración frente a secuencial |
| --- | --- | ---: | ---: | ---: |
| Secuencial | Todos los IDs | 1 |  | 1,00 |
| MPI por tableros | Todos los IDs | 11 | 76.07 |  |
| MPI por ramas | Todos los IDs, uno después de otro | 11 |  |  |
| MPI híbrido | Todos los IDs | 11 |  |  |

Calcula la aceleración como `tiempo secuencial / tiempo MPI`. Mide el tiempo MPI desde el inicio del reparto hasta recibir todos los resultados necesarios.

## Conclusiones

- ¿Qué estrategia obtuvo el menor tiempo para los 30 tableros? ¿Cuánto mejoró respecto a la versión secuencial?
- ¿Cómo afectaron la comunicación y las diferencias de duración entre tableros?
- ¿Cómo se comparó repartir tableros con resolverlos en orden y repartir las ramas de cada uno?
