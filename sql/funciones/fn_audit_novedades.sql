-- 2) Función que inserta en la tabla de auditoría
CREATE OR REPLACE FUNCTION public.fn_audit_novedades()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO public.novedades_audit (nov_id, operacion, new_estado, fecha, usuario_id, observacion)
    VALUES (NEW.id, 'INSERT', NEW.estado, now(), NEW.id_usuario, NEW.observaciones);
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO public.novedades_audit (nov_id, operacion, old_estado, new_estado, fecha, usuario_id, observacion)
    VALUES (NEW.id, 'UPDATE', OLD.estado, NEW.estado, now(), NEW.id_usuario, NEW.observaciones);
    RETURN NEW;
  ELSE
    RETURN NEW;
  END IF;
END;
$$;