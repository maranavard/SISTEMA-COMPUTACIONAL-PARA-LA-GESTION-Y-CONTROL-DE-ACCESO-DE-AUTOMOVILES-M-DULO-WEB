-- trg_audit_novedades.sql
DROP TRIGGER IF EXISTS trg_audit_novedades ON public.novedad;

CREATE TRIGGER trg_audit_novedades
AFTER INSERT OR UPDATE ON public.novedad
FOR EACH ROW
EXECUTE FUNCTION public.fn_audit_novedades();
