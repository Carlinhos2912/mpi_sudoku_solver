import argparse
import time
from pathlib import Path

from baseline_secuencial import leer_seeds
from sudoku import puede_colocar

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

TAG_TRABAJO = 10
TAG_RESULTADO = 11
TAG_CANCELAR = 12
TAG_FIN = 13


def crear_ramas(tablero):
    """Crea una rama por cada valor válido de la primera casilla vacía."""
    for fila in range(9):
        for columna in range(9):
            if tablero[fila][columna] != 0:
                continue
            ramas = []
            for valor in range(1, 10):
                if puede_colocar(tablero, fila, columna, valor):
                    rama = [fila[:] for fila in tablero]
                    rama[fila][columna] = valor
                    ramas.append(rama)
            return ramas
    return [tablero]


def resolver_rama(tablero, coordinador=0):
    """Resuelve una rama y permite cancelar la búsqueda desde el coordinador."""
    for fila in range(9):
        for columna in range(9):
            if comm.Iprobe(source=coordinador, tag=TAG_CANCELAR):
                comm.recv(source=coordinador, tag=TAG_CANCELAR)
                return False, None
            if tablero[fila][columna] != 0:
                continue
            for valor in range(1, 10):
                if puede_colocar(tablero, fila, columna, valor):
                    tablero[fila][columna] = valor
                    resuelto, solucion = resolver_rama(tablero, coordinador)
                    if resuelto:
                        return True, solucion
                    tablero[fila][columna] = 0
            return False, None
    return True, tablero


def resolver_tablero(tablero):
    """Coordina el reparto de ramas y devuelve el estado del tablero."""
    ramas = crear_ramas(tablero)
    if size == 1:
        return resolver_rama(ramas[0]) if ramas else (False, None)

    trabajadores = list(range(1, size))
    pendientes = list(ramas)
    activos = set()

    for trabajador in trabajadores:
        if pendientes:
            comm.send(pendientes.pop(0), dest=trabajador, tag=TAG_TRABAJO)
            activos.add(trabajador)
        else:
            comm.send(None, dest=trabajador, tag=TAG_CANCELAR)

    solucion = None
    while activos and solucion is None:
        estado = MPI.Status()
        resultado = comm.recv(source=MPI.ANY_SOURCE, tag=TAG_RESULTADO, status=estado)
        trabajador = estado.Get_source()
        activos.discard(trabajador)
        resuelto, candidato = resultado
        if resuelto:
            solucion = candidato
            for destino in activos:
                comm.send(None, dest=destino, tag=TAG_CANCELAR)
            while activos:
                estado = MPI.Status()
                comm.recv(source=MPI.ANY_SOURCE, tag=TAG_RESULTADO, status=estado)
                activos.discard(estado.Get_source())
        elif pendientes:
            comm.send(pendientes.pop(0), dest=trabajador, tag=TAG_TRABAJO)
            activos.add(trabajador)
        else:
            # El trabajador queda esperando el siguiente tablero.
            pass

    if solucion is not None:
        return True, solucion
    return False, None


def trabajar():
    """Recibe y resuelve ramas hasta que el coordinador envía TAG_FIN."""
    while True:
        estado = MPI.Status()
        rama = comm.recv(source=0, tag=MPI.ANY_TAG, status=estado)
        if estado.Get_tag() == TAG_FIN:
            return
        if estado.Get_tag() == TAG_CANCELAR:
            continue
        resultado = resolver_rama(rama)
        comm.send(resultado, dest=0, tag=TAG_RESULTADO)


def seleccionar(parser, ruta):
    """Lee y selecciona las seeds solicitadas por la línea de comandos."""
    try:
        seeds = leer_seeds(ruta)
    except OSError as error:
        parser.error(f"no se pudo leer {ruta}: {error}")
    if not seeds:
        parser.error(f"no se encontraron seeds en {ruta}")
    if args.id:
        if args.id not in seeds:
            parser.error(f"ID '{args.id}' no existe. Disponibles: {', '.join(seeds)}")
        return [(args.id, seeds[args.id])]
    return list(seeds.items())


def main():
    global args
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ruta", type=Path, default=Path(__file__).parent / "seeds.txt",
                        help="archivo de seeds (por defecto: ./seeds.txt)")
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--id", "--seed", help="resolver solo la seed con este ID")
    seleccion.add_argument("--all", action="store_true", help="resolver todos los seeds")
    args = parser.parse_args()

    if rank == 0:
        seleccionados = seleccionar(parser, args.ruta)
    else:
        seleccionados = None
    seleccionados = comm.bcast(seleccionados, root=0)

    if rank != 0:
        trabajar()
        return

    inicio_total = time.perf_counter()
    for identificador, original in seleccionados:
        inicio = time.perf_counter()
        resuelto, _ = resolver_tablero([fila[:] for fila in original])
        segundos = time.perf_counter() - inicio
        print(f"\nID: {identificador}")
        print("Resuelto" if resuelto else "Sin solución")
        print(f"{'Tiempo' if args.id else 'Tiempo parcial'}: {segundos:.6f} segundos",
              flush=True)

    for trabajador in range(1, size):
        comm.send(None, dest=trabajador, tag=TAG_FIN)
    comm.Barrier()
    if not args.id:
        print(f"\nTiempo total: {time.perf_counter() - inicio_total:.6f} segundos")


if __name__ == "__main__":
    main()
