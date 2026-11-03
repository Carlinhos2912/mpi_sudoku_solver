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
| Secuencial | Todos los IDs | 1 | 257,467 | 1,00 |
| MPI por tableros | Todos los IDs | 11 | 76,070 | 3,385 |
| MPI por ramas | Todos los IDs, uno después de otro | 11 | 348,797 | 0,738 |
| MPI híbrido | Todos los IDs | 11 | 80,435 | 3,201 |

Calcula la aceleración como `tiempo secuencial / tiempo MPI`. Mide el tiempo MPI desde el inicio del reparto hasta recibir todos los resultados necesarios.

## Conclusiones

- ¿Qué estrategia obtuvo el menor tiempo para los 30 tableros? ¿Cuánto mejoró respecto a la versión secuencial?

    R/ Las estrategias con menor tiempo total en `--all` fueron el MPI por tableros, seguido de MPI híbrido. Con aceleraciones respecto al tiempo secuencial de: 3,385 y 3,201 respectivamente.

- ¿Cómo afectaron la comunicación y las diferencias de duración entre tableros?

    R/ En el primer caso (por_tableros) solo se realizaban comunicaciones al inicio, al repartirlos, y a al final, entregando los resultados. De esta estratégia se obtuvo el menor tiempo total, por lo que se interpreta mayor eficiencia al haber menos interrupciones por comunicaciones.

    En el segundo caso (por_ramas) se realizaban comunicaciones en cada iteración de las ramas. Por esto se interpreta el mayor tiempo total de ejecución como resultado de un mayor número de interrupciones por comunicaciones.

    Por último, el caso híbrido presenta un rendimiento similar al de por tableros, teniendo un número más equilibrado (considerablemente menor) de interrupicones por comunicaciones.

- ¿Cómo se comparó repartir tableros con resolverlos en orden y repartir las ramas de cada uno?

    R/ Se evidenció mayor eficiencia al repartir tableros a cada procesador frente a resolverlos en orden. 
    
    Por otra parte, se evidencian tiempos similares entre repartir tableros y repartir las ramas en grupos. 
