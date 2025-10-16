CREATE TRIGGER trg_novedad_asignacion
BEFORE INSERT ON public.novedad
FOR EACH ROW
EXECUTE FUNCTION public.fn_asignar_liberar_espacio();
